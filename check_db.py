import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# 환경 변수 로드 (API 키 인식)
load_dotenv()

# rag_loader.py와 동일한 DB 경로 설정
CHROMA_PERSIST_DIR = os.path.join(os.getcwd(), "vector_db", "chroma")

print(f"[{CHROMA_PERSIST_DIR}] 경로의 DB를 불러옵니다...")

# 임베딩 모델 로드 (DB 생성 시와 동일한 모델 사용)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Chroma(
    persist_directory=CHROMA_PERSIST_DIR, 
    embedding_function=embeddings
)

# DB 내의 모든 데이터 가져오기
db_data = vectorstore.get()

total_chunks = len(db_data['ids'])
print(f"\n✅ 현재 DB에 저장된 총 데이터(청크) 수: {total_chunks}개")

# 데이터가 있다면 어떻게 들어있는지 5개만 미리보기
if total_chunks > 0:
    print("\n🔍 [저장된 데이터 미리보기]")
    
    # 중복 제목을 제거하고 어떤 요리들이 있는지 확인하기 위한 Set
    unique_titles = set()
    
    for i in range(total_chunks):
        metadata = db_data['metadatas'][i]
        unique_titles.add(metadata.get('title', '제목 없음'))
        
        # 첫 5개 청크만 상세 내용 출력
        if i < 5:
            doc_id = db_data['ids'][i]
            content = db_data['documents'][i]
            print(f"[{i+1}] 문서 ID: {doc_id}")
            print(f"    요리명: {metadata.get('title', '제목 없음')}")
            print(f"    출처 URL: {metadata.get('url', 'URL 없음')}")
            print(f"    내용 일부: {content[:50]}...\n")
            
    print(f"🍲 DB에 저장된 고유 요리 종류 수: {len(unique_titles)}개")
    print(f"목록: {', '.join(list(unique_titles)[:10])} ...")