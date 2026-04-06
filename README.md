# SKN25-3rd-3Team

# 1. 팀 소개

# 2. 프로젝트 기간

# 3. 프로젝트 개요

## 📕 프로젝트명

## ✅ 프로젝트 배경 및 목적

## 🖐️ 프로젝트 소개

```
SKN25-3RD-3TEAM/
├── app/
│   ├── db/                    # 데이터베이스 관리 (PostgreSQL, MongoDB)
│   │   ├── apply_schema.py
│   │   ├── mongo_db.py
│   │   └── postgres_db.py
│   ├── etl/                   # 데이터 정제 및 적재
│   │   ├── raw_recipe_etl.py
│   │   ├── sink.py
│   │   ├── source.py
│   │   └── transform.py
│   ├── rag/                   # 🌟 RAG 및 검색 엔진 핵심 로직
│   │   ├── __init__.py
│   │   ├── rag_loader.py      # 벡터 DB(Chroma) 구축 및 로드
│   │   ├── search_engine.py   # NAVER API 연동 웹 검색 도구 (Web Retriever)
│   │   ├── prompts.py         # 시스템 프롬프트 및 페르소나 설정
│   │   └── agent_workflow.py  # DB 검색 -> 결과 확인 -> 웹 검색 분기 로직 (LangGraph/Agent)
│   ├── api/                   # Streamlit과 통신할 FastAPI (선택 사항)
│   │   └── main.py
│   └── utils/
│       └── helpers.py         # 공통 유틸리티 (비동기 처리 등)
├── frontend/                  # Streamlit 기반 UI
│   ├── recipe_ui.py                 # 메인 실행 파일
│   └── components/               # UI 컴포넌트 (해시태그, 채팅창 등)
├── vector_db/                 # 로컬 Chroma DB 저장소
├── .env                       # API Key (OpenAI, NAVER_CLIENT_ID/SECRET)
├── requirements.txt           
└── README.md
```

## ❤️ 기대효과

## 👤 대상 사용자

# 4. 기술 스택

# 5. 수행결과

# 6. 한 줄 회고