"""LCEL 기반 RAG 파이프라인.

[3차→4차 변경점]
1. import 경로: backend.* → recipes.*
2. 3단 Fallback:
     1차: MongoDB Atlas Vector Search
     2차: 네이버 블로그 웹 검색
     3차: LLM 일반 지식 (추측임 명시)
3. RecipeAgent.run()이 반환값에 candidates(저장 가능한 레시피 후보)도 포함.
   → 프론트에서 별 버튼 표시용. mongo_recipe_id 가 있으면 DB 레시피.
"""
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from recipes.rag.prompts import (
    DISH_NAME_PROMPT_TEMPLATE,
    EXTRACTION_SYSTEM_PROMPT,
    GENERAL_KNOWLEDGE_PROMPT,
    build_system_prompt,
)
from recipes.rag.retriever import search_similar_recipes
from recipes.rag.search_engine import (
    clean_html,
    fetch_blog_body,
    resolve_blog_url,
    search_naver_blogs,
)
from recipes.utils.config import OPENAI_API_KEY


def _serialize_recipe(recipe: dict) -> dict:
    """retrieved 레시피를 JSON 응답용으로 정제.

    - DB 레시피: _id (ObjectId)가 있을 수 있음 → 문자열로 변환
    - 웹 레시피: mongo_id 없음 → 빈 문자열
    - ingredients_summary, steps_summary는 카드 표시용 짧은 요약
    """
    raw_id = recipe.get("_id") or recipe.get("id")
    mongo_id = str(raw_id) if raw_id else ""

    ingredients = recipe.get("ingredients", "")
    if isinstance(ingredients, list):
        ing_text = ", ".join(str(i).replace(" 구매", "") for i in ingredients)
    else:
        ing_text = str(ingredients)

    steps = recipe.get("steps", [])
    if isinstance(steps, list):
        steps_text = " / ".join(str(s)[:80] for s in steps[:3])
    else:
        steps_text = str(steps)[:240]

    return {
        "mongo_recipe_id": mongo_id,
        "title": recipe.get("title", "제목 없음"),
        "url": recipe.get("url", ""),
        "ingredients_summary": ing_text[:500],
        "steps_summary": steps_text[:500],
    }


class RecipeAgent:
    """RAG 워크플로우 컨트롤러."""

    def __init__(self):
        self.llm = ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            model="gpt-4o-mini",
            temperature=0,
        )
        self.parser = StrOutputParser()
        print("🚀 [Pipeline] LangChain v1.x + LCEL 기반 RecipeAgent 가동.")

    # -----------------------------------------------------------------
    # 1. 식재료 추출
    # -----------------------------------------------------------------
    def _extract_ingredients(self, user_query: str) -> str:
        prompt = ChatPromptTemplate.from_messages(
            [("system", EXTRACTION_SYSTEM_PROMPT), ("user", "{query}")]
        )
        chain = prompt | self.llm | self.parser
        extracted = chain.invoke({"query": user_query})
        print(f"🧠 [Pipeline] 추출 키워드: {extracted}")
        return extracted

    # -----------------------------------------------------------------
    # 2-1. Fallback Lv.2 — 웹 검색
    # -----------------------------------------------------------------
    def _fallback_web_search(self, ingredients_str: str) -> list:
        print("🕵️ [Fallback Lv.2] 웹 검색으로 전환합니다...")

        explore_items = search_naver_blogs(
            f"{ingredients_str} 레시피", display=5, sort_type="date"
        )
        if not explore_items:
            return []

        titles = "\n".join([clean_html(i["title"]) for i in explore_items])
        prompt = ChatPromptTemplate.from_template(DISH_NAME_PROMPT_TEMPLATE)
        chain = prompt | self.llm | self.parser
        dish_name = chain.invoke({"ingredients": ingredients_str, "titles": titles})
        print(f"💡 [Fallback Lv.2] 확정된 요리명: '{dish_name}'")

        target_items = search_naver_blogs(
            f"{dish_name} 레시피", display=2, sort_type="sim"
        )
        web_recipes = []
        for item in target_items:
            body = fetch_blog_body(item["link"], max_chars=1200)
            if body:
                web_recipes.append(
                    {
                        "title": f"[웹 검색] {clean_html(item['title'])}",
                        "url": resolve_blog_url(item["link"]),
                        "ingredients": ingredients_str,
                        "steps": [body],
                    }
                )
        return web_recipes

    # -----------------------------------------------------------------
    # 2-2. Fallback Lv.3 — LLM 일반지식
    # -----------------------------------------------------------------
    def _fallback_general_knowledge(
        self, question: str, preferences: dict
    ) -> str:
        print("🤔 [Fallback Lv.3] DB·웹 모두 실패 → LLM 일반지식 가동.")
        prefs = preferences or {}
        prompt = ChatPromptTemplate.from_template(GENERAL_KNOWLEDGE_PROMPT)
        llm = ChatOpenAI(
            openai_api_key=OPENAI_API_KEY, model="gpt-4o-mini", temperature=0.3
        )
        chain = prompt | llm | self.parser
        return chain.invoke(
            {
                "question": question,
                "allergies": prefs.get("allergies", "없음"),
                "difficulty": prefs.get("difficulty", "상관없음"),
                "cooking_time": prefs.get("cooking_time", "상관없음"),
                "saved_sauces": prefs.get("saved_sauces", "없음"),
            }
        )

    # -----------------------------------------------------------------
    # 3. 메인 파이프라인
    # 반환: {
    #   "answer": str,
    #   "source": "db" | "web" | "llm" | "no_ingredient",
    #   "candidates": [ {mongo_recipe_id, title, url, ingredients_summary, steps_summary} ]
    # }
    # -----------------------------------------------------------------
    def run(
        self,
        question: str,
        preferences: dict = None,
        chat_history: list = None,
    ) -> dict:
        # Step 1: 재료 추출
        ingredient_keywords = self._extract_ingredients(question)
        if "없음" in ingredient_keywords:
            return {
                "answer": "식재료를 포함해서 다시 질문해 주세요! "
                          "(예: 감자랑 양파로 뭐 해 먹지?)",
                "source": "no_ingredient",
                "candidates": [],
            }

        # Step 2: 1차 — 벡터 DB 검색
        retrieved = search_similar_recipes(ingredient_keywords)
        source = "db"

        # Step 3: 2차 — 웹 fallback
        if not retrieved:
            retrieved = self._fallback_web_search(ingredient_keywords)
            if retrieved:
                source = "web"

        # Step 4: 3차 — LLM 일반지식 fallback
        if not retrieved:
            answer = self._fallback_general_knowledge(question, preferences)
            return {
                "answer": answer,
                "source": "llm",
                "candidates": [],  # LLM 추정은 저장 후보 없음
            }

        # Step 5: 정상 답변 생성
        system_text = build_system_prompt(retrieved, preferences)
        messages = [("system", system_text)]

        if chat_history:
            for msg in chat_history[-4:]:
                role = "user" if msg.get("role") == "user" else "assistant"
                messages.append((role, msg.get("text", "")))

        messages.append(("user", "{question}"))

        final_prompt = ChatPromptTemplate.from_messages(messages)
        final_llm = ChatOpenAI(
            openai_api_key=OPENAI_API_KEY, model="gpt-4o-mini", temperature=0.7
        )
        final_chain = final_prompt | final_llm | self.parser

        print(f"🔥 [Pipeline] 답변 생성 중 (source={source})...")
        answer = final_chain.invoke({"question": question})

        candidates = [_serialize_recipe(r) for r in retrieved]
        return {"answer": answer, "source": source, "candidates": candidates}
