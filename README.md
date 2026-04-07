# SKN25-3rd-3Team

# 1. 팀 소개

# 2. 프로젝트 기간

# 3. 프로젝트 개요

## 📕 프로젝트명

## ✅ 프로젝트 배경 및 목적

## 🖐️ 프로젝트 소개

```
SKN25-3RD-3TEAM/
├── backend/
│   ├── db/
│   │   └── mongo_db.py         # 🔄 (수정) MongoDB 연결 및 컬렉션 반환 모듈
│   ├── etl/
│   │   └── embed_recipes.py    # 🆕 (신규) 노트북의 "데이터 1000개씩 임베딩 넣는 반복문"을 스크립트화 한 파일
│   ├── rag/
│   │   ├── prompts.py          # 🔄 (수정) 재료 추출 및 레시피 추천용 프롬프트 분리 보관
│   │   ├── retriever.py        # 🆕 (신규) MongoDB Atlas Vector Search 검색 로직
│   │   ├── pipeline.py         # 🆕 (신규) 질문 -> 추출 -> 검색 -> 답변생성 (기존 agent_workflow 대체)
│   │   └── search_engine.py    # ✅ (유지) DB에 레시피가 없을 때를 대비한 네이버 크롤링 웹 검색 도구
│   ├── api/
│   │   └── main.py             # ✅ (유지) FastAPI 백엔드 엔드포인트
│   └── utils/
│       └── config.py           # 🆕 (신규) .env 로드 및 OpenAI/MongoDB 전역 클라이언트 설정
├── frontend/
│   └── recipe_ui.py            # ✅ (유지) Streamlit UI 프론트엔드
├── .env                        # API 키 및 DB URI (MONGO_URI 필수)
└── requirements.txt            # 의존성 패키지 (psycopg, chromadb 등은 삭제 가능)
```

## ❤️ 기대효과

## 👤 대상 사용자

# 4. 기술 스택

# 5. 수행결과

# 6. 한 줄 회고