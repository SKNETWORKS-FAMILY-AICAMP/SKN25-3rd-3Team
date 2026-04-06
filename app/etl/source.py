from __future__ import annotations

from bson import ObjectId

from ..db.mongo_db import get_recipes_collection


def get_mongo_data(limit: int, start_after_id: str | None = None) -> list[dict]:
    """
    MongoDB recipes 컬렉션에서 _id 기준으로 이어서 raw recipe를 읽는다.
    """
    collection = get_recipes_collection()
    mongo_database = collection.database
    query: dict = {}

    if start_after_id:
        query["_id"] = {"$gt": ObjectId(start_after_id)}

    print(
        f"[MongoDB] {mongo_database.name}.{collection.name} 컬렉션에서 "
        f"{limit}건 조회 시작 (start_after_id={start_after_id or '없음'})"
    )

    try:
        documents = list(collection.find(query).sort("_id", 1).limit(limit))
    finally:
        mongo_database.client.close()

    print(f"[MongoDB] 조회 완료: {len(documents)}건")
    return documents
