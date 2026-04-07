# =====================================================================
# [전체 프로젝트에서의 역할: 통합 비즈니스 컨트롤러]
# 1. 페이지 설정: 브라우저 탭 이름과 아이콘을 '냉털봇'으로 최상단에서 정의합니다.
# 2. 무한 루프 방지: URL 파라미터가 실제로 존재할 때만 로직을 수행하고 화면을 갱신합니다.
# 3. 상태 관리: LangChain 객체 변환 및 RAG 파이프라인 호출을 담당합니다.
# =====================================================================

import streamlit as st
import os
import sys
from langchain_core.messages import HumanMessage, AIMessage

# ── 1. 페이지 기본 설정 (반드시 가장 먼저 실행되어야 탭 이름이 바뀝니다!) ──
st.set_page_config(
    page_title="냉털봇",
    page_icon="🧊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── 2. 경로 보정 및 모듈 임포트 ──
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from frontend.recipe_ui import render_custom_css, render_fridge_ui
from backend.rag.pipeline import RecipeAgent

# ── 3. 세션 상태 초기화 ──
def initialize_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "bot", "text": "안녕하세요! 🧅 냉장고 속 재료를 알려주시면 딱 맞는 레시피를 찾아드릴게요!"},
            {"role": "bot", "text": "냉장고 문을 열고 재료를 직접 입력해보세요 👇"},
        ]
    if "fridge_open" not in st.session_state: st.session_state.fridge_open = False
    if "just_opened" not in st.session_state: st.session_state.just_opened = False
    if "agent" not in st.session_state: st.session_state.agent = RecipeAgent()
    if "pending_question" not in st.session_state: st.session_state.pending_question = None
    if "allergies" not in st.session_state: st.session_state.allergies = "없음"
    if "difficulty" not in st.session_state: st.session_state.difficulty = "초보"
    if "cooking_time" not in st.session_state: st.session_state.cooking_time = "20분"
    if "saved_sauces" not in st.session_state: st.session_state.saved_sauces = []

def get_langchain_history():
    history = []
    for m in st.session_state.messages[-8:]:
        msg_obj = HumanMessage(content=m["text"]) if m["role"] == "user" else AIMessage(content=m["text"])
        history.append(msg_obj)
    return history

# ── 4. 핵심 버그 수정: 무한 루프 방지 및 액션 처리 ──
def handle_user_actions():
    params = st.query_params
    processed = False

    # 💡 [핵심 해결] 처리할 파라미터가 '실제로' 있을 때만 로직을 수행합니다.
    if "action" in params or "sauces" in params or "q" in params:
        if "action" in params and params["action"] == "sync_open":
            st.session_state.fridge_open = True
            st.session_state.just_opened = True

        elif "sauces" in params:
            raw = params["sauces"]
            if raw == "none":
                st.session_state.saved_sauces = []
                st.session_state.messages.append({"role": "bot", "text": "선택된 소스가 없어요 😅\n보유 중인 소스를 체크해 주세요!"})
            else:
                st.session_state.saved_sauces = raw.split(',')
                msg = f"소스 저장 완료! 🎉\n현재 사용 가능한 소스: {', '.join(st.session_state.saved_sauces)}"
                st.session_state.messages.append({"role": "bot", "text": msg})
            st.session_state.fridge_open = True

        elif "q" in params:
            st.session_state.allergies = params.get("allergy", st.session_state.allergies)
            st.session_state.difficulty = params.get("diff", st.session_state.difficulty)
            st.session_state.cooking_time = params.get("time", st.session_state.cooking_time)
            st.session_state.messages.append({"role": "user", "text": params["q"]})
            st.session_state.pending_question = params["q"]
            st.session_state.fridge_open = True

        processed = True

    # 파라미터를 처리했다면 비우고 화면을 강제로 딱 '한 번만' 갱신합니다.
    if processed:
        st.query_params.clear()
        st.rerun()

# ── 5. AI 응답 처리 ──
def process_ai_reply():
    if st.session_state.pending_question:
        user_q = st.session_state.pending_question
        st.session_state.pending_question = None
        
        with st.spinner("🍳 냉장고 속 재료로 최고의 레시피를 조합 중..."):
            prefs = {
                "allergies": st.session_state.allergies, 
                "difficulty": st.session_state.difficulty,
                "cooking_time": st.session_state.cooking_time,
                "saved_sauces": ", ".join(st.session_state.saved_sauces) if st.session_state.saved_sauces else "없음"
            }
            bot_reply = st.session_state.agent.run(question=user_q, preferences=prefs, chat_history=get_langchain_history())
            st.session_state.messages.append({"role": "bot", "text": bot_reply})
            st.rerun()

def main():
    initialize_state()
    handle_user_actions()
    process_ai_reply()
    
    render_custom_css()
    render_fridge_ui(
        st.session_state.messages, 
        st.session_state.fridge_open, 
        st.session_state.just_opened,
        st.session_state.allergies, 
        st.session_state.difficulty, 
        st.session_state.cooking_time, 
        st.session_state.saved_sauces
    )
    
    # 렌더링이 끝난 후 애니메이션 플래그 해제
    if st.session_state.just_opened:
        st.session_state.just_opened = False
        
    col1, col2, col3 = st.columns([1.5, 2.5, 1.5])
    with col2:
        if not st.session_state.fridge_open:
            if st.button("🧊 냉털 AI 시작하기", use_container_width=True):
                st.session_state.fridge_open = True
                st.session_state.just_opened = True
                st.rerun()
        else:
            if st.button("🚪 냉장고 닫기", use_container_width=True):
                st.session_state.fridge_open = False
                st.session_state.just_opened = False
                st.rerun()

if __name__ == "__main__":
    main()