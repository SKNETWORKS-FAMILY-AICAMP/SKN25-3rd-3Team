# =====================================================================
# [전체 프로젝트에서의 역할: LangChain 기반 벡터 검색 엔진]
# 이 파일은 LangChain의 'MongoDBAtlasVectorSearch'를 사용하여 
# 클라우드 데이터베이스의 벡터 검색 기능을 수행하는 모듈입니다.
# 제공된 패키지 버전(langchain-community 0.4.1)의 규격에 맞춰
# 사용자의 질문을 벡터로 변환하고 MongoDB Atlas의 vectorSearch index와 통신합니다.
# =====================================================================

from langchain_community.vectorstores import MongoDBAtlasVectorSearch
from langchain_openai import OpenAIEmbeddings
from backend.db.mongo_db import recipe_collection
from backend.utils.config import OPENAI_API_KEY

# ---------------------------------------------------------------------
# 1. OpenAI 임베딩 및 벡터스토어 초기화
# [설계 의도] 
# 'text-embedding-3-small' 모델을 사용하여 256차원으로 임베딩을 생성합니다.
# 이는 DB 적재 시 사용된 규격과 동일하며, LangChain의 통합 인터페이스를 통해 관리됩니다.
# ---------------------------------------------------------------------
embeddings = OpenAIEmbeddings(
    openai_api_key=OPENAI_API_KEY,
    model="text-embedding-3-small",
    dimensions=256  # 🚨 DB의 'ingredients_embedding' 필드 규격과 일치 필수
)

# MongoDB 벡터스토어 객체 생성
vector_store = MongoDBAtlasVectorSearch(
    collection=recipe_collection,
    embedding=embeddings,
    index_name="vector_index",           # MongoDB Atlas에 설정된 인덱스 이름
    text_key="ingredients_text",         # 검색 대상 텍스트 필드
    embedding_key="ingredients_embedding" # 벡터 데이터 필드
)

# ---------------------------------------------------------------------
# 2. 유사 레시피 검색 함수
# [설계 의도]
# LangChain의 'similarity_search_with_relevance_scores' 메서드를 사용하여
# 검색 결과와 유사도 점수를 함께 가져옵니다. 이를 통해 설정한 임계값(0.75) 미만의
# 연관성 낮은 레시피를 필터링하여 답변의 품질을 보장합니다.
# ---------------------------------------------------------------------
def search_similar_recipes(query_text: str, top_k: int = 3, score_threshold: float = 0.75) -> list:
    """LangChain 벡터스토어를 활용하여 유사도 기반 레시피를 검색합니다."""
    if not query_text or query_text == "없음":
        return []

    try:
        # 검색을 수행하기 직전에 DB에 데이터가 정상적으로 있는지 확인합니다.
        total_docs = recipe_collection.count_documents({})
        embedded_docs = recipe_collection.count_documents({"ingredients_embedding": {"$exists": True}})
        print(f"\n🚨 [DB 상태 점검] 전체 레시피: {total_docs}개 | 벡터 임베딩 완료: {embedded_docs}개")

        # 유사도 점수를 포함한 검색 수행
        results = vector_store.similarity_search_with_score(
            query=query_text,
            k=top_k
        )

        # [디버깅] 원본 점수 출력
        if results:
            print(f"📊 [디버깅] '{query_text}' 검색 결과 원본 점수 (커트라인: {score_threshold}):")
            for i, (doc, score) in enumerate(results, 1):
                title = doc.metadata.get('title', '제목 없음')
                print(f"   {i}위: {title} (유사도: {score:.4f})")
        else:
            print(f"📊 [디버깅] '{query_text}' 검색 결과가 아예 없습니다.")

        filtered_results = []
        for doc, score in results:
            if score >= score_threshold:
                recipe_data = doc.metadata
                recipe_data["ingredients"] = doc.page_content
                recipe_data["score"] = score
                filtered_results.append(recipe_data)

        print(f"🔍 [Retriever] LangChain(v1.x) 엔진을 통해 {len(filtered_results)}개의 레시피 탐색 완료.")
        return filtered_results

    except Exception as e:
        print(f"⚠️ [Retriever] 벡터 검색 중 오류 발생: {e}")
        return []