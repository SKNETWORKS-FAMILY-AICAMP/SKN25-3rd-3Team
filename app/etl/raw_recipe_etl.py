"""
MongoDB recipes 컬렉션 데이터를 PostgreSQL parsed 테이블로 적재하는 ETL 실행 스크립트.
"""

from __future__ import annotations

from typing import Any

from ..db.postgres_db import get_postgres_connection
from .sink import insert_parsed_ingredients, insert_parsed_recipe, insert_parsed_steps, replace_parsed_recipe_children
from .source import get_mongo_data
from .transform import build_parsed_recipe_payload, parse_ingredient

DEFAULT_ETL_LIMIT = 10


def _coerce_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def run_etl(limit: int = DEFAULT_ETL_LIMIT, start_after_id: str | None = None) -> str | None:
    """
    MongoDB -> PostgreSQL ETL 실행 함수.
    레시피 1건 단위로 트랜잭션 처리한다.
    """
    print("[ETL] 시작")

    raw_recipes = get_mongo_data(limit=limit, start_after_id=start_after_id)
    if not raw_recipes:
        print("[ETL] 적재할 데이터가 없습니다.")
        return None

    inserted_count = 0
    overridden_count = 0
    failed_count = 0
    last_batch_raw_recipe_id = str(raw_recipes[-1].get("_id", ""))

    with get_postgres_connection() as postgres_connection:
        total_count = len(raw_recipes)

        for index, raw_recipe in enumerate(raw_recipes, start=1):
            raw_recipe_id = str(raw_recipe.get("_id", ""))
            print(f"[ETL] ({index}/{total_count}) raw_recipe_id={raw_recipe_id} 처리 시작")

            ingredients = _coerce_list(raw_recipe.get("ingredients"))
            steps = _coerce_list(raw_recipe.get("steps"))
            parsed_ingredients = [parse_ingredient(ingredient) for ingredient in ingredients]
            parsed_recipe = build_parsed_recipe_payload(raw_recipe, parsed_ingredients)

            try:
                with postgres_connection.transaction():
                    with postgres_connection.cursor() as cursor:
                        parsed_recipe_id, created = insert_parsed_recipe(cursor, parsed_recipe)
                        if not created:
                            replace_parsed_recipe_children(cursor, parsed_recipe_id)

                        insert_parsed_steps(cursor, parsed_recipe_id, steps)
                        insert_parsed_ingredients(cursor, parsed_recipe_id, parsed_ingredients)
            except Exception as exc:
                failed_count += 1
                print(f"[ETL] raw_recipe_id={raw_recipe_id} 실패, rollback 수행: {exc}")
                continue

            if created:
                inserted_count += 1
            else:
                overridden_count += 1
            print(f"[ETL] raw_recipe_id={raw_recipe_id} commit 완료")

    print(f"[ETL] 종료 - inserted={inserted_count}, overridden={overridden_count}, failed={failed_count}")
    if failed_count == 0 and last_batch_raw_recipe_id:
        print(f"[ETL] 다음 실행용 start_after_id={last_batch_raw_recipe_id}")
        return last_batch_raw_recipe_id

    if failed_count > 0:
        print("[ETL] 실패 건이 있어 자동 이어가기 cursor는 출력하지 않습니다. 확인 후 같은 cursor로 재실행하세요.")

    return None
