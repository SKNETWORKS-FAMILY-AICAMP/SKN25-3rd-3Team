import streamlit as st
import streamlit.components.v1 as components
import sys
import os
import html as html_module
import json

# 프로젝트 루트를 sys.path에 추가
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
.block-container {
    padding-top: 0.5rem !important;
    padding-bottom: 0rem !important;
    max-width: 480px !important;
}
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] {
    display: none !important;
}

/* 열기/닫기 버튼 */
.stButton > button {
    border: 1.5px solid #EA580C !important;
    color: #EA580C !important;
    border-radius: 20px !important;
    background: transparent !important;
    font-size: 13px !important;
    padding: 6px 24px !important;
}
.stButton > button:hover {
    background: #EA580C !important;
    color: #fff !important;
}
hr { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ── 세션 상태 초기화 ──
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "bot", "text": "안녕하세요! 🧅 냉장고 속 재료를 알려주시면 딱 맞는 레시피를 찾아드릴게요!"},
        {"role": "bot", "text": "재료를 직접 입력하거나 아래 버튼을 눌러보세요 👇"},
    ]
if "fridge_open" not in st.session_state:
    st.session_state.fridge_open = False
if "agent" not in st.session_state:
    st.session_state.agent = RecipeAgent()
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None
if "allergies" not in st.session_state:
    st.session_state.allergies = "없음"
if "difficulty" not in st.session_state:
    st.session_state.difficulty = "초보"
if "cooking_time" not in st.session_state:
    st.session_state.cooking_time = "20분"


# ── 헬퍼 함수들 ──
def get_user_preferences() -> dict:
    return {
        "allergies": st.session_state.allergies,
        "difficulty": st.session_state.difficulty,
        "cooking_time": st.session_state.cooking_time,
    }

def get_chat_history() -> list:
    from langchain_core.messages import HumanMessage, AIMessage
    history = []
    for m in st.session_state.messages[-10:]:
        if m["role"] == "user":
            history.append(HumanMessage(content=m["text"]))
        else:
            history.append(AIMessage(content=m["text"]))
    return history

def ask_agent(question: str) -> str:
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
    st.session_state.messages.append({"role": "user", "text": user_text})
    st.session_state.pending_question = user_text


# ── 채팅 입력 처리 (Streamlit 네이티브 - 페이지 하단 고정) ──
# 이것은 iframe 내 입력창의 백업으로, 냉장고가 열렸을 때만 표시
is_open = st.session_state.fridge_open

# ── URL 쿼리 파라미터로 전달된 메시지 처리 (pending보다 먼저!) ──
query_params = st.query_params
if "q" in query_params:
    user_q = query_params["q"]
    print(f"[UI] 쿼리 파라미터로 메시지 수신: '{user_q}'")
    # 취향 설정도 쿼리에서 업데이트
    if "allergy" in query_params:
        st.session_state.allergies = query_params["allergy"]
    if "diff" in query_params:
        st.session_state.difficulty = query_params["diff"]
    if "time" in query_params:
        st.session_state.cooking_time = query_params["time"]
    
    # 냉장고 열린 상태 유지
    st.session_state.fridge_open = True
    is_open = True
    
    # 쿼리 파라미터 클리어 (무한 루프 방지)
    st.query_params.clear()
    
    # 메시지 처리
    process_user_message(user_q)
    st.rerun()

# ── pending 질문 처리 ──
if st.session_state.pending_question:
    question = st.session_state.pending_question
    st.session_state.pending_question = None
    print(f"[UI] pending 질문 처리 시작: '{question}'")
    with st.spinner("🍳 레시피를 찾고 있어요..."):
        bot_reply = ask_agent(question)
    print(f"[UI] 응답 수신 완료 (길이: {len(bot_reply)}자)")
    st.session_state.messages.append({"role": "bot", "text": bot_reply})


# ── 말풍선 HTML 생성 ──
msgs_html = ""
for m in st.session_state.messages:
    safe_text = html_module.escape(m["text"]).replace("\n", "<br>")
    if m["role"] == "bot":
        msgs_html += f'''
        <div class="m">
            <div class="m-icon">🤖</div>
            <div class="bub b">{safe_text}</div>
        </div>'''
    else:
        msgs_html += f'''
        <div class="m u">
            <div class="bub u">{safe_text}</div>
            <div class="m-icon">🙋</div>
        </div>'''

# ── 냉장고 문 트랜스폼 ──
left_t  = "perspective(900px) rotateY(-122deg)" if is_open else "perspective(900px) rotateY(0deg)"
right_t = "perspective(900px) rotateY(122deg)"  if is_open else "perspective(900px) rotateY(0deg)"
inner_opacity = "1" if is_open else "0"
inner_pointer = "auto" if is_open else "none"
door_pointer  = "none" if is_open else "auto"

# ── 냉장고 통합 HTML (채팅 + 입력창 + FAQ + 설정 모두 포함) ──
fridge_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
* {{ box-sizing:border-box; margin:0; padding:0; }}
html, body {{ background:transparent; font-family:'Noto Sans KR',sans-serif; height:100%; overflow:hidden; }}

.scene {{ display:flex; flex-direction:column; align-items:center; padding:4px 0; }}

.fridge {{
  position:relative;
  width:420px; height:720px;
  background:#e2ddd8;
  border-radius:26px;
  border:3px solid #c8c2bc;
  overflow:hidden;
}}

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
  background:#EA580C; padding:12px 16px;
  display:flex; align-items:center; gap:10px; flex-shrink:0;
}}
.hdr-av {{
  width:36px; height:36px; border-radius:50%; background:#fff3ec;
  display:flex; align-items:center; justify-content:center; font-size:20px;
}}
.hdr-title {{ color:#fff; font-size:14px; font-weight:700; }}
.hdr-sub   {{ color:#ffd4b8; font-size:10px; margin-top:1px; }}
.hdr-dot   {{ width:8px; height:8px; border-radius:50%; background:#86efac; margin-left:auto; }}

/* 채팅창 */
.chat {{
  flex:1; overflow-y:auto;
  padding:12px 12px 8px;
  display:flex; flex-direction:column; gap:8px;
}}
.m {{ display:flex; gap:6px; align-items:flex-end; }}
.m.u {{ flex-direction:row-reverse; }}
.m-icon {{
  width:26px; height:26px; border-radius:50%;
  background:#fff3ec; border:1px solid #f5d0b0;
  display:flex; align-items:center; justify-content:center;
  font-size:13px; flex-shrink:0;
}}
.bub {{
  max-width:78%; padding:8px 12px; border-radius:14px;
  font-size:12px; line-height:1.55; word-break:keep-all;
}}
.bub.b {{ background:#fff3ec; border:1px solid #f5d0b0; color:#7c3a10; border-bottom-left-radius:3px; }}
.bub.u {{ background:#EA580C; color:#fff; border-bottom-right-radius:3px; }}

/* FAQ 영역 */
.faq-area {{
  flex-shrink:0;
  background:#fff8f2;
  border-top:1px solid #f0ddd0;
  padding:8px 12px 6px;
}}
.faq-lbl {{
  font-size:10px; color:#b07050; font-weight:700;
  letter-spacing:0.05em; margin-bottom:6px;
}}
.faq-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:5px; }}
.faq-btn {{
  background:#fff; border:1.5px solid #f0c8a0;
  border-radius:20px; padding:7px 6px;
  font-size:11px; color:#9a4a10; cursor:pointer;
  text-align:center; font-family:'Noto Sans KR',sans-serif;
  transition:background 0.15s, border-color 0.15s;
}}
.faq-btn:hover {{ background:#fff3ec; border-color:#EA580C; color:#EA580C; }}

/* 취향 설정 토글 */
.pref-toggle {{
  flex-shrink:0;
  background:#fff8f2;
  border-top:1px solid #f0ddd0;
  padding:6px 12px;
}}
.pref-header {{
  font-size:11px; color:#9a4a10; cursor:pointer;
  display:flex; align-items:center; gap:4px;
  user-select:none;
}}
.pref-header:hover {{ color:#EA580C; }}
.pref-body {{
  display:none; padding:8px 0 4px;
}}
.pref-body.open {{ display:block; }}
.pref-row {{
  display:flex; align-items:center; gap:8px;
  margin-bottom:6px; font-size:11px; color:#7c3a10;
}}
.pref-row label {{ min-width:70px; font-weight:500; }}
.pref-row select, .pref-row input {{
  flex:1; border:1px solid #f0d0b0; border-radius:8px;
  padding:4px 8px; font-size:11px; background:#fff;
  font-family:'Noto Sans KR',sans-serif; color:#333;
  outline:none;
}}
.pref-row select:focus, .pref-row input:focus {{ border-color:#EA580C; }}

/* 입력창 */
.inp-area {{
  flex-shrink:0;
  display:flex; align-items:center; gap:6px;
  padding:8px 12px 12px;
  background:#fff8f2;
  border-top:1px solid #f0ddd0;
}}
.inp-area input {{
  flex:1; border:1.5px solid #f0d0b0; border-radius:22px;
  padding:9px 14px; font-size:12px; background:#fff;
  outline:none; font-family:'Noto Sans KR',sans-serif; color:#333;
}}
.inp-area input:focus {{ border-color:#EA580C; }}
.send-btn {{
  width:34px; height:34px; border-radius:50%;
  background:#EA580C; border:none; cursor:pointer;
  display:flex; align-items:center; justify-content:center; flex-shrink:0;
}}
.send-btn svg {{ width:13px; height:13px; fill:#fff; }}
.send-btn:hover {{ background:#c2490a; }}

/* 냉장고 문 */
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
.door-r {{ --ox:100%; border-radius:0 24px 24px 0; border-left:1.5px solid #b0aaa4; transform:{right_t}; }}
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

      <!-- FAQ 버튼 -->
      <div class="faq-area">
        <div class="faq-lbl">✨ 자주 찾는 기능</div>
        <div class="faq-grid">
          <button class="faq-btn" onclick="sendToStreamlit('냉장고에 있는 재료로 뭐 만들 수 있어?')">🥕 재료로 레시피 찾기</button>
          <button class="faq-btn" onclick="sendToStreamlit('오늘 간단하게 만들어 먹을 메뉴 추천해줘')">📅 오늘 뭐 먹지?</button>
          <button class="faq-btn" onclick="sendToStreamlit('냉장고 재료 최대한 소진할 수 있는 레시피 알려줘')">🔥 재료 소진 플랜</button>
          <button class="faq-btn" onclick="sendToStreamlit('저칼로리 다이어트 레시피 추천해줘')">💪 다이어트 레시피</button>
        </div>
      </div>

      <!-- 취향 설정 -->
      <div class="pref-toggle">
        <div class="pref-header" onclick="togglePref()">
          <span id="prefArrow">▶</span> ⚙️ 취향 설정 (알레르기 / 난이도 / 시간)
        </div>
        <div class="pref-body" id="prefBody">
          <div class="pref-row">
            <label>알레르기</label>
            <input type="text" id="allergyInput" value="{html_module.escape(st.session_state.allergies)}" placeholder="예: 땅콩, 갑각류" />
          </div>
          <div class="pref-row">
            <label>난이도</label>
            <select id="diffInput">
              <option {'selected' if st.session_state.difficulty=='초보' else ''}>초보</option>
              <option {'selected' if st.session_state.difficulty=='보통' else ''}>보통</option>
              <option {'selected' if st.session_state.difficulty=='고수' else ''}>고수</option>
            </select>
          </div>
          <div class="pref-row">
            <label>조리 시간</label>
            <select id="timeInput">
              <option {'selected' if st.session_state.cooking_time=='15분' else ''}>15분</option>
              <option {'selected' if st.session_state.cooking_time=='20분' else ''}>20분</option>
              <option {'selected' if st.session_state.cooking_time=='30분' else ''}>30분</option>
              <option {'selected' if st.session_state.cooking_time=='45분' else ''}>45분</option>
              <option {'selected' if st.session_state.cooking_time=='60분' else ''}>60분</option>
            </select>
          </div>
        </div>
      </div>

      <!-- 입력창 -->
      <div class="inp-area">
        <input
          type="text" id="msgInput"
          placeholder="재료를 입력하세요... (예: 계란, 양파, 두부)"
          onkeydown="if(event.key==='Enter') sendMsg()"
          autocomplete="off"
        />
        <button class="send-btn" onclick="sendMsg()">
          <svg viewBox="0 0 24 24"><path d="M2 21l21-9L2 3v7l15 2-15 2z"/></svg>
        </button>
      </div>
    </div>

    <!-- 냉장고 문 -->
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
  // 채팅창 스크롤 최하단
  var cb = document.getElementById('chatBody');
  if (cb) cb.scrollTop = cb.scrollHeight;

  // 입력 포커스
  window.addEventListener('load', function() {{
    setTimeout(function() {{
      var inp = document.getElementById('msgInput');
      if (inp) inp.focus();
    }}, 1200);
  }});

  // 취향 설정 토글
  function togglePref() {{
    var body = document.getElementById('prefBody');
    var arrow = document.getElementById('prefArrow');
    if (body.classList.contains('open')) {{
      body.classList.remove('open');
      arrow.textContent = '▶';
    }} else {{
      body.classList.add('open');
      arrow.textContent = '▼';
    }}
  }}

  // iframe → Streamlit 부모 페이지로 메시지 전달
  function sendToStreamlit(text) {{
    // 사용자 말풍선을 즉시 추가 (시각적 피드백)
    addMsg('user', text);
    addMsg('bot', '🍳 레시피를 찾고 있어요...');
    
    // Streamlit에 메시지 전달 (URL 쿼리 파라미터 방식)
    var prefs = getPrefs();
    var url = window.parent.location.origin + window.parent.location.pathname 
              + '?q=' + encodeURIComponent(text)
              + '&allergy=' + encodeURIComponent(prefs.allergies)
              + '&diff=' + encodeURIComponent(prefs.difficulty)
              + '&time=' + encodeURIComponent(prefs.cooking_time);
    window.parent.location.href = url;
  }}

  function sendMsg() {{
    var inp = document.getElementById('msgInput');
    var val = inp.value.trim();
    if (!val) return;
    inp.value = '';
    sendToStreamlit(val);
  }}

  function addMsg(role, text) {{
    var cb = document.getElementById('chatBody');
    var div = document.createElement('div');
    div.className = 'm' + (role === 'user' ? ' u' : '');
    if (role === 'bot') {{
      div.innerHTML = '<div class="m-icon">🤖</div><div class="bub b">' + text + '</div>';
    }} else {{
      div.innerHTML = '<div class="bub u">' + text + '</div><div class="m-icon">🙋</div>';
    }}
    cb.appendChild(div);
    cb.scrollTop = cb.scrollHeight;
  }}

  function getPrefs() {{
    return {{
      allergies: document.getElementById('allergyInput').value || '없음',
      difficulty: document.getElementById('diffInput').value || '초보',
      cooking_time: document.getElementById('timeInput').value || '20분'
    }};
  }}
</script>
</body>
</html>
"""


# ── 냉장고 렌더링 ──
components.html(fridge_html, height=740, scrolling=False)

# ── 열기/닫기 버튼 ──
col1, col2, col3 = st.columns([2, 2, 2])
with col2:
    label = "🚪 닫기" if is_open else "🧊 냉털 AI 시작하기"
    if st.button(label, key="toggle_fridge"):
        st.session_state.fridge_open = not st.session_state.fridge_open
        st.rerun()