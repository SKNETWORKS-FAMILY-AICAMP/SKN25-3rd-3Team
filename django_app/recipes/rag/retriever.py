"""LangChain 기반 MongoDB Atlas Vector Search 래퍼.

3차 프로젝트의 backend/rag/retriever.py에서 import 경로만 변경했습니다.
score_threshold는 .env로 외부화하여 데모/튜닝에 유리하게 만들었습니다.
"""
import os

from langchain_community.vectorstores import MongoDBAtlasVectorSearch
from langchain_openai import OpenAIEmbeddings

from recipes.db.mongo_db import recipe_collection
from recipes.utils.config import OPENAI_API_KEY

# 임베딩 + 벡터스토어 초기화
embeddings = OpenAIEmbeddings(
    openai_api_key=OPENAI_API_KEY,
    model="text-embedding-3-small",
    dimensions=256,  # DB 인덱스 차원과 동일 필수
)

vector_store = MongoDBAtlasVectorSearch(
    collection=recipe_collection,
    embedding=embeddings,
    index_name="vector_index",
    text_key="ingredients_text",
    embedding_key="ingredients_embedding",
)

DEFAULT_SCORE_THRESHOLD = float(os.getenv("RAG_SCORE_THRESHOLD", "0.75"))


def search_similar_recipes(
    query_text: str,
    top_k: int = 3,
    score_threshold: float = DEFAULT_SCORE_THRESHOLD,
) -> list:
    """벡터 유사도 기반 레시피 검색. 임계값 미만은 필터링."""
    if not query_text or query_text == "없음":
        return []

    try:
        total_docs = recipe_collection.count_documents({})
        embedded_docs = recipe_collection.count_documents(
            {"ingredients_embedding": {"$exists": True}}
        )
        print(
            f"\n🚨 [DB 상태] 전체 레시피: {total_docs} | "
            f"임베딩 완료: {embedded_docs}"
        )

        results = vector_store.similarity_search_with_score(query=query_text, k=top_k)

        if results:
            print(f"📊 '{query_text}' 검색 결과 (커트라인 {score_threshold}):")
            for i, (doc, score) in enumerate(results, 1):
                title = doc.metadata.get("title", "제목 없음")
                print(f"   {i}위: {title} (유사도 {score:.4f})")
        else:
            print(f"📊 '{query_text}' 검색 결과 없음")

        filtered = []
        for doc, score in results:
            if score >= score_threshold:
                recipe_data = doc.metadata
                recipe_data["ingredients"] = doc.page_content
                recipe_data["score"] = score
                filtered.append(recipe_data)

        print(f"🔍 [Retriever] 통과 레시피 {len(filtered)}건")
        return filtered

    except Exception as e:
        print(f"⚠️ [Retriever] 벡터 검색 오류: {e}")
        return []
