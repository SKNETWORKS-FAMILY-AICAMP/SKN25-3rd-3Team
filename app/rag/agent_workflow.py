import os
import re
from typing import Dict, Any, List

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# 내부 모듈 임포트
from app.rag.prompts import (
    INGREDIENT_EXTRACT_PROMPT, 
    DISH_NAME_PROMPT, 
    get_recipe_prompt
)
from app.rag.search_engine import (
    search_naver_blogs, 
    fetch_blog_body, 
    clean_html,
    resolve_blog_url
)
from app.rag.rag_loader import CHROMA_PERSIST_DIR, build_vector_db

load_dotenv()

class RecipeAgent:
    def __init__(self):
        print("[Agent] RecipeAgent 초기화 시작...")
        # 1. 모델 설정 (요금 효율적인 gpt-4o-mini 사용, 30초 타임아웃)
        self.llm = ChatOpenAI(
            model="gpt-4o-mini", 
            temperature=0.2,
            request_timeout=30
        )
        
        # 2. 임베딩 및 로컬 벡터 DB 로드
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            request_timeout=15
        )
        self.vectorstore = Chroma(
            persist_directory=CHROMA_PERSIST_DIR,
            embedding_function=self.embeddings
        )
        print(f"[Agent] RecipeAgent 초기화 완료! (DB 경로: {CHROMA_PERSIST_DIR})")
        
        # 3. 검색 임계값
        self.similarity_threshold = 0.5 

    def _extract_keywords(self, question: str) -> str:
        """질문에서 핵심 재료 키워드를 추출합니다."""
        chain = INGREDIENT_EXTRACT_PROMPT | self.llm | StrOutputParser()
        return chain.invoke({"question": question})

    def _identify_dish_name(self, ingredients: str, blog_items: list) -> str:
        """블로그 제목들을 분석하여 최적의 요리 이름을 결정합니다."""
        titles = "\n".join([clean_html(item.get('title', '')) for item in blog_items])
        chain = DISH_NAME_PROMPT | self.llm | StrOutputParser()
        return chain.invoke({"ingredients": ingredients, "titles": titles})

    def _get_web_context(self, question: str) -> str:
        """네이버 검색 및 크롤링을 통해 외부 컨텍스트를 생성합니다."""
        # 1단계: 재료 추출 및 정찰 검색 (최신순 5개)
        ingredients = self._extract_keywords(question)
        print(f"[Agent] 추출된 재료: {ingredients} (정찰 검색 중...)")
        # 정찰 검색에 '레시피'를 붙여 맛집 리뷰 대신 요리법 포스팅이 걸리도록 함
        explore_items = search_naver_blogs(f"{ingredients} 레시피", display=5, sort_type="date")

        if not explore_items:
            return ""

        # 2단계: 진짜 요리 이름 확정
        dish_name = self._identify_dish_name(ingredients, explore_items)
        print(f"[Agent] 확정된 요리명: '{dish_name}' (상세 검색 및 크롤링 시작)")

        # 3단계: 상세 검색 (정확도순 3개) 및 본문 크롤링
        target_items = search_naver_blogs(f"{dish_name} 레시피", display=3, sort_type="sim")
        blog_docs = []
        for item in target_items:
            body = fetch_blog_body(item['link'])
            if body:
                real_url = resolve_blog_url(item['link'])
                # 💡 수정 포인트: 본문에 URL을 붙이지 않고 metadata에 안전하게 보관합니다.
                from langchain_core.documents import Document
                blog_docs.append(Document(page_content=body, metadata={"source_url": real_url}))

        if not blog_docs:
            return ""

        # 4단계: 실시간 임시 벡터 DB 구축 및 컨텍스트 추출
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_documents(blog_docs)
        
        temp_db = Chroma.from_documents(documents=chunks, embedding=self.embeddings)
        relevant_docs = temp_db.similarity_search(dish_name, k=5)
        
        # 💡 수정 포인트: 검색된 조각들의 메타데이터에서 URL을 다시 꺼내옵니다. (중복 제거)
        found_urls = set(doc.metadata.get("source_url", "") for doc in relevant_docs if doc.metadata.get("source_url"))
        
        # LLM에게 넘겨줄 최종 텍스트 조립
        context_text = "\n\n".join([doc.page_content for doc in relevant_docs])
        if found_urls:
            urls_text = "\n".join([f"출처 URL: {url}" for url in found_urls])
            return f"{context_text}\n\n[웹 검색 출처]\n{urls_text}"
        
        return context_text

    def run(self, question: str, preferences: Dict[str, str], chat_history: List = []) -> str:
        print(f"\n{'='*50}")
        print(f"[Agent] run() 진입 - 질문: '{question}'")
        print(f"[Agent] 설정: {preferences}")
        print(f"{'='*50}")
        
        # 1단계: 질문에서 핵심 재료 키워드를 추출하여 검색 정확도를 높임
        print("[Agent] 1단계: 키워드 추출 중 (OpenAI API 호출)...")
        search_query = self._extract_keywords(question)
        print(f"[Agent] 내부 DB 검색 키워드: '{search_query}'")
        
        # 2단계: 추출된 키워드로 로컬 벡터 DB 검색
        local_results = self.vectorstore.similarity_search_with_score(search_query, k=5)
        
        # 디버깅: 실제 거리 점수와 매칭된 문서 제목 출력
        for doc, score in local_results:
            title = doc.metadata.get("title", doc.page_content[:30])
            print(f"  - [{round(score, 3)}] {title}")
        
        # 코사인 거리 0.7 미만(유사도 0.3 이상)이면 유효한 것으로 판단
        # (짧은 재료 키워드 vs 긴 레시피 문서 간 거리는 원래 넓게 나옴)
        valid_local = [doc for doc, score in local_results if score < 0.7]

        if valid_local:
            print(f"[Agent] 내부 DB에서 {len(valid_local)}개 관련 레시피 발견!")
            context = "\n\n".join([doc.page_content for doc in valid_local])
        else:
            print("[Agent] 내부 DB 정보 부족. 네이버 딥 크롤링 모드 가동.")
            context = self._get_web_context(question)

        if not context:
            return "해당되는 레시피가 없습니다." # prompts.py의 규칙 적용

        # 3. 최종 레시피 생성 Chain 실행
        prompt = get_recipe_prompt()
        chain = (
            RunnablePassthrough.assign(
                context=lambda x: context,
                chat_history=lambda x: chat_history,
                allergies=lambda x: preferences.get("allergies", "없음"),
                difficulty=lambda x: preferences.get("difficulty", "보통"),
                cooking_time=lambda x: preferences.get("cooking_time", "30분")
            )
            | prompt
            | self.llm
            | StrOutputParser()
        )

        return chain.invoke({"question": question})

# --- 실행 테스트 ---
if __name__ == "__main__":
    agent = RecipeAgent()
    user_prefs = {"allergies": "없음", "difficulty": "초보", "cooking_time": "20분"}
    
    # 1. 내부 DB 테스트 (예: 크래미 유부초밥) [cite: 21]
    print("\n[Test 1] 로컬 검색 테스트")
    print(agent.run("유부초밥이랑 크래미 있어", user_prefs))

    # 2. 웹 검색 테스트 (예: 이북식 찜닭) [cite: 24, 54]
    print("\n[Test 2] 웹 딥 크롤링 테스트")
    print(agent.run("이북식 찜닭 만드는 법 알려줘", user_prefs))