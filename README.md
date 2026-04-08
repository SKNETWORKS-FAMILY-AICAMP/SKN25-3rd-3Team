# SKN25-3rd-3Team

# 1. 팀 소개
| 이름 | GitHub | 역할 |
| :--- | :---: | :--- |
| 권가영 | [@Gayoung03](https://github.com/Gayoung03) | 네이버 검색 API 기반 실시간 데이터 검증, GPT 연동 RAG 파이프라인 구축|
| 김연준 | [@kgbrladuswns](https://github.com/kgbrladuswns) | 코드베이스 구축, 정규화 DDL 생성, ETL Transform  |
| 전운열 | [@cudaboy](https://github.com/cudaboy) | LangChain 아키텍처 구축, 발표 |
| 조은석 | [@silverstone-1004](https://github.com/silverstone-1004) | 데이터베이스 구축, 데이터 파이프라인 설계 |
| 최유림 | [@yulim8823](https://github.com/yulim8823) | 아이디어 제시, 웹 크롤링, 발표 자료(PPT) 작성 |
# 2. 프로젝트 기간
2026.4.6. - 2026.4.7.

# 3. 프로젝트 개요

## 📕 프로젝트명
"AI 냉털봇: 너의 냉장고를 구해줘"
(RAG 기반 지능형 식재료 맞춤 레시피 추천 시스템)

## ✅ 프로젝트 배경 및 목적
• 배경: 6만 건 이상의 방대한 레시피 데이터가 존재하지만, 사용자가 가진 '남은 식재료' 조합에 딱 맞는 요리를 찾기 위해 일일이 검색하고 필터링하는 과정은 여전히 번거롭고 직관적이지 못함.

• 목적: 사용자가 자연어로 냉장고 속 재료를 말하면, 벡터 검색(Vector Search) 기술을 통해 가장 유사도가 높은 레시피를 찾아내고, LLM(대규모 언어 모델)이 이를 맛있게 요약하여 추천하는 개인화된 요리 어시스턴트 구축.

## 🖐️ 프로젝트 소개

### (1) 디렉토리 구조
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
### (2) 시스템 구조
<img width="1095" height="615" alt="image" src="https://github.com/user-attachments/assets/3324e17d-db5e-49d3-b0eb-4ee371295191" />

## ❤️ 기대효과
• 식재료 낭비 감소: 냉장고에 남은 자투리 재료를 활용할 수 있는 최적의 레시피를 제안하여 음식물 쓰레기 절감에 기여.

• 결정 장애 해소: "오늘 뭐 먹지?"라는 고민에 대해 데이터 기반의 신뢰도 높은 답변을 즉각적으로 제공.

• 정확한 정보 전달: 단순한 텍스트 답변을 넘어 실제 요리 커뮤니티(1만개의 레시피 등)의 원본 링크와 상세 조리 순서를 제공하여 실질적인 요리 수행을 도움.

## 👤 대상 사용자
• 자취생 및 1인 가구: 소량으로 남은 재료 처리가 고민인 사용자.

• 초보 요리사: 재료 이름만으로 간단하고 명확한 조리법을 찾고 싶은 사용자.

• 바쁜 직장인: 퇴근 후 냉장고에 있는 재료로 빠르게 메뉴를 결정하고 싶은 사람.

• 식단 관리가 필요한 사람: 특정 재료(알레르기 유발 재료 등)를 제외하고 안전한 요리를 찾고 싶은 사용자.

# 4. 기술 스택
- **Language**
  - ![Python](https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=python&logoColor=white)
  - ![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)

- **Database**
  - ![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white)

- **Pipeline**
  - ![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=linkerd&logoColor=white)

- **API**
  - ![OpenAI](https://img.shields.io/badge/OpenAI-000000?style=for-the-badge&logo=openai&logoColor=white)
  - ![Naver](https://img.shields.io/badge/Naver-03C75A?style=for-the-badge&logo=naver&logoColor=white)
 
- **Visualization**
  - ![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)


# 5. 수행결과

https://github.com/user-attachments/assets/0533d0f2-6f13-4a20-a514-6a895814f425

