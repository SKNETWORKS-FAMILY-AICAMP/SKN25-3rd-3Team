from __future__ import annotations

from typing import Any

from psycopg.types.json import Jsonb

INSERT_PARSED_RECIPE_SQL = """
    INSERT INTO parsed_recipe (
        raw_recipe_id,
        source,
        source_recipe_id,
        title,
        url,
        category_name,
        category_param,
        category_id,
        parse_status,
        warnings
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (raw_recipe_id) DO NOTHING
    RETURNING id
"""

INSERT_PARSED_STEP_SQL = """
    INSERT INTO parsed_recipe_step (
        parsed_recipe_id,
        step_index,
        content
    )
    VALUES (%s, %s, %s)
"""

INSERT_PARSED_INGREDIENT_SQL = """
    INSERT INTO parsed_recipe_ingredient (
        parsed_recipe_id,
        ingredient_index,
        raw_text,
        normalized_text,
        ingredient_name_raw,
        ingredient_name_raw_normalized,
        quantity_text,
        quantity_value,
        quantity_min,
        quantity_max,
        quantity_unit_raw,
        quantity_unit_normalized,
        is_optional,
        annotations,
        entity_type,
        parse_status,
        warnings
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""


def _normalize_step_content(step: Any) -> str:
    if step is None:
        return ""
    if not isinstance(step, str):
        step = str(step)
    return " ".join(step.split()).strip()


def insert_parsed_recipe(cursor, parsed_recipe: dict[str, Any]) -> tuple[int | None, bool]:
    """
    parsed_recipe를 적재하고 RETURNING id를 통해 FK 연결용 PK를 반환한다.
    """
    cursor.execute(
        INSERT_PARSED_RECIPE_SQL,
        (
            parsed_recipe["raw_recipe_id"],
            parsed_recipe["source"],
            parsed_recipe["source_recipe_id"],
            parsed_recipe["title"],
            parsed_recipe["url"],
            parsed_recipe["category_name"],
            parsed_recipe["category_param"],
            parsed_recipe["category_id"],
            parsed_recipe["parse_status"],
            Jsonb(parsed_recipe["warnings"]),
        ),
    )
    inserted_row = cursor.fetchone()
    if inserted_row is None:
        print(f"[PostgreSQL] raw_recipe_id={parsed_recipe['raw_recipe_id']} 는 이미 적재되어 있어 skip")
        return None, False

    parsed_recipe_id = inserted_row["id"]

    print(f"[PostgreSQL] parsed_recipe insert 완료: id={parsed_recipe_id}")
    return parsed_recipe_id, True


def insert_parsed_steps(cursor, parsed_recipe_id: int, steps: list[Any]) -> None:
    """
    parsed_recipe_step를 순서대로 적재한다.
    """
    for step_index, step in enumerate(steps, start=1):
        cursor.execute(INSERT_PARSED_STEP_SQL, (parsed_recipe_id, step_index, _normalize_step_content(step)))

    print(f"[PostgreSQL] parsed_recipe_step insert 완료: {len(steps)}건")


def insert_parsed_ingredients(cursor, parsed_recipe_id: int, parsed_ingredients: list[dict[str, Any]]) -> None:
    """
    parsed_recipe_ingredient를 순서대로 적재한다.
    """
    for ingredient_index, ingredient in enumerate(parsed_ingredients, start=1):
        cursor.execute(
            INSERT_PARSED_INGREDIENT_SQL,
            (
                parsed_recipe_id,
                ingredient_index,
                ingredient["raw_text"],
                ingredient["normalized_text"],
                ingredient["ingredient_name_raw"],
                ingredient["ingredient_name_raw_normalized"],
                ingredient["quantity_text"],
                ingredient["quantity_value"],
                ingredient["quantity_min"],
                ingredient["quantity_max"],
                ingredient["quantity_unit_raw"],
                ingredient["quantity_unit_normalized"],
                ingredient["is_optional"],
                Jsonb(ingredient["annotations"]),
                ingredient["entity_type"],
                ingredient["parse_status"],
                Jsonb(ingredient["warnings"]),
            ),
        )

    print(f"[PostgreSQL] parsed_recipe_ingredient insert 완료: {len(parsed_ingredients)}건")
