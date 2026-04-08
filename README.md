# SKN25-3rd-3Team

# 1. 팀 소개
| 이름 | GitHub | 역할 |
| :--- | :---: | :--- |
| 권가영 | [@Gayoung03](https://github.com/Gayoung03) | GPT 기반 실시간 RAG 시스템 및 데이터 ETL 자동화 파이프라인 구축 |
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
• 배경: 6만 건 이상의 방대한 레시피 데이터가 존재하지만, 사용자가 가진 '남은 식재료' 조합에 딱 맞는 요리를 찾기 위해 일일이 검색하고 필터링하는 과정은 여전히 번거롭고 직관적이지 못합니다.

• 목적: 사용자가 자연어로 냉장고 속 재료를 말하면, 벡터 검색(Vector Search) 기술을 통해 가장 유사도가 높은 레시피를 찾아내고, LLM(대규모 언어 모델)이 이를 맛있게 요약하여 추천하는 개인화된 요리 어시스턴트를 구축합니다.

• 핵심 KPI: 기존 서비스(만개의레시피, Super Cook 등)와 달리 **"남는 재료 최소화"**를 핵심 KPI로 설정하여 실질적인 재료 완전 소진을 목표로 최적의 조리 계획을 설계합니다.

## ❤️ 기대효과
• 식재료 낭비 감소: 불필요한 추가 구매를 억제하고 식비 절감과 음식물 쓰레기 감소라는 경제적·환경적 가치를 동시에 제공합니다.

• 결정 장애 해소: "무엇을 먹을까"라는 고민을 "어떻게 다 쓸까"라는 해결책으로 바꾸어주는 맞춤형 솔루션을 제공합니다.

• 신뢰성 높은 정보 (환각 방지): 실제 레시피 데이터 기반 RAG 파이프라인 구축으로 LLM의 환각 현상(Hallucination)을 방지하고 정확한 정보를 전달합니다.

## 👤 대상 사용자
• 자취생 및 1인 가구: 소량으로 남은 재료 처리가 고민인 사용자.

• 초보 요리사: 재료 이름만으로 간단하고 명확한 조리법을 찾고 싶은 사용자.

• 바쁜 직장인: 퇴근 후 냉장고에 있는 재료로 빠르게 메뉴를 결정하고 싶은 사람.

• 식단 관리가 필요한 사람: 특정 재료(알레르기 유발 재료 등)를 제외하고 안전한 요리를 찾고 싶은 사용자.



# 4. 핵심 기술 및 아키텍처

<img width="1095" height="615" alt="시스템" src="https://github.com/user-attachments/assets/deb26b6f-27fc-4daf-bcdf-b533aa4f804e" />

## 📊 데이터 파이프라인 (Data Engineering)
• 수집: '만개의 레시피' 웹 크롤링을 통해 56,000건 이상의 기본 조리 데이터를 대량 확보했습니다.

• 정제: 필수 정보(재료, 조리법)가 누락된 결측값을 제거하고, 분석에 불필요한 수식어 및 상업용 키워드를 지우는 불용어 처리 등 5단계 자동화 파이프라인을 통해 순수 조리 데이터를 정제했습니다.

• 적재: RAG 시스템 구축을 위해 정제된 데이터를 JSONL 형식으로 변환 후 MongoDB Atlas Vector DB에 적재했습니다.

## 🧠 동적 검색 아키텍처 (RAG & Fallback)
• 1차 벡터 검색: 사용자가 입력한 재료 키워드를 추출하여 256차원 벡터로 변환한 뒤, MongoDB에서 코사인 유사도 검색을 수행합니다.

• 실시간 Fallback 메커니즘: 유사도 점수가 기준치(0.75) 이상일 경우 DB 내 상위 3개 레시피를 가져옵니다. 만약 DB 검색 결과가 미달(0.75 미만)일 경우, 네이버 검색 API를 실시간으로 호출하여 최신 블로그 본문을 크롤링하고 청킹(Chunking)하여 지식 기반 데이터로 확장·대체 답변을 생성합니다.

• ✍️ 프롬프트 엔지니어링 (Prompt Engineering)단순 검색 결과를 그대로 전달하지 않고, 검색된 레시피 데이터에 **사용자 페르소나(알레르기 유발 재료, 요리 난이도/시간, 현재 보유 중인 양념/소스)**를 동적으로 결합하여 LLM 시스템 프롬프트를 구성합니다. 이를 통해 개인의 상황에 완벽히 맞춰진 구조화된 맞춤형 요리 가이드를 생성합니다.


# 5. 프로젝트 디렉토리 구조
```
SKN25-3RD-3TEAM/
├── backend/
│   ├── db/
│   │   └── mongo_db.py         # MongoDB 연결 및 컬렉션 반환 모듈
│   ├── etl/
│   │   └── embed_recipes.py    # 데이터 1000개씩 임베딩하는 ETL 자동화 스크립트
│   ├── rag/
│   │   ├── prompts.py          # 재료 추출 및 레시피 추천용 프롬프트 보관
│   │   ├── retriever.py        # MongoDB Atlas Vector Search 검색 로직
│   │   ├── pipeline.py         # 질문 -> 추출 -> 검색 -> 답변생성 파이프라인
│   │   └── search_engine.py    # DB 데이터 부족 시 네이버 크롤링 Fallback 도구
│   ├── api/
│   │   └── main.py             # FastAPI 백엔드 엔드포인트
│   └── utils/
│       └── config.py           # .env 로드 및 전역 클라이언트 설정
├── frontend/
│   └── recipe_ui.py            # Streamlit UI 프론트엔드
├── .env                        # API 키 및 DB URI
└── requirements.txt            # 의존성 패키지
```


# 6. 기술 스택
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


# 7. 향후 과제 (Future Works)
• 정규화 작업 고도화: 특수기호 삭제 및 동의어 mapping 과정을 고도화하여 코사인 유사도 계산의 정확성을 더욱 향상시킬 계획입니다.

• 칼로리 계산 제공: 추천된 레시피의 예상 칼로리를 자동으로 계산하여 사용자의 건강한 식단 관리를 돕는 기능을 추가할 예정입니다.

• 사진 기반 재료 자동 인식 (Vision AI): 냉장고 사진을 찍어 전송하기만 하면 AI가 재료를 자동 인식하여 즉시 레시피를 추천하는 편의 기능을 기획 중입니다.

• 데이터 파이프라인 자동화: Airflow를 활용해 레시피 데이터를 주기적으로 수집하고 벡터DB를 자동으로 최신화하는 MLOps 환경을 구축할 것입니다.

# 8. 수행결과

https://github.com/user-attachments/assets/0533d0f2-6f13-4a20-a514-6a895814f425