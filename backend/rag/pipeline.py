# =====================================================================
# [전체 프로젝트에서의 역할: LCEL 기반 RAG 워크플로우 지휘소]
# 이 파일은 LangChain Expression Language(LCEL) 체인 구조를 활용하여
# 질문 분석부터 최종 추천 답변 생성까지의 전체 프로세스를 관리합니다.
# 1.0대 버전 이상의 LangChain 표준 규격을 준수하여 'Prompt | LLM | Parser'
# 형태의 파이프라인을 구축하고, DB 검색 실패 시 웹 검색(Fallback)을 수행합니다.
# =====================================================================

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from backend.utils.config import OPENAI_API_KEY
from backend.rag.prompts import EXTRACTION_SYSTEM_PROMPT, DISH_NAME_PROMPT_TEMPLATE, build_system_prompt
from backend.rag.retriever import search_similar_recipes
from backend.rag.search_engine import search_naver_blogs, fetch_blog_body, clean_html, resolve_blog_url

class RecipeAgent:
    def __init__(self):
        """ChatOpenAI 및 기본 출력 파서 초기화"""
        # 제공된 패키지 리스트의 langchain-openai 1.1.12 규격 사용
        self.llm = ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            model="gpt-4o-mini",
            temperature=0
        )
        self.parser = StrOutputParser()
        print("🚀 [Pipeline] LangChain v1.x 및 LCEL 기반 RecipeAgent 가동 시작.")

    # ---------------------------------------------------------------------
    # 1. 식재료 추출 체인 (LCEL)
    # [설계 의도] 사용자의 자연어 질문에서 검색에 필요한 키워드만 정교하게 추출합니다.
    # LCEL의 파이프 연산자(|)를 사용하여 데이터 흐름을 명확하게 정의했습니다.
    # ---------------------------------------------------------------------
    def _extract_ingredients(self, user_query: str) -> str:
        """사용자 입력에서 요리 재료 키워드만 추출합니다."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", EXTRACTION_SYSTEM_PROMPT),
            ("user", "{query}")
        ])
        
        # 체인 선언: Prompt | LLM | Parser
        chain = prompt | self.llm | self.parser
        extracted = chain.invoke({"query": user_query})
        
        print(f"🧠 [Pipeline] 추출된 키워드: {extracted}")
        return extracted

    # ---------------------------------------------------------------------
    # 2. 네이버 블로그 검색 및 요리명 확정 로직 (Fallback)
    # [설계 의도] 내부 DB 검색 결과가 부족할 때 가동되며, 웹 검색 결과로부터
    # 가장 적절한 요리명을 LLM 체인을 통해 도출해냅니다.
    # ---------------------------------------------------------------------
    def _fallback_web_search(self, ingredients_str: str) -> list:
        print(f"🕵️ [Web Search] DB 내 관련 정보 부족. 네이버 블로그 검색으로 전환합니다...")
        
        # 1. 초기 검색 (최신순)
        explore_items = search_naver_blogs(f"{ingredients_str} 레시피", display=5, sort_type="date")
        if not explore_items:
            return []
        
        # 2. 요리명 확정 체인 실행 (LCEL)
        titles = "\n".join([clean_html(i['title']) for i in explore_items])
        prompt = ChatPromptTemplate.from_template(DISH_NAME_PROMPT_TEMPLATE)
        chain = prompt | self.llm | self.parser
        
        dish_name = chain.invoke({"ingredients": ingredients_str, "titles": titles})
        print(f"💡 [Web Search] 블로그 분석 결과 확정된 요리명: '{dish_name}'")
        
        # 3. 확정된 요리명으로 본문 수집
        target_items = search_naver_blogs(f"{dish_name} 레시피", display=2, sort_type="sim")
        web_recipes = []
        for item in target_items:
            body = fetch_blog_body(item['link'], max_chars=1200)
            if body:
                web_recipes.append({
                    "title": f"[웹 검색] {clean_html(item['title'])}",
                    "url": resolve_blog_url(item['link']),
                    "ingredients": ingredients_str,
                    "steps": [body]
                })
        return web_recipes

    # ---------------------------------------------------------------------
    # 3. 전체 파이프라인 가동 (Main Run)
    # [설계 의도] 재료 추출 -> 검색 -> 최종 답변 생성의 단계를 거칩니다.
    # 최종 답변 생성 단계에서는 LangChain 메시지 구조를 사용하여 대화의 문맥을 유지합니다.
    # ---------------------------------------------------------------------
    def run(self, question: str, preferences: dict = None, chat_history: list = None) -> str:
        # Step 1: 재료 추출 체인 가동
        ingredient_keywords = self._extract_ingredients(question)
        if "없음" in ingredient_keywords:
            return "식재료를 포함해서 다시 질문해 주세요! (예: 감자랑 양파로 뭐 해 먹지?)"

        # Step 2: LangChain 기반 벡터 검색 실행
        retrieved_recipes = search_similar_recipes(ingredient_keywords)
        
        # Step 3: 필요 시 웹 검색 Fallback 실행
        if not retrieved_recipes:
            retrieved_recipes = self._fallback_web_search(ingredient_keywords)
            
        if not retrieved_recipes:
            return f"현재 적절한 레시피 정보를 찾지 못했습니다."

        # Step 4: 최종 답변 생성 체인 구축 (LCEL)
        # build_system_prompt를 활용해 동적인 지시문을 생성합니다.
        system_text = build_system_prompt(retrieved_recipes, preferences)
        
        messages = [("system", system_text)]
        
        # 대화 내역 주입
        if chat_history:
            for msg in chat_history[-4:]:
                role = "user" if msg.get("role") == "user" else "assistant"
                messages.append((role, msg.get("text", "")))
        
        messages.append(("user", "{question}"))
        
        # 응답 생성을 위한 최종 체인 구성
        # 0.7의 Temperature로 적절한 친절함과 창의성을 유도합니다.
        final_prompt = ChatPromptTemplate.from_messages(messages)
        final_llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model="gpt-4o-mini", temperature=0.7)
        final_chain = final_prompt | final_llm | self.parser
        
        print(f"🔥 [Pipeline] LangChain 엔진을 통해 최종 답변 생성 중...")
        return final_chain.invoke({"question": question})