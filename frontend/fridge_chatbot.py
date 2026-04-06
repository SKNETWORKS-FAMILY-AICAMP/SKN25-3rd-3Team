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

/* 버튼 공통 스타일 */
.stButton > button {
    border: 1.5px solid #EA580C !important;
    color: #EA580C !important;
    border-radius: 20px !important;
    background: transparent !important;
    font-size: 13px !important;
    padding: 7px 22px !important;
    white-space: nowrap !important;
    line-height: 1.4 !important;
}
.stButton > button:hover {
    background: #EA580C !important;
    color: #fff !important;
}
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
if "saved_sauces" not in st.session_state:
    st.session_state.saved_sauces = []

is_open = st.session_state.fridge_open

# 말풍선 HTML 생성
msgs_html = ""
for m in st.session_state.messages:
    text = m["text"].replace("\n", "<br>")
    if m["role"] == "bot":
        msgs_html += f'<div class="m"><div class="m-icon">🤖</div><div class="bub b">{text}</div></div>'
    else:
        msgs_html += f'<div class="m u"><div class="bub u">{text}</div><div class="m-icon">🙋</div></div>'

# 문 애니메이션 transform
left_t  = "perspective(900px) rotateY(-122deg)" if is_open else "perspective(900px) rotateY(0deg)"
right_t = "perspective(900px) rotateY(122deg)"  if is_open else "perspective(900px) rotateY(0deg)"
inner_opacity = "1" if is_open else "0"
inner_pointer = "auto" if is_open else "none"
door_pointer  = "none" if is_open else "auto"

# [수정] 소스 목록 — 중복 제거 및 새 항목 추가, 카테고리 재편
sauce_list = [
    ("기본 양념 및 소스", [
        "진간장", "국간장",          # 기존: 양조간장·저염간장 제거, 진간장·국간장 유지
        "고추장",
        "된장",
        "쌈장",
        "굴소스",
        "식초",                       # 기존: 일반식초 통합
        "사과식초",                   # 기존 유지
        "발사믹식초",                 # 기존 유지
        "맛술", "미림",               # 기존 유지
        "케첩",                       # 기존 유지
        "마요네즈",                   # 기존 유지
        "설탕",                       # 기존 유지
        "소금",                       # 기존 유지
        "후추",                       # 기존 유지
        "고춧가루",                   # [신규]
        "다진 마늘",                  # [신규]
        "액젓 (멸치액젓)",            # [신규]
        "액젓 (까나리액젓)",          # [신규]
        "올리고당 / 물엿",            # [신규]
    ]),
    ("기름류", [
        "식용유",                     # 기존 유지
        "올리브오일",                 # 기존 유지
        "참기름",                     # 기존 유지
        "들기름",                     # 기존 유지
        "버터",                       # 기존 유지
        "고추기름",                   # 기존: 고추류→기름류로 이동
        "아보카도유",                 # [신규]
        "트러플 오일",                # [신규]
        "라드",                       # [신규]
    ]),
    ("트렌디 & 에스닉 소스", [
        "스리라차",                   # 기존: 기타→이 카테고리로 이동
        "두반장",                     # 기존: 기타→이 카테고리로 이동
        "타바스코",                   # 기존: 기타→이 카테고리로 이동
        "쯔유",                       # [신규]
        "피시소스",                   # 기존: 소스류→이 카테고리로 이동
        "바질 페스토",                # [신규]
        "홀그레인 머스터드",          # [신규]
        "우스터소스",                 # 기존 유지 (카테고리 이동)
        "XO소스",                     # 기존 유지 (카테고리 이동)
        "머스타드",                   # 기존 유지
    ]),
    ("편의형 만능 소스", [
        "불닭 소스",                  # [신규]
        "참치액",                     # [신규]
        "연두",                       # [신규]
        "치킨스톡",                   # [신규]
        "돈가스 소스",                # [신규]
        "데리야끼 소스",              # [신규]
        "스테이크 소스",              # [신규]
        "청주",                       # 기존 유지 (카테고리 이동)
    ]),
    ("드레싱 및 기타", [
        "오리엔탈 드레싱",            # [신규]
        "참깨 드레싱",                # [신규]
        "허니 머스터드",              # [신규]
        "파마산 치즈 가루",           # [신규]
        "와사비 (고추냉이)",          # [신규]
    ]),
]

saved = st.session_state.saved_sauces
sauce_html_items = ""
for category, items in sauce_list:
    sauce_html_items += f'<div class="cat-label">{category}</div><div class="check-grid">'
    for item in items:
        checked = "checked" if item in saved else ""
        sauce_html_items += f'<label class="check-item"><input type="checkbox" value="{item}" {checked} onchange="toggleSauce(this)"><span>{item}</span></label>'
    sauce_html_items += '</div>'

fridge_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
* {{ box-sizing:border-box; margin:0; padding:0; }}
html, body {{ background:transparent; font-family:'Noto Sans KR',sans-serif; }}

.scene {{ display:flex; flex-direction:column; align-items:center; padding:4px 0; }}

.fridge {{
  position:relative;
  width:420px; height:700px;
  background:#e2ddd8;
  border-radius:26px;
  border:3px solid #c8c2bc;
  overflow:hidden;
  cursor:pointer;
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

.sauce-page {{
  position:absolute; inset:0;
  background:#fffaf5;
  border-radius:24px;
  display:flex; flex-direction:column;
  overflow:hidden;
  opacity:0; pointer-events:none;
  transition:opacity 0.3s ease;
  z-index:10;
}}
.sauce-page.active {{ opacity:1; pointer-events:auto; }}
.sauce-hdr {{
  background:#EA580C; padding:14px 18px;
  display:flex; align-items:center; gap:10px; flex-shrink:0;
}}
.sauce-hdr-title {{ color:#fff; font-size:15px; font-weight:700; flex:1; }}
.sauce-close {{
  background:rgba(255,255,255,0.2); border:none; border-radius:50%;
  width:30px; height:30px; color:#fff; font-size:16px; cursor:pointer;
  display:flex; align-items:center; justify-content:center;
}}
.sauce-body {{ flex:1; overflow-y:auto; padding:14px; display:flex; flex-direction:column; gap:8px; }}
.cat-label {{ font-size:11px; font-weight:700; color:#EA580C; letter-spacing:0.05em; margin:6px 0 4px; }}
.check-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:6px; }}
.check-item {{
  display:flex; align-items:center; gap:6px;
  background:#fff3ec; border:1px solid #f5d0b0;
  border-radius:10px; padding:7px 10px; cursor:pointer;
  font-size:12px; color:#7c3a10; transition:background 0.15s;
}}
.check-item:hover {{ background:#ffe8d6; }}
.check-item input {{ accent-color:#EA580C; width:14px; height:14px; flex-shrink:0; }}
.sauce-save-btn {{
  margin:12px 14px 16px;
  background:#EA580C; color:#fff; border:none;
  border-radius:22px; padding:12px;
  font-size:13px; font-weight:700; cursor:pointer;
  font-family:'Noto Sans KR',sans-serif; flex-shrink:0;
}}
.sauce-save-btn:hover {{ background:#c94d0a; }}

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

.chat {{
  flex:1; overflow-y:auto; padding:14px 14px 10px;
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
.bub {{ max-width:76%; padding:9px 13px; border-radius:16px; font-size:12.5px; line-height:1.6; word-break:keep-all; }}
.bub.b {{ background:#fff3ec; border:1px solid #f5d0b0; color:#7c3a10; border-bottom-left-radius:3px; }}
.bub.u {{ background:#EA580C; color:#fff; border-bottom-right-radius:3px; }}

.inp-area {{
  flex-shrink:0; display:flex; align-items:center; gap:8px;
  padding:10px 14px; background:#fff8f2; border-top:1px solid #f0ddd0;
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

.bottom-area {{
  flex-shrink:0; background:#fff8f2;
  border-top:1px solid #f0ddd0; padding:10px 14px 14px;
}}
.faq-lbl {{ font-size:10px; color:#b07050; font-weight:700; letter-spacing:0.05em; margin-bottom:8px; }}
.faq-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:7px; margin-bottom:10px; }}
.faq-btn {{
  background:#fff; border:1.5px solid #f0c8a0;
  border-radius:22px; padding:9px 8px;
  font-size:12px; color:#9a4a10; cursor:pointer; text-align:center;
  font-family:'Noto Sans KR',sans-serif;
  transition:background 0.15s, border-color 0.15s, color 0.15s;
}}
.faq-btn:hover {{ background:#fff3ec; border-color:#EA580C; color:#EA580C; }}

.action-row {{
  display:flex; align-items:center; justify-content:center;
  gap:10px; margin-top:4px;
}}
.action-btn {{
  background:#fff; border:1.5px solid #EA580C;
  border-radius:18px; padding:7px 16px;
  font-size:12px; color:#EA580C; cursor:pointer;
  font-family:'Noto Sans KR',sans-serif; font-weight:700;
  transition:background 0.15s;
  white-space:nowrap;
}}
.action-btn:hover {{ background:#fff3ec; }}

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
.door-logo {{ font-size:36px; opacity:0.45; }}
.door-hint {{ font-size:11px; color:#999; letter-spacing:0.05em; opacity:0.8; }}
.fridge-top {{
  position:absolute; top:10px; left:50%; transform:translateX(-50%);
  width:70px; height:7px; background:#c8c2bc; border-radius:4px; z-index:10;
}}
</style>
</head>
<body>
<div class="scene">
  <div class="fridge" id="fridge" onclick="handleFridgeClick(event)">
    <div class="fridge-top"></div>

    <!-- ── 챗봇 내부 ── -->
    <div class="inner" id="chatInner">
      <div class="hdr">
        <div class="hdr-av">🍳</div>
        <div>
          <div class="hdr-title">냉털봇</div>
          <div class="hdr-sub">재료 소진 레시피 AI</div>
        </div>
        <div class="hdr-dot"></div>
      </div>
      <div class="chat" id="chatBody">{msgs_html}</div>
      <div class="inp-area">
        <input type="text" id="msgInput"
          placeholder="재료를 입력하세요... (예: 계란, 양파)"
          onkeydown="if(event.key==='Enter') sendMsg()"
          autocomplete="off"/>
        <button class="send-btn" onclick="sendMsg()">
          <svg viewBox="0 0 24 24"><path d="M2 21l21-9L2 3v7l15 2-15 2z"/></svg>
        </button>
      </div>
      <div class="bottom-area">
        <div class="faq-lbl">✨ 자주 찾는 기능</div>
        <div class="faq-grid">
          <button class="faq-btn" onclick="sendFaq('🥕 재료로 레시피 찾기','냉장고에 어떤 재료가 있는지 알려주세요!')">🥕 재료로 레시피 찾기</button>
          <button class="faq-btn" onclick="sendFaq('📅 오늘 뭐 먹지?','오늘 드실 메뉴를 추천해드릴게요!')">📅 오늘 뭐 먹지?</button>
          <button class="faq-btn" onclick="sendFaq('🔥 재료 소진 플랜','재료를 효율적으로 소진하는 플랜을 짜드릴게요!')">🔥 재료 소진 플랜</button>
          <button class="faq-btn" onclick="sendFaq('💪 다이어트 레시피','저칼로리 레시피를 추천해드릴게요!')">💪 다이어트 레시피</button>
        </div>
        <div class="action-row">
          <button class="action-btn" onclick="openSaucePage()">🧴 소스 저장</button>
        </div>
      </div>
    </div>

    <!-- 소스 저장 페이지 -->
    <div class="sauce-page" id="saucePage">
      <div class="sauce-hdr">
        <div class="sauce-hdr-title">🧴 내 소스 저장하기</div>
        <button class="sauce-close" onclick="closeSaucePage()">✕</button>
      </div>
      <div class="sauce-body">
        <p style="font-size:11.5px;color:#b07050;margin-bottom:4px;">보유하고 있는 소스/양념을 선택해주세요!</p>
        {sauce_html_items}
      </div>
      <button class="sauce-save-btn" onclick="saveSauces()">✅ 저장 완료</button>
    </div>

    <!-- ── 냉장고 문 ── -->
    <div class="doors" id="doors">
      <div class="door door-l" id="doorL">
        <div class="d-handle"></div>
        <div class="door-logo">🧊</div>
        <div class="door-hint">탭하여 시작</div>
      </div>
      <div class="door door-r" id="doorR">
        <div class="d-handle"></div>
        <div class="door-logo">🍳</div>
        <div class="door-hint">탭하여 시작</div>
      </div>
    </div>
  </div>
</div>

<script>
  var isOpen = {'true' if is_open else 'false'};

  var cb = document.getElementById('chatBody');
  if (cb) cb.scrollTop = cb.scrollHeight;

  function handleFridgeClick(e) {{
    if (!isOpen) openFridge();
  }}

  function openFridge() {{
    isOpen = true;
    document.getElementById('doorL').style.transform = 'perspective(900px) rotateY(-122deg)';
    document.getElementById('doorR').style.transform = 'perspective(900px) rotateY(122deg)';
    document.getElementById('doors').style.pointerEvents = 'none';
    setTimeout(function() {{
      var inner = document.getElementById('chatInner');
      inner.style.opacity = '1';
      inner.style.pointerEvents = 'auto';
      document.getElementById('msgInput').focus();
    }}, 900);
  }}

  function closeFridge() {{
    event.stopPropagation();
    isOpen = false;
    var inner = document.getElementById('chatInner');
    inner.style.opacity = '0';
    inner.style.pointerEvents = 'none';
    document.getElementById('doorL').style.transform = 'perspective(900px) rotateY(0deg)';
    document.getElementById('doorR').style.transform = 'perspective(900px) rotateY(0deg)';
    setTimeout(function() {{
      document.getElementById('doors').style.pointerEvents = 'auto';
    }}, 1300);
  }}

  function openSaucePage() {{
    event.stopPropagation();
    document.getElementById('saucePage').classList.add('active');
  }}

  function closeSaucePage() {{
    document.getElementById('saucePage').classList.remove('active');
  }}

  function saveSauces() {{
    var checked = [];
    document.querySelectorAll('.sauce-body input[type=checkbox]:checked').forEach(function(el) {{
      checked.push(el.value);
    }});
    var msg = checked.length > 0
      ? '소스 저장 완료! 🎉<br>저장된 소스: ' + checked.join(', ')
      : '선택된 소스가 없어요 😅<br>소스를 선택해주세요!';
    closeSaucePage();
    addMsg('bot', msg);
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

  function sendMsg() {{
    event.stopPropagation();
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
    event.stopPropagation();
    addMsg('user', label);
    setTimeout(function() {{ addMsg('bot', reply); }}, 400);
  }}

  if (isOpen) {{
    setTimeout(function() {{
      var inp = document.getElementById('msgInput');
      if (inp) inp.focus();
    }}, 300);
  }}
</script>
</body>
</html>
"""

components.html(fridge_html, height=720, scrolling=False)

# ── [수정] 냉장고 닫힌 상태: 시작하기 버튼 / 열린 상태: 닫기 버튼만 표시 ──
col1, col2, col3 = st.columns([1.5, 2.5, 1.5])
with col2:
    if not is_open:
        # 닫힌 상태 → 시작하기 버튼
        if st.button("🧊 냉털 AI 시작하기"):
            st.session_state.fridge_open = True
            st.rerun()
    else:
        # [수정] 열린 상태 → "냉털 AI 시작하기" 버튼 숨기고 닫기 버튼만 표시
        if st.button("🚪 냉장고 닫기"):
            st.session_state.fridge_open = False
            st.rerun()
