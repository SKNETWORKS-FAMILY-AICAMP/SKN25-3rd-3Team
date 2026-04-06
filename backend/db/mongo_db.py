# =====================================================================
# [전체 프로젝트에서의 역할]
# 이 파일은 MongoDB Atlas 클라우드 데이터베이스와의 연결을 전담하는 공통 모듈입니다.
# backend/utils/config.py에서 로드한 환경변수(URI, DB명 등)를 바탕으로 DB에 접속하며,
# 레시피 원본 데이터와 벡터 임베딩이 모두 저장된 'recipes' 컬렉션 객체를 생성해 반환합니다.
# 이후 검색 로직(retriever.py)이나 임베딩 적재 로직(embed_recipes.py) 등 
# DB 접근이 필요한 모든 곳에서 이 파일의 `recipe_collection`을 임포트하여 사용하게 됩니다.
# =====================================================================

from pymongo import MongoClient
from backend.utils.config import MONGO_URI, DB_NAME, COLLECTION_NAME

def get_db_collection():
    """MongoDB 클라이언트를 연결하고 특정 컬렉션을 반환합니다."""
    if not MONGO_URI:
        raise ValueError("MONGO_URI 환경변수가 설정되지 않았습니다. .env 파일을 확인해주세요.")
    
    # MongoDB 클라이언트 연결 (연결 타임아웃 3초 설정으로 안전성 확보)
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    
    # 지정된 데이터베이스 및 컬렉션 선택
    db = client[DB_NAME]
    return db[COLLECTION_NAME]

# 다른 파일에서 즉시 import 하여 사용할 수 있도록 전역 인스턴스로 생성해 둡니다.
recipe_collection = get_db_collection()