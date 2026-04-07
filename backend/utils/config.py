# =====================================================================
# [전체 프로젝트에서의 역할]
# 이 파일은 프로젝트 전체에서 공통으로 사용되는 환경변수(.env)를 로드하고,
# 외부 API 클라이언트(OpenAI)를 전역적으로 한 번만 초기화하는 설정(Config) 모듈입니다.
# =====================================================================

import os
from dotenv import load_dotenv
from openai import OpenAI

# 1. .env 파일 로드
load_dotenv()

# 2. 주요 환경 변수 가져오기
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

DB_NAME = os.getenv("DB_NAME", "recipe_project")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "recipes")

# 💡 [추가됨] 네이버 블로그 검색 API 키
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

# 3. 필수 환경변수 검증
if not OPENAI_API_KEY:
    raise ValueError("🚨 OPENAI_API_KEY가 설정되지 않았습니다.")
if not MONGO_URI:
    raise ValueError("🚨 MONGO_URI가 설정되지 않았습니다.")
if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
    print("⚠️ [경고] 네이버 API 키가 없습니다. 웹 검색 Fallback 기능이 작동하지 않을 수 있습니다.")

# 4. 전역 클라이언트 인스턴스 생성
open_client = OpenAI(api_key=OPENAI_API_KEY)