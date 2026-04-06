import streamlit as st
import streamlit.components.v1 as components
import sys
import os
import html as html_module

# 프로젝트 루트를 sys.path에 추가 (백엔드 에이전트 로드용)
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

# ── 전역 스타일 (Streamlit 기본 UI 숨김 및 모바일 프레임) ──
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

/* 하단 Streamlit 열기/닫기 버튼 스타일 */
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

# ── 1. 세션 상태 초기화 ──
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "bot", "text": "안녕하세요! 🧅 냉장고 속 재료를 알려주시면 딱 맞는 레시피를 찾아드릴게요!"},
        {"role": "bot", "text": "냉장고 문을 열고 재료를 직접 입력해보세요 👇"},
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
if "saved_sauces" not in st.session_state:
    st.session_state.saved_sauces = []

# ── 2. 헬퍼 함수 (RAG 에이전트 연동용) ──
def get_user_preferences() -> dict:
    sauce_info = ", ".join(st.session_state.saved_sauces) if st.session_state.saved_sauces else "없음"
    return {
        "allergies": st.session_state.allergies,
        "difficulty": st.session_state.difficulty,
        "cooking_time": st.session_state.cooking_time,
        "saved_sauces": sauce_info  # 백엔드에 저장된 소스 정보 전달
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
        answer = agent.run(question=question, preferences=preferences, chat_history=chat_history)
    except Exception as e:
        answer = f"죄송합니다, 오류가 발생했어요 😢\n({e})"
    return answer

def process_user_message(user_text: str):
    st.session_state.messages.append({"role": "user", "text": user_text})
    st.session_state.pending_question = user_text

# ── 3. URL 쿼리 파라미터 처리 (JS -> Streamlit 통신 동기화) ──
query_params = st.query_params
should_rerun = False

if "action" in query_params:
    # URL 쿼리를 통한 동기화 (Fallback)
    if query_params["action"] == "sync_open":
        st.session_state.fridge_open = True
        st.session_state.just_opened = True # 애니메이션 동시 적용
    query_params.clear()
    should_rerun = True

elif "sauces" in query_params:
    if query_params["sauces"] == "none":
        st.session_state.saved_sauces = []
        st.session_state.messages.append({"role": "bot", "text": "선택된 소스가 없어요 😅\n소스를 선택해주세요!"})
    else:
        st.session_state.saved_sauces = query_params["sauces"].split(',')
        sauce_msg = f"소스 저장 완료! 🎉\n저장된 소스: {', '.join(st.session_state.saved_sauces)}"
        st.session_state.messages.append({"role": "bot", "text": sauce_msg})
    
    st.session_state.fridge_open = True
    st.session_state.just_opened = False
    query_params.clear()
    should_rerun = True

elif "q" in query_params:
    user_q = query_params["q"]
    if "allergy" in query_params: st.session_state.allergies = query_params["allergy"]
    if "diff" in query_params: st.session_state.difficulty = query_params["diff"]
    if "time" in query_params: st.session_state.cooking_time = query_params["time"]
    
    st.session_state.fridge_open = True
    st.session_state.just_opened = False
    query_params.clear()
    process_user_message(user_q)
    should_rerun = True

if should_rerun:
    st.rerun()

# ── 4. 질문(Agent) 처리 ──
if st.session_state.pending_question:
    question = st.session_state.pending_question
    st.session_state.pending_question = None
    with st.spinner("🍳 레시피를 찾고 있어요..."):
        bot_reply = ask_agent(question)
    st.session_state.messages.append({"role": "bot", "text": bot_reply})


# ── 5. HTML 렌더링 준비 (애니메이션 통합 로직) ──
is_open = st.session_state.fridge_open
just_opened = st.session_state.get("just_opened", False)

# [핵심] 버튼 클릭이든, 냉장고 클릭이든 조건 없이 '부드럽게 열리는 애니메이션' 스크립트 렌더링
if just_opened:
    left_t  = "perspective(900px) rotateY(0deg)"
    right_t = "perspective(900px) rotateY(0deg)"
    inner_opacity = "0"
    inner_pointer = "none"
    door_pointer  = "none"
    
    auto_open_script = """
    setTimeout(function() {
        document.getElementById('doorL').style.transform = 'perspective(900px) rotateY(-122deg)';
        document.getElementById('doorR').style.transform = 'perspective(900px) rotateY(122deg)';
        setTimeout(function() {
            var inner = document.getElementById('chatInner');
            inner.style.opacity = '1';
            inner.style.pointerEvents = 'auto';
            var inp = document.getElementById('msgInput');
            if (inp) inp.focus();
        }, 900);
    }, 100);
    """
    st.session_state.just_opened = False  # 1회용 플래그 리셋
else:
    left_t  = "perspective(900px) rotateY(-122deg)" if is_open else "perspective(900px) rotateY(0deg)"
    right_t = "perspective(900px) rotateY(122deg)"  if is_open else "perspective(900px) rotateY(0deg)"
    inner_opacity = "1" if is_open else "0"
    inner_pointer = "auto" if is_open else "none"
    door_pointer  = "none" if is_open else "auto"
    auto_open_script = ""

# 말풍선 생성
msgs_html = ""
for m in st.session_state.messages:
    safe_text = html_module.escape(m["text"]).replace("\n", "<br>")
    if m["role"] == "bot":
        msgs_html += f'<div class="m"><div class="m-icon">🤖</div><div class="bub b">{safe_text}</div></div>'
    else:
        msgs_html += f'<div class="m u"><div class="bub u">{safe_text}</div><div class="m-icon">🙋</div></div>'

# 소스 카테고리 구성
sauce_list = [
    ("기본 양념 및 소스", ["진간장", "국간장", "고추장", "된장", "쌈장", "굴소스", "식초", "사과식초", "발사믹식초", "맛술", "미림", "케첩", "마요네즈", "설탕", "소금", "후추", "고춧가루", "다진 마늘", "액젓 (멸치액젓)", "액젓 (까나리액젓)", "올리고당 / 물엿"]),
    ("기름류", ["식용유", "올리브오일", "참기름", "들기름", "버터", "고추기름", "아보카도유", "트러플 오일", "라드"]),
    ("트렌디 & 에스닉 소스", ["스리라차", "두반장", "타바스코", "쯔유", "피시소스", "바질 페스토", "홀그레인 머스터드", "우스터소스", "XO소스", "머스타드"]),
    ("편의형 만능 소스", ["불닭 소스", "참치액", "연두", "치킨스톡", "돈가스 소스", "데리야끼 소스", "스테이크 소스", "청주"]),
    ("드레싱 및 기타", ["오리엔탈 드레싱", "참깨 드레싱", "허니 머스터드", "파마산 치즈 가루", "와사비 (고추냉이)"]),
]

saved = st.session_state.saved_sauces
sauce_html_items = ""
for category, items in sauce_list:
    sauce_html_items += f'<div class="cat-label">{category}</div><div class="check-grid">'
    for item in items:
        checked = "checked" if item in saved else ""
        sauce_html_items += f'<label class="check-item"><input type="checkbox" value="{item}" {checked}><span>{item}</span></label>'
    sauce_html_items += '</div>'

# ── 6. 냉장고 전체 HTML/CSS/JS 프레임 ──
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
  position:relative; width:420px; height:720px; background:#e2ddd8;
  border-radius:26px; border:3px solid #c8c2bc; overflow:hidden; cursor:pointer;
}}

.inner {{
  position:absolute; inset:0; background:#fffaf5; border-radius:24px;
  display:flex; flex-direction:column; overflow:hidden;
  opacity:{inner_opacity}; transition:opacity 0.5s ease 1s; pointer-events:{inner_pointer};
}}

.hdr {{ background:#EA580C; padding:12px 16px; display:flex; align-items:center; gap:10px; flex-shrink:0; }}
.hdr-av {{ width:36px; height:36px; border-radius:50%; background:#fff3ec; display:flex; align-items:center; justify-content:center; font-size:20px; }}
.hdr-title {{ color:#fff; font-size:14px; font-weight:700; }}
.hdr-sub   {{ color:#ffd4b8; font-size:10px; margin-top:1px; }}

.chat {{ flex:1; overflow-y:auto; padding:12px 12px 8px; display:flex; flex-direction:column; gap:8px; }}
.m {{ display:flex; gap:6px; align-items:flex-end; }}
.m.u {{ flex-direction:row-reverse; }}
.m-icon {{ width:26px; height:26px; border-radius:50%; background:#fff3ec; border:1px solid #f5d0b0; display:flex; align-items:center; justify-content:center; font-size:13px; flex-shrink:0; }}
.bub {{ max-width:78%; padding:8px 12px; border-radius:14px; font-size:12px; line-height:1.55; word-break:keep-all; }}
.bub.b {{ background:#fff3ec; border:1px solid #f5d0b0; color:#7c3a10; border-bottom-left-radius:3px; }}
.bub.u {{ background:#EA580C; color:#fff; border-bottom-right-radius:3px; }}

.bottom-area {{ flex-shrink:0; background:#fff8f2; border-top:1px solid #f0ddd0; padding:8px 12px 6px; }}
.faq-lbl {{ font-size:10px; color:#b07050; font-weight:700; letter-spacing:0.05em; margin-bottom:6px; }}
.faq-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:5px; margin-bottom:8px; }}
.faq-btn {{ background:#fff; border:1.5px solid #f0c8a0; border-radius:20px; padding:7px 6px; font-size:11px; color:#9a4a10; cursor:pointer; text-align:center; font-family:'Noto Sans KR',sans-serif; transition:background 0.15s, border-color 0.15s; }}
.faq-btn:hover {{ background:#fff3ec; border-color:#EA580C; color:#EA580C; }}

.pref-header {{ font-size:11px; color:#9a4a10; cursor:pointer; display:flex; align-items:center; gap:4px; user-select:none; margin-bottom:6px; }}
.pref-header:hover {{ color:#EA580C; }}
.pref-body {{ display:none; padding-bottom:6px; }}
.pref-body.open {{ display:block; }}
.pref-row {{ display:flex; align-items:center; gap:8px; margin-bottom:6px; font-size:11px; color:#7c3a10; }}
.pref-row label {{ min-width:70px; font-weight:500; }}
.pref-row select, .pref-row input {{ flex:1; border:1px solid #f0d0b0; border-radius:8px; padding:4px 8px; font-size:11px; background:#fff; font-family:'Noto Sans KR',sans-serif; color:#333; outline:none; }}

.action-btn {{ width:100%; background:#fff; border:1.5px solid #EA580C; border-radius:18px; padding:6px; font-size:11.5px; color:#EA580C; cursor:pointer; font-weight:700; transition:background 0.15s; }}
.action-btn:hover {{ background:#fff3ec; }}

.inp-area {{ display:flex; align-items:center; gap:6px; padding:6px 12px 12px; background:#fff8f2; }}
.inp-area input {{ flex:1; border:1.5px solid #f0d0b0; border-radius:22px; padding:9px 14px; font-size:12px; background:#fff; outline:none; font-family:'Noto Sans KR',sans-serif; color:#333; }}
.inp-area input:focus {{ border-color:#EA580C; }}
.send-btn {{ width:34px; height:34px; border-radius:50%; background:#EA580C; border:none; cursor:pointer; display:flex; align-items:center; justify-content:center; flex-shrink:0; }}
.send-btn svg {{ width:13px; height:13px; fill:#fff; }}

.sauce-page {{ position:absolute; inset:0; background:#fffaf5; border-radius:24px; display:flex; flex-direction:column; opacity:0; pointer-events:none; transition:opacity 0.3s ease; z-index:20; }}
.sauce-page.active {{ opacity:1; pointer-events:auto; }}
.sauce-hdr {{ background:#EA580C; padding:12px 16px; display:flex; align-items:center; color:#fff; font-weight:700; font-size:14px; }}
.sauce-close {{ margin-left:auto; background:rgba(255,255,255,0.2); border:none; border-radius:50%; width:28px; height:28px; color:#fff; cursor:pointer; }}
.sauce-body {{ flex:1; overflow-y:auto; padding:14px; }}
.cat-label {{ font-size:11px; font-weight:700; color:#EA580C; margin:6px 0 4px; }}
.check-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:6px; margin-bottom:10px; }}
.check-item {{ display:flex; align-items:center; gap:6px; background:#fff3ec; border:1px solid #f5d0b0; border-radius:10px; padding:7px 10px; font-size:11px; color:#7c3a10; cursor:pointer; }}
.check-item input {{ accent-color:#EA580C; }}
.sauce-save-btn {{ margin:10px 14px 14px; background:#EA580C; color:#fff; border:none; border-radius:22px; padding:10px; font-size:12px; font-weight:700; cursor:pointer; }}

.doors {{ position:absolute; inset:0; display:flex; pointer-events:{door_pointer}; }}
.door {{ width:50%; height:100%; background:linear-gradient(160deg,#dedad4 0%,#ccc8c2 100%); border:2.5px solid #b8b2ac; display:flex; align-items:center; justify-content:center; flex-direction:column; gap:10px; transition:transform 1.3s cubic-bezier(0.4,0,0.2,1); position:relative; }}
.door-l {{ transform-origin:0% center; border-radius:24px 0 0 24px; border-right:1.5px solid #b0aaa4; transform:{left_t}; }}
.door-r {{ transform-origin:100% center; border-radius:0 24px 24px 24px; border-left:1.5px solid #b0aaa4; transform:{right_t}; }}
.d-handle {{ width:6px; height:64px; background:#9a9490; border-radius:3px; position:absolute; }}
.door-l .d-handle {{ right:14px; }}
.door-r .d-handle {{ left:14px; }}
.door-logo {{ font-size:36px; opacity:0.45; }}
.door-hint {{ font-size:11px; color:#999; letter-spacing:0.05em; opacity:0.8; }}
.fridge-top {{ position:absolute; top:10px; left:50%; transform:translateX(-50%); width:70px; height:7px; background:#c8c2bc; border-radius:4px; z-index:10; }}
</style>
</head>
<body>
<div class="scene">
  <div class="fridge" id="fridge" onclick="handleFridgeClick()">
    <div class="fridge-top"></div>

    <div class="inner" id="chatInner">
      <div class="hdr">
        <div class="hdr-av">🍳</div>
        <div>
          <div class="hdr-title">냉털봇</div>
          <div class="hdr-sub">재료 소진 레시피 AI</div>
        </div>
      </div>

      <div class="chat" id="chatBody">
        {msgs_html}
      </div>

      <div class="bottom-area">
        <div class="faq-lbl">✨ 자주 찾는 기능</div>
        <div class="faq-grid">
          <button class="faq-btn" onclick="sendFaq('🥕 재료로 레시피 찾기','냉장고에 어떤 재료가 있는지 알려주세요!')">🥕 재료로 레시피 찾기</button>
          <button class="faq-btn" onclick="sendFaq('📅 오늘 뭐 먹지?','오늘 드실 메뉴를 추천해드릴게요!')">📅 오늘 뭐 먹지?</button>
          <button class="faq-btn" onclick="sendFaq('🔥 재료 소진 플랜','재료를 효율적으로 소진하는 플랜을 짜드릴게요!')">🔥 재료 소진 플랜</button>
          <button class="faq-btn" onclick="sendFaq('💪 다이어트 레시피','저칼로리 레시피를 추천해드릴게요!')">💪 다이어트 레시피</button>
        </div>

        <div class="pref-header" onclick="togglePref()">
          <span id="prefArrow">▶</span> ⚙️ 취향 설정 (알레르기 / 난이도 / 시간)
        </div>
        <div class="pref-body" id="prefBody">
          <div class="pref-row">
            <label>알레르기</label>
            <input type="text" id="allergyInput" value="{html_module.escape(st.session_state.allergies)}" placeholder="예: 땅콩" />
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
              <option {'selected' if st.session_state.cooking_time=='60분' else ''}>60분</option>
            </select>
          </div>
        </div>

        <button class="action-btn" onclick="openSaucePage()">🧴 소스 및 양념 저장하기</button>
      </div>

      <div class="inp-area">
        <input type="text" id="msgInput" placeholder="재료를 입력하세요... (예: 계란, 양파)" onkeydown="if(event.key==='Enter') sendMsg()" autocomplete="off"/>
        <button class="send-btn" onclick="sendMsg()"><svg viewBox="0 0 24 24"><path d="M2 21l21-9L2 3v7l15 2-15 2z"/></svg></button>
      </div>
    </div>

    <div class="sauce-page" id="saucePage">
      <div class="sauce-hdr">
        <div>🧴 내 소스 저장하기</div>
        <button class="sauce-close" onclick="closeSaucePage()">✕</button>
      </div>
      <div class="sauce-body">
        <p style="font-size:10.5px;color:#b07050;margin-bottom:8px;">보유하신 소스를 체크해두면 AI가 참고합니다!</p>
        {sauce_html_items}
      </div>
      <button class="sauce-save-btn" onclick="saveSauces()">✅ 선택 완료 및 저장</button>
    </div>

    <div class="doors" id="doors">
      <div class="door door-l" id="doorL"><div class="d-handle"></div><div class="door-logo">🧊</div><div class="door-hint">탭하여 시작</div></div>
      <div class="door door-r" id="doorR"><div class="d-handle"></div><div class="door-logo">🍳</div><div class="door-hint">탭하여 시작</div></div>
    </div>
  </div>
</div>

<script>
  var isOpen = {'true' if is_open else 'false'};

  var cb = document.getElementById('chatBody');
  if (cb) cb.scrollTop = cb.scrollHeight;

  if (isOpen) {{
    setTimeout(function() {{ var inp = document.getElementById('msgInput'); if (inp) inp.focus(); }}, 300);
  }}

  // 하단 버튼이나 냉장고 클릭 시 동일하게 작동하는 열림 스크립트
  {auto_open_script}

  // [핵심 해결] 냉장고 문을 클릭했을 때 자바스크립트가 직접 파이썬 버튼을 클릭하게 만듭니다.
  function handleFridgeClick() {{
    if (!isOpen) {{
        isOpen = true; // 중복 클릭 방지
        
        try {{
            // Streamlit 부모 창에 있는 [🧊 냉털 AI 시작하기] 버튼을 직접 찾아 클릭합니다.
            // 이렇게 하면 하단 버튼을 누른 것과 100% 동일하게 파이썬 로직이 돌아가며 문 닫기 버튼이 렌더링됩니다.
            var btns = window.parent.document.querySelectorAll('button');
            for (var i = 0; i < btns.length; i++) {{
                if (btns[i].innerText.includes('냉털 AI 시작하기')) {{
                    btns[i].click();
                    return; // 정상 클릭 시 여기서 종료 (이후 Streamlit이 화면을 갱신하며 애니메이션 재생)
                }}
            }}
        }} catch(e) {{
            console.warn("Parent access restricted. Fallback to URL.");
        }}

        // 버튼 클릭에 실패했을 때만 작동하는 대체 로직 (URL 파라미터)
        var url = window.parent.location.origin + window.parent.location.pathname + '?action=sync_open';
        window.parent.location.href = url;
    }}
  }}

  function togglePref() {{
    event.stopPropagation();
    var body = document.getElementById('prefBody');
    var arrow = document.getElementById('prefArrow');
    if (body.classList.contains('open')) {{ body.classList.remove('open'); arrow.textContent = '▶'; }} 
    else {{ body.classList.add('open'); arrow.textContent = '▼'; }}
  }}

  function openSaucePage() {{
    event.stopPropagation();
    document.getElementById('saucePage').classList.add('active');
  }}
  function closeSaucePage() {{
    event.stopPropagation();
    document.getElementById('saucePage').classList.remove('active');
  }}

  function saveSauces() {{
    event.stopPropagation();
    var checked = [];
    document.querySelectorAll('.sauce-body input[type=checkbox]:checked').forEach(function(el) {{ checked.push(el.value); }});
    
    var urlStr = checked.length > 0 ? encodeURIComponent(checked.join(',')) : 'none';
    var url = window.parent.location.origin + window.parent.location.pathname + '?sauces=' + urlStr;
    window.parent.location.href = url;
  }}

  function sendToStreamlit(text) {{
    addMsg('user', text);
    addMsg('bot', '🍳 레시피를 찾고 있어요...');
    var prefs = getPrefs();
    var url = window.parent.location.origin + window.parent.location.pathname 
              + '?q=' + encodeURIComponent(text)
              + '&allergy=' + encodeURIComponent(prefs.allergies)
              + '&diff=' + encodeURIComponent(prefs.difficulty)
              + '&time=' + encodeURIComponent(prefs.cooking_time);
    window.parent.location.href = url;
  }}

  function sendMsg() {{
    event.stopPropagation();
    var inp = document.getElementById('msgInput');
    var val = inp.value.trim();
    if (!val) return;
    inp.value = '';
    sendToStreamlit(val);
  }}

  function sendFaq(label, reply) {{
    event.stopPropagation();
    sendToStreamlit(label);
  }}

  function addMsg(role, text) {{
    var div = document.createElement('div');
    div.className = 'm' + (role === 'user' ? ' u' : '');
    if (role === 'bot') {{ div.innerHTML = '<div class="m-icon">🤖</div><div class="bub b">' + text + '</div>'; }} 
    else {{ div.innerHTML = '<div class="bub u">' + text + '</div><div class="m-icon">🙋</div>'; }}
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

# ── 7. 프론트엔드 렌더링 ──
components.html(fridge_html, height=750, scrolling=False)

# ── 8. 외부 Streamlit 버튼 (닫기/열기 동기화) ──
col1, col2, col3 = st.columns([1.5, 2.5, 1.5])
with col2:
    if not st.session_state.fridge_open:
        # 문이 닫혀있을 때만 이 버튼이 렌더링 됩니다. 
        # 사용자가 문을 클릭하면 자바스크립트가 알아서 이 버튼을 클릭해 줍니다.
        if st.button("🧊 냉털 AI 시작하기", use_container_width=True):
            st.session_state.fridge_open = True
            st.session_state.just_opened = True 
            st.rerun()
    else:
        # 문이 열려있으면 '닫기' 버튼으로 변경
        if st.button("🚪 냉장고 닫기", use_container_width=True):
            st.session_state.fridge_open = False
            st.session_state.just_opened = False
            st.rerun()