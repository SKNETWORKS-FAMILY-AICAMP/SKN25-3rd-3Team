import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="냉털봇",
    page_icon="🧊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

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

# ── 세션 상태 ──
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "bot", "text": "안녕하세요! 🧅 냉장고 속 재료를 알려주시면 딱 맞는 레시피를 찾아드릴게요!"},
        {"role": "bot", "text": "아래 버튼을 눌러 시작하거나 재료를 직접 입력해보세요 👇"},
    ]
if "fridge_open" not in st.session_state:
    st.session_state.fridge_open = False

is_open = st.session_state.fridge_open

# 말풍선 HTML
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

left_t  = "perspective(900px) rotateY(-122deg)" if is_open else "perspective(900px) rotateY(0deg)"
right_t = "perspective(900px) rotateY(122deg)"  if is_open else "perspective(900px) rotateY(0deg)"
inner_opacity = "1" if is_open else "0"
inner_pointer = "auto" if is_open else "none"
door_pointer  = "none" if is_open else "auto"

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

/* 입력창 */
.inp-area {{
  flex-shrink:0;
  display:flex; align-items:center; gap:8px;
  padding:10px 14px;
  background:#fff8f2;
  border-top:1px solid #f0ddd0;
}}
.inp-area input {{
  flex:1; border:1.5px solid #f0d0b0; border-radius:22px;
  padding:9px 16px; font-size:12.5px; background:#fff;
  outline:none; font-family:'Noto Sans KR',sans-serif; color:#333;
}}
.inp-area input:focus {{ border-color:#EA580C; }}
.send-btn {{
  width:36px; height:36px; border-radius:50%;
  background:#EA580C; border:none; cursor:pointer;
  display:flex; align-items:center; justify-content:center; flex-shrink:0;
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
  font-size:12px; color:#9a4a10; cursor:pointer;
  text-align:center;
  font-family:'Noto Sans KR',sans-serif;
  transition:background 0.15s, border-color 0.15s, color 0.15s;
}}
.faq-btn:hover {{ background:#fff3ec; border-color:#EA580C; color:#EA580C; }}

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

      <!-- 입력창 -->
      <div class="inp-area">
        <input
          type="text"
          id="msgInput"
          placeholder="재료를 입력하세요... (예: 계란, 양파)"
          onkeydown="if(event.key==='Enter') sendMsg()"
          autocomplete="off"
        />
        <button class="send-btn" onclick="sendMsg()">
          <svg viewBox="0 0 24 24"><path d="M2 21l21-9L2 3v7l15 2-15 2z"/></svg>
        </button>
      </div>

      <!-- FAQ 버튼 -->
      <div class="faq-area">
        <div class="faq-lbl">✨ 자주 찾는 기능</div>
        <div class="faq-grid">
          <button class="faq-btn" onclick="sendFaq('🥕 재료로 레시피 찾기', '냉장고에 어떤 재료가 있는지 알려주세요!')">🥕 재료로 레시피 찾기</button>
          <button class="faq-btn" onclick="sendFaq('📅 오늘 뭐 먹지?', '오늘 드실 메뉴를 추천해드릴게요!')">📅 오늘 뭐 먹지?</button>
          <button class="faq-btn" onclick="sendFaq('🔥 재료 소진 플랜', '재료를 효율적으로 소진하는 플랜을 짜드릴게요!')">🔥 재료 소진 플랜</button>
          <button class="faq-btn" onclick="sendFaq('💪 다이어트 레시피', '저칼로리 레시피를 추천해드릴게요!')">💪 다이어트 레시피</button>
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

  // 입력창 포커스 (iframe 안에서 클릭 없이도 바로 입력 가능하게)
  window.addEventListener('load', function() {{
    setTimeout(function() {{
      var inp = document.getElementById('msgInput');
      if (inp) inp.focus();
    }}, 1200);
  }});

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

  function sendMsg() {{
    var inp = document.getElementById('msgInput');
    var val = inp.value.trim();
    if (!val) return;
    addMsg('user', val);
    inp.value = '';
    inp.focus();
    setTimeout(function() {{
      addMsg('bot', '재료 확인했어요! 🎉<br>\\'' + val + '\\' 기반으로 레시피 찾아볼게요~');
    }}, 500);
  }}

  function sendFaq(label, reply) {{
    addMsg('user', label);
    setTimeout(function() {{
      addMsg('bot', reply);
    }}, 400);
  }}
</script>
</body>
</html>
"""

# ── 렌더링 ──
components.html(fridge_html, height=700, scrolling=False)

# ── 열기/닫기 버튼만 밖에 ──
col1, col2, col3 = st.columns([2, 2, 2])
with col2:
    label = "🚪 닫기" if is_open else "🧊 냉털 AI 시작하기"
    if st.button(label):
        st.session_state.fridge_open = not st.session_state.fridge_open
        st.rerun()
