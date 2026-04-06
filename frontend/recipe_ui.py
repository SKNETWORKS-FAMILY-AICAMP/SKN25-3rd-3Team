import streamlit as st
import streamlit.components.v1 as components
import sys
import os

# 프로젝트 루트를 sys.path에 추가 (app 패키지 임포트를 위해)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.rag.agent_workflow import RecipeAgent

# ── 페이지 설정 ──
st.set_page_config(
    page_title="냉털봇",
    page_icon="🧊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── 전역 스타일 ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif;
    background-color: #fff8f3;
}
.block-container { padding-top: 1rem !important; max-width: 480px !important; }
#MainMenu, footer, header { visibility: hidden; }

/* 열기/닫기 버튼 */
.stButton > button {
    border: 1.5px solid #EA580C !important;
    color: #EA580C !important;
    border-radius: 20px !important;
    background: transparent !important;
    font-size: 13px !important;
    padding: 6px 24px !important;
}
.stButton > button:hover { background: #EA580C !important; color: #fff !important; }
</style>
""", unsafe_allow_html=True)

# ── 세션 상태 초기화 ──
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "bot", "text": "안녕하세요! 🧅 냉장고 속 재료를 알려주시면 딱 맞는 레시피를 찾아드릴게요!"},
        {"role": "bot", "text": "아래 버튼을 눌러 시작하거나 재료를 직접 입력해보세요 👇"},
    ]
if "fridge_open" not in st.session_state:
    st.session_state.fridge_open = False
if "agent" not in st.session_state:
    st.session_state.agent = RecipeAgent()
if "user_input" not in st.session_state:
    st.session_state.user_input = None
if "faq_input" not in st.session_state:
    st.session_state.faq_input = None

# ── 사이드바: 사용자 취향 설정 ──
with st.sidebar:
    st.markdown("### 🔧 내 취향 필터 설정")
    st.caption("설정한 정보가 레시피 추천에 반영됩니다.")

    allergies = st.text_input(
        "⚠️ 알레르기 재료",
        value=st.session_state.get("allergies", "없음"),
        placeholder="예: 땅콩, 갑각류"
    )
    difficulty = st.selectbox(
        "👨‍🍳 요리 난이도",
        ["초보", "보통", "고수"],
        index=["초보", "보통", "고수"].index(st.session_state.get("difficulty", "초보"))
    )
    cooking_time = st.selectbox(
        "⏱️ 선호 조리 시간",
        ["15분", "20분", "30분", "45분", "60분"],
        index=["15분", "20분", "30분", "45분", "60분"].index(st.session_state.get("cooking_time", "20분"))
    )

    st.session_state.allergies = allergies
    st.session_state.difficulty = difficulty
    st.session_state.cooking_time = cooking_time


def get_user_preferences() -> dict:
    """현재 세션의 사용자 취향 설정을 딕셔너리로 반환합니다."""
    return {
        "allergies": st.session_state.get("allergies", "없음"),
        "difficulty": st.session_state.get("difficulty", "초보"),
        "cooking_time": st.session_state.get("cooking_time", "20분"),
    }


def get_chat_history() -> list:
    """
    LangChain MessagesPlaceholder에 넘길 대화 이력을 구성합니다.
    최근 10개 메시지만 사용하여 토큰을 절약합니다.
    """
    from langchain_core.messages import HumanMessage, AIMessage

    history = []
    recent = st.session_state.messages[-10:]
    for m in recent:
        if m["role"] == "user":
            history.append(HumanMessage(content=m["text"]))
        else:
            history.append(AIMessage(content=m["text"]))
    return history


def ask_agent(question: str) -> str:
    """RecipeAgent를 호출하여 답변을 받아옵니다."""
    agent: RecipeAgent = st.session_state.agent
    preferences = get_user_preferences()
    chat_history = get_chat_history()

    try:
        answer = agent.run(
            question=question,
            preferences=preferences,
            chat_history=chat_history
        )
    except Exception as e:
        answer = f"죄송합니다, 오류가 발생했어요 😢\n({e})"
    return answer


def process_user_message(user_text: str):
    """사용자 메시지를 처리하고 봇 응답을 세션에 추가합니다."""
    # 사용자 메시지 추가
    st.session_state.messages.append({"role": "user", "text": user_text})

    # Agent 호출 (로딩 표시는 Streamlit이 자동 처리)
    bot_reply = ask_agent(user_text)

    # 봇 응답 추가
    st.session_state.messages.append({"role": "bot", "text": bot_reply})


# ── 현재 상태 변수 ──
is_open = st.session_state.fridge_open

# ── 말풍선 HTML 생성 ──
msgs_html = ""
for m in st.session_state.messages:
    text = m["text"].replace("\n", "<br>")
    if m["role"] == "bot":
        msgs_html += f'''
        <div class="m">
            <div class="m-icon">🤖</div>
            <div class="bub b">{text}</div>
        </div>'''
    else:
        msgs_html += f'''
        <div class="m u">
            <div class="bub u">{text}</div>
            <div class="m-icon">🙋</div>
        </div>'''

# ── 냉장고 문 트랜스폼 값 ──
left_t  = "perspective(900px) rotateY(-122deg)" if is_open else "perspective(900px) rotateY(0deg)"
right_t = "perspective(900px) rotateY(122deg)"  if is_open else "perspective(900px) rotateY(0deg)"
inner_opacity  = "1" if is_open else "0"
inner_pointer  = "auto" if is_open else "none"
door_pointer   = "none" if is_open else "auto"

# ── 냉장고 HTML ──
fridge_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
* {{ box-sizing:border-box; margin:0; padding:0; }}
html, body {{ background:transparent; font-family:'Noto Sans KR',sans-serif; height:100%; }}

.scene {{ display:flex; flex-direction:column; align-items:center; padding:4px 0; }}

/* ── 냉장고 껍데기 ── */
.fridge {{
  position:relative;
  width:420px;
  height:680px;
  background:#e2ddd8;
  border-radius:26px;
  border:3px solid #c8c2bc;
  overflow:hidden;
}}

/* ── 냉장고 내부 전체 ── */
.inner {{
  position:absolute; inset:0;
  background:#fffaf5;
  border-radius:24px;
  display:flex; flex-direction:column;
  overflow:hidden;
  opacity:{inner_opacity};
  transition:opacity 0.5s ease 1s;
  pointer-events:{inner_pointer};
}}

/* 헤더 */
.hdr {{
  background:#EA580C; padding:14px 18px;
  display:flex; align-items:center; gap:12px; flex-shrink:0;
}}
.hdr-av {{
  width:40px; height:40px; border-radius:50%; background:#fff3ec;
  display:flex; align-items:center; justify-content:center; font-size:22px;
}}
.hdr-title {{ color:#fff; font-size:15px; font-weight:700; }}
.hdr-sub   {{ color:#ffd4b8; font-size:11px; margin-top:2px; }}
.hdr-dot   {{ width:9px; height:9px; border-radius:50%; background:#86efac; margin-left:auto; }}

/* 채팅창 */
.chat {{
  flex:1; overflow-y:auto;
  padding:14px 14px 10px;
  display:flex; flex-direction:column; gap:10px;
}}
.m {{ display:flex; gap:8px; align-items:flex-end; }}
.m.u {{ flex-direction:row-reverse; }}
.m-icon {{
  width:28px; height:28px; border-radius:50%;
  background:#fff3ec; border:1px solid #f5d0b0;
  display:flex; align-items:center; justify-content:center;
  font-size:14px; flex-shrink:0;
}}
.bub {{
  max-width:76%; padding:9px 13px; border-radius:16px;
  font-size:12.5px; line-height:1.6; word-break:keep-all;
}}
.bub.b {{ background:#fff3ec; border:1px solid #f5d0b0; color:#7c3a10; border-bottom-left-radius:3px; }}
.bub.u {{ background:#EA580C; color:#fff; border-bottom-right-radius:3px; }}

/* 입력창 - 비활성 표시용 (실제 입력은 Streamlit에서 처리) */
.inp-area {{
  flex-shrink:0;
  display:flex; align-items:center; gap:8px;
  padding:10px 14px;
  background:#fff8f2;
  border-top:1px solid #f0ddd0;
}}
.inp-area .fake-input {{
  flex:1; border:1.5px solid #f0d0b0; border-radius:22px;
  padding:9px 16px; font-size:12.5px; background:#fff;
  color:#aaa; font-family:'Noto Sans KR',sans-serif;
}}
.send-btn {{
  width:36px; height:36px; border-radius:50%;
  background:#EA580C; border:none;
  display:flex; align-items:center; justify-content:center; flex-shrink:0;
  opacity:0.5;
}}
.send-btn svg {{ width:14px; height:14px; fill:#fff; }}

/* FAQ 영역 */
.faq-area {{
  flex-shrink:0;
  background:#fff8f2;
  border-top:1px solid #f0ddd0;
  padding:10px 14px 16px;
}}
.faq-lbl {{
  font-size:10px; color:#b07050; font-weight:700;
  letter-spacing:0.05em; margin-bottom:8px;
}}
.faq-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:7px; }}
.faq-btn {{
  background:#fff; border:1.5px solid #f0c8a0;
  border-radius:22px; padding:9px 8px;
  font-size:12px; color:#9a4a10; cursor:default;
  text-align:center;
  font-family:'Noto Sans KR',sans-serif;
}}

/* ── 냉장고 문 ── */
.doors {{
  position:absolute; inset:0; display:flex;
  pointer-events:{door_pointer};
}}
.door {{
  width:50%; height:100%;
  background:linear-gradient(160deg,#dedad4 0%,#ccc8c2 100%);
  border:2.5px solid #b8b2ac;
  display:flex; align-items:center; justify-content:center;
  flex-direction:column; gap:10px;
  transform-origin:var(--ox) center;
  transition:transform 1.3s cubic-bezier(0.4,0,0.2,1);
  position:relative; will-change:transform;
}}
.door-l {{ --ox:0%; border-radius:24px 0 0 24px; border-right:1.5px solid #b0aaa4; transform:{left_t}; }}
.door-r {{ --ox:100%; border-radius:0 24px 24px 24px; border-left:1.5px solid #b0aaa4; transform:{right_t}; }}
.d-handle {{ width:6px; height:64px; background:#9a9490; border-radius:3px; position:absolute; }}
.door-l .d-handle {{ right:14px; }}
.door-r .d-handle {{ left:14px; }}
.d-char  {{ font-size:52px; font-weight:700; color:#6a6460; }}
.d-brand {{ font-size:10px; color:#aaa; letter-spacing:0.14em; }}
.fridge-top {{
  position:absolute; top:10px; left:50%; transform:translateX(-50%);
  width:70px; height:7px; background:#c8c2bc; border-radius:4px; z-index:10;
}}
</style>
</head>
<body>
<div class="scene">
  <div class="fridge">
    <div class="fridge-top"></div>

    <!-- ── 내부 챗봇 ── -->
    <div class="inner">
      <!-- 헤더 -->
      <div class="hdr">
        <div class="hdr-av">🍳</div>
        <div>
          <div class="hdr-title">냉털봇</div>
          <div class="hdr-sub">재료 소진 레시피 AI</div>
        </div>
        <div class="hdr-dot"></div>
      </div>

      <!-- 채팅 말풍선 -->
      <div class="chat" id="chatBody">
        {msgs_html}
      </div>

      <!-- 입력창 (안내용 - 실제 입력은 아래 Streamlit 위젯) -->
      <div class="inp-area">
        <div class="fake-input">⬇ 아래 입력창에 재료를 입력하세요</div>
        <div class="send-btn">
          <svg viewBox="0 0 24 24"><path d="M2 21l21-9L2 3v7l15 2-15 2z"/></svg>
        </div>
      </div>

      <!-- FAQ 버튼 (안내용) -->
      <div class="faq-area">
        <div class="faq-lbl">✨ 자주 찾는 기능 (아래 버튼 이용)</div>
        <div class="faq-grid">
          <div class="faq-btn">🥕 재료로 레시피 찾기</div>
          <div class="faq-btn">📅 오늘 뭐 먹지?</div>
          <div class="faq-btn">🔥 재료 소진 플랜</div>
          <div class="faq-btn">💪 다이어트 레시피</div>
        </div>
      </div>
    </div>

    <!-- ── 냉장고 문 ── -->
    <div class="doors">
      <div class="door door-l">
        <div class="d-handle"></div>
        <div class="d-char">냉</div>
        <div class="d-brand">NAENGTEOL</div>
      </div>
      <div class="door door-r">
        <div class="d-handle"></div>
        <div class="d-char">털</div>
        <div class="d-brand">RECIPE AI</div>
      </div>
    </div>
  </div>
</div>

<script>
  // 채팅창 최하단 스크롤
  var cb = document.getElementById('chatBody');
  if (cb) cb.scrollTop = cb.scrollHeight;
</script>
</body>
</html>
"""

# ── 냉장고 컴포넌트 렌더링 ──
components.html(fridge_html, height=700, scrolling=False)

# ── 열기/닫기 버튼 ──
col1, col2, col3 = st.columns([2, 2, 2])
with col2:
    label = "🚪 닫기" if is_open else "🧊 냉털 AI 시작하기"
    if st.button(label):
        st.session_state.fridge_open = not st.session_state.fridge_open
        st.rerun()

# ── 냉장고가 열려있을 때만 입력 UI 표시 ──
if is_open:
    st.markdown("---")

    # FAQ 빠른 버튼
    st.markdown(
        "<p style='font-size:12px; color:#b07050; font-weight:700; "
        "letter-spacing:0.05em; margin-bottom:4px;'>✨ 자주 찾는 기능</p>",
        unsafe_allow_html=True,
    )
    faq_cols = st.columns(4)
    faq_options = [
        ("🥕 재료로 찾기", "냉장고에 있는 재료로 뭐 만들 수 있어?"),
        ("📅 오늘 뭐 먹지?", "오늘 간단하게 만들어 먹을 메뉴 추천해줘"),
        ("🔥 재료 소진", "냉장고 재료 최대한 소진할 수 있는 레시피 알려줘"),
        ("💪 다이어트", "저칼로리 다이어트 레시피 추천해줘"),
    ]
    for i, (btn_label, question) in enumerate(faq_options):
        with faq_cols[i]:
            if st.button(btn_label, key=f"faq_{i}"):
                st.session_state.faq_input = question

    # 텍스트 입력
    user_text = st.chat_input("재료를 입력하세요... (예: 계란, 양파, 두부)")

    # FAQ 버튼이 눌렸을 경우 처리
    if st.session_state.faq_input:
        faq_q = st.session_state.faq_input
        st.session_state.faq_input = None
        with st.spinner("🍳 레시피를 찾고 있어요..."):
            process_user_message(faq_q)
        st.rerun()

    # 사용자가 직접 입력한 경우 처리
    if user_text:
        with st.spinner("🍳 레시피를 찾고 있어요..."):
            process_user_message(user_text)
        st.rerun()