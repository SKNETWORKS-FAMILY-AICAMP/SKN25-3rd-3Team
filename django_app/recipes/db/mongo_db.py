"""MongoDB Atlas 컬렉션 핸들 제공.

3차 프로젝트의 backend/db/mongo_db.py에서 import 경로를
backend.utils.config → recipes.utils.config 로 변경했습니다.
"""
from pymongo import MongoClient

from recipes.utils.config import COLLECTION_NAME, DB_NAME, MONGO_URI


def get_db_collection():
    """MongoDB 클라이언트 연결 후 'recipes' 컬렉션을 반환합니다."""
    if not MONGO_URI:
        raise ValueError("MONGO_URI가 설정되지 않았습니다. .env 확인 필요.")
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    db = client[DB_NAME]
    return db[COLLECTION_NAME]


recipe_collection = get_db_collection()
