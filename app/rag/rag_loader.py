import os
from typing import List, Dict, Any

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# 기존 DB 연결 모듈 (postgres_db.py) 임포트
from app.db.postgres_db import get_postgres_connection

# 환경변수 로드
load_dotenv()

# 벡터 DB 저장 경로 설정
CHROMA_PERSIST_DIR = os.path.join(os.getcwd(), "vector_db", "chroma")

def fetch_recipes_from_db(limit: int = 1000) -> List[Dict[str, Any]]:
    """
    PostgreSQL에서 정제된 레시피 데이터를 효율적으로 로드합니다.
    """
    query = """
        SELECT 
            r.id,
            r.title,
            r.url,
            (
                SELECT json_agg(i.normalized_text ORDER BY i.ingredient_index) 
                FROM parsed_recipe_ingredient i 
                WHERE i.parsed_recipe_id = r.id
            ) as ingredients,
            (
                SELECT json_agg(s.content ORDER BY s.step_index) 
                FROM parsed_recipe_step s 
                WHERE s.parsed_recipe_id = r.id
            ) as steps
        FROM parsed_recipe r
        WHERE r.parse_status = 'parsed'
        LIMIT %s;
    """
    
    recipes = []
    print(f"[DB] PostgreSQL에서 데이터를 조회 중입니다... (최대 {limit}건)")
    
    with get_postgres_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
            
            for row in rows:
                recipes.append({
                    "id": row["id"],
                    "title": row["title"],
                    "url": row["url"],
                    "ingredients": row["ingredients"] or [],
                    "steps": row["steps"] or []
                })
                
    print(f"[DB] 총 {len(recipes)}개의 데이터를 불러왔습니다.")
    return recipes

def format_recipe_to_text(recipe: Dict[str, Any]) -> str:
    """
    레시피를 검색에 최적화된 텍스트 포맷으로 변환합니다.
    """
    steps_text = "\n".join([f"{i+1}. {s}" for i, s in enumerate(recipe["steps"])])
    
    return (
        f"요리명: {recipe['title']}\n"
        f"필요 재료: {', '.join(recipe['ingredients'])}\n\n"
        f"[조리 순서]\n{steps_text}\n"
        f"출처: {recipe['url']}"
    )

def create_documents(recipes: List[Dict[str, Any]]) -> List[Document]:
    """
    데이터를 LangChain Document 객체로 변환합니다.
    """
    return [
        Document(
            page_content=format_recipe_to_text(r),
            metadata={"recipe_id": r["id"], "title": r["title"], "url": r["url"]}
        ) for r in recipes
    ]

def build_vector_db(documents: List[Document]):
    """
    문서를 분할하고 임베딩하여 ChromaDB를 구축합니다.
    """
    print("[RAG] 텍스트 분할 중 (Chunk Size: 500)...")
    # 기획서 기준 500자 청킹 적용 
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    print(f"[RAG] 생성된 청크 수: {len(chunks)}개")

    print("[RAG] 임베딩 및 Chroma DB 저장 중...")
    # 가성비 좋은 최신 모델 사용 [cite: 19, 114]
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    vectorstore = Chroma.from_documents(
        documents=chunks, 
        embedding=embeddings, 
        persist_directory=CHROMA_PERSIST_DIR,
        # 코사인 유사도를 사용하도록 메타데이터 추가
        collection_metadata={"hnsw:space": "cosine"} 
    )
    
    print(f"[RAG] 벡터 DB 구축 완료! (경로: {CHROMA_PERSIST_DIR})")
    return vectorstore

def main():
    # 1. 데이터 로드 (현재 약 120개 레시피가 있으므로 1000으로 충분) [cite: 105]
    recipes = fetch_recipes_from_db(limit=1000)
    
    if not recipes:
        print("적재할 데이터가 없습니다.")
        return

    # 2. Document 변환
    documents = create_documents(recipes)
    
    # 3. 벡터 DB 구축
    build_vector_db(documents)

if __name__ == "__main__":
    main()