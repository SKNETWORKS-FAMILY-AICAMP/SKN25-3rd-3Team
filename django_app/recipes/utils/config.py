"""환경변수 / 외부 클라이언트 중앙 설정.

3차 프로젝트의 backend/utils/config.py 그대로 이관.
Django settings.py가 이미 .env를 로드하지만, 모듈 단독 실행(스크립트)에서도
동작하도록 load_dotenv를 한 번 더 호출합니다.
"""
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

DB_NAME = os.getenv("DB_NAME", "recipe_project")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "recipes")

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

if not OPENAI_API_KEY:
    raise ValueError("🚨 OPENAI_API_KEY가 설정되지 않았습니다.")
if not MONGO_URI:
    raise ValueError("🚨 MONGO_URI가 설정되지 않았습니다.")
if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
    print("⚠️ [경고] 네이버 API 키가 없습니다. 웹 검색 Fallback 기능이 작동하지 않을 수 있습니다.")

open_client = OpenAI(api_key=OPENAI_API_KEY)
