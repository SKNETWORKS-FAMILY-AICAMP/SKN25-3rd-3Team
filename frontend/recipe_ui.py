# =====================================================================
# [전체 프로젝트에서의 역할: UI 전담 고해상도 렌더링 모듈]
# 이 파일은 '냉털봇' 서비스의 시각적 인터페이스를 생성하고 출력합니다.
# 1. 안전한 JS 이벤트 제어: JS 엔진이 충돌하지 않도록 예외 처리(if e...)를 추가했습니다.
# 2. 방대한 소스 데이터: 60여 개의 상세 소스 카테고리 데이터를 보유합니다.
# =====================================================================

import html as html_module
import json
import os

import streamlit as st
import streamlit.components.v1 as components

def render_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; background-color: #fff8f3; }
    .block-container { padding-top: 0.5rem !important; padding-bottom: 0rem !important; max-width: 480px !important; }
    #MainMenu, footer, header { visibility: hidden; }
    [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"] { display: none !important; }
    
    .stButton > button {
        border: 1.5px solid #EA580C !important; color: #EA580C !important;
        border-radius: 20px !important; background: transparent !important;
        font-size: 13px !important; padding: 6px 24px !important; font-weight: 700;
    }
    .stButton > button:hover { background: #EA580C !important; color: #fff !important; }
    hr { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

def get_sauce_grid_html(saved_sauces):
    sauce_list = [
        ("기본 양념 및 소스", ["진간장", "국간장", "고추장", "된장", "쌈장", "굴소스", "식초", "사과식초", "발사믹식초", "맛술", "미림", "케첩", "마요네즈", "설탕", "소금", "후추", "고춧가루", "다진 마늘", "액젓 (멸치액젓)", "액젓 (까나리액젓)", "올리고당 / 물엿"]),
        ("기름류", ["식용유", "올리브오일", "참기름", "들기름", "버터", "고추기름", "아보카도유", "트러플 오일", "라드"]),
        ("트렌디 & 에스닉 소스", ["스리라차", "두반장", "타바스코", "쯔유", "피시소스", "바질 페스토", "홀그레인 머스터드", "우스터소스", "XO소스", "머스타드"]),
        ("편의형 만능 소스", ["불닭 소스", "참치액", "연두", "치킨스톡", "돈가스 소스", "데리야끼 소스", "스테이크 소스", "청주"]),
        ("드레싱 및 기타", ["오리엔탈 드레싱", "참깨 드레싱", "허니 머스터드", "파마산 치즈 가루", "와사비 (고추냉이)"]),
    ]
    html_out = ""
    for category, items in sauce_list:
        html_out += f'<div class="cat-label" style="font-size:11px; font-weight:700; color:#EA580C; margin:6px 0 4px;">{category}</div>'
        html_out += '<div class="check-grid" style="display:grid; grid-template-columns:1fr 1fr; gap:6px; margin-bottom:10px;">'
        for item in items:
            checked = "checked" if item in saved_sauces else ""
            html_out += f'<label class="check-item" style="display:flex; align-items:center; gap:6px; background:#fff3ec; border:1px solid #f5d0b0; border-radius:10px; padding:7px 10px; font-size:11px; color:#7c3a10; cursor:pointer;">'
            html_out += f'<input type="checkbox" value="{item}" {checked} style="accent-color:#EA580C;"><span>{item}</span></label>'
        html_out += '</div>'
    return html_out

def render_fridge_ui(messages, is_open, just_opened, allergies, difficulty, cooking_time, saved_sauces):
    api_chat_url = os.getenv("RECIPE_API_URL", "http://127.0.0.1:8000/chat")
    saved_sauces_text = ", ".join(saved_sauces) if saved_sauces else "없음"
    messages_json = json.dumps(messages, ensure_ascii=False).replace("</", "<\\/")
    msgs_html = ""
    for m in messages:
        safe_text = html_module.escape(m["text"]).replace("\n", "<br>")
        role_class = " u" if m["role"] == "user" else ""
        bub_class = " u" if m["role"] == "user" else " b"
        icon = "🙋" if m["role"] == "user" else "🤖"
        msgs_html += f'<div class="m{role_class}"><div class="m-icon">{icon}</div><div class="bub{bub_class}">{safe_text}</div></div>'

    sauce_items_html = get_sauce_grid_html(saved_sauces)
    
    if just_opened:
        left_t, right_t = "perspective(900px) rotateY(0deg)", "perspective(900px) rotateY(0deg)"
        inner_opacity, inner_pointer, door_pointer = "0", "none", "none"
        auto_open_script = """
        setTimeout(function() {
            document.getElementById('doorL').style.transform = 'perspective(900px) rotateY(-122deg)';
            document.getElementById('doorR').style.transform = 'perspective(900px) rotateY(122deg)';
            setTimeout(function() {
                var inner = document.getElementById('chatInner');
                inner.style.opacity = '1'; inner.style.pointerEvents = 'auto';
                var inp = document.getElementById('msgInput'); if (inp) inp.focus();
            }, 900);
        }, 100);
        """
    else:
        left_t  = f"perspective(900px) rotateY({'-122deg' if is_open else '0deg'})"
        right_t = f"perspective(900px) rotateY({'122deg' if is_open else '0deg'})"
        inner_opacity = "1" if is_open else "0"
        inner_pointer = "auto" if is_open else "none"
        door_pointer  = "none" if is_open else "auto"
        auto_open_script = ""

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
    * {{ box-sizing:border-box; margin:0; padding:0; }}
    body {{ background:transparent; font-family:'Noto Sans KR',sans-serif; overflow:hidden; }}
    .scene {{ display:flex; flex-direction:column; align-items:center; padding:4px 0; }}
    .fridge {{ position:relative; width:420px; height:720px; background:#e2ddd8; border-radius:26px; border:3px solid #c8c2bc; overflow:hidden; cursor:pointer; }}
    .fridge-top {{ position:absolute; top:10px; left:50%; transform:translateX(-50%); width:70px; height:7px; background:#c8c2bc; border-radius:4px; z-index:10; }}
    .inner {{ position:absolute; inset:0; background:#fffaf5; border-radius:24px; display:flex; flex-direction:column; overflow:hidden; opacity:{inner_opacity}; transition:opacity 0.5s ease 0.9s; pointer-events:{inner_pointer}; }}
    .hdr {{ background:#EA580C; padding:12px 16px; display:flex; align-items:center; gap:10px; flex-shrink:0; }}
    .hdr-av {{ width:36px; height:36px; border-radius:50%; background:#fff3ec; display:flex; align-items:center; justify-content:center; font-size:20px; }}
    .hdr-title {{ color:#fff; font-size:14px; font-weight:700; }}
    .hdr-sub {{ color:#ffd4b8; font-size:10px; }}
    .chat {{ flex:1; overflow-y:auto; padding:12px; display:flex; flex-direction:column; gap:8px; }}
    .m {{ display:flex; gap:6px; align-items:flex-end; }} .m.u {{ flex-direction:row-reverse; }}
    .m-icon {{ width:26px; height:26px; border-radius:50%; background:#fff3ec; border:1px solid #f5d0b0; display:flex; align-items:center; justify-content:center; font-size:13px; flex-shrink:0; }}
    .bub {{ max-width:78%; padding:8px 12px; border-radius:14px; font-size:12px; line-height:1.55; word-break:keep-all; }}
    .bub.b {{ background:#fff3ec; color:#7c3a10; border-bottom-left-radius:3px; border:1px solid #f5d0b0; }}
    .bub.u {{ background:#EA580C; color:#fff; border-bottom-right-radius:3px; }}
    .bottom-area {{ flex-shrink:0; background:#fff8f2; border-top:1px solid #f0ddd0; padding:8px 12px 6px; }}
    .faq-lbl {{ font-size:10px; color:#b07050; font-weight:700; letter-spacing:0.05em; margin-bottom:6px; }}
    .faq-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:5px; margin-bottom:8px; }}
    .faq-btn {{ background:#fff; border:1.5px solid #f0c8a0; border-radius:20px; padding:7px 6px; font-size:11px; color:#9a4a10; cursor:pointer; text-align:center; font-family:'Noto Sans KR'; transition:all 0.15s; }}
    .faq-btn:hover {{ background:#fff3ec; border-color:#EA580C; color:#EA580C; }}
    .pref-header {{ font-size:11px; color:#9a4a10; cursor:pointer; display:flex; align-items:center; gap:4px; margin-bottom:6px; }}
    .pref-body {{ display:none; padding-bottom:6px; }} .pref-body.open {{ display:block; }}
    .pref-row {{ display:flex; align-items:center; gap:8px; margin-bottom:6px; font-size:11px; color:#7c3a10; }}
    .pref-row label {{ min-width:70px; font-weight:500; }}
    .pref-row select, .pref-row input {{ flex:1; border:1px solid #f0d0b0; border-radius:8px; padding:4px 8px; font-size:11px; background:#fff; outline:none; }}
    .action-btn {{ width:100%; background:#fff; border:1.5px solid #EA580C; border-radius:18px; padding:6px; font-size:11.5px; color:#EA580C; cursor:pointer; font-weight:700; }}
    .inp-area {{ display:flex; align-items:center; gap:6px; padding:6px 12px 12px; background:#fff8f2; }}
    .inp-area input {{ flex:1; border:1.5px solid #f0d0b0; border-radius:22px; padding:9px 14px; font-size:12px; background:#fff; outline:none; }}
    .send-btn {{ width:34px; height:34px; border-radius:50%; background:#EA580C; border:none; cursor:pointer; display:flex; align-items:center; justify-content:center; }}
    .send-btn svg {{ width:13px; height:13px; fill:#fff; }}
    .sauce-page {{ position:absolute; inset:0; background:#fffaf5; border-radius:24px; display:flex; flex-direction:column; opacity:0; pointer-events:none; transition:opacity 0.3s; z-index:20; }}
    .sauce-page.active {{ opacity:1; pointer-events:auto; }}
    .sauce-hdr {{ background:#EA580C; padding:12px 16px; display:flex; align-items:center; color:#fff; font-weight:700; font-size:14px; }}
    .sauce-close {{ margin-left:auto; background:rgba(255,255,255,0.2); border:none; border-radius:50%; width:28px; height:28px; color:#fff; cursor:pointer; }}
    .sauce-body {{ flex:1; overflow-y:auto; padding:14px; }}
    .sauce-save-btn {{ margin:10px 14px 14px; background:#EA580C; color:#fff; border:none; border-radius:22px; padding:10px; font-size:12px; font-weight:700; cursor:pointer; }}
    .doors {{ position:absolute; inset:0; display:flex; pointer-events:{door_pointer}; }}
    .door {{ width:50%; height:100%; background:linear-gradient(160deg,#dedad4 0%,#ccc8c2 100%); border:2.5px solid #b8b2ac; transition:transform 1.3s cubic-bezier(0.4,0,0.2,1); position:relative; display:flex; align-items:center; justify-content:center; flex-direction:column; }}
    .door-l {{ transform-origin:0% center; border-radius:24px 0 0 24px; transform:{left_t}; }}
    .door-r {{ transform-origin:100% center; border-radius:0 24px 24px 0; transform:{right_t}; }}
    .d-handle {{ width:6px; height:64px; background:#9a9490; border-radius:3px; position:absolute; }}
    .door-l .d-handle {{ right:14px; }} .door-r .d-handle {{ left:14px; }}
    .door-logo {{ font-size:36px; opacity:0.45; }}
    .door-hint {{ font-size:11px; color:#999; margin-top:10px; }}
    </style>
    </head>
    <body>
    <div class="scene">
      <div class="fridge" id="fridge" onclick="handleFridgeClick()">
        <div class="fridge-top"></div>
        <div class="inner" id="chatInner">
          <div class="hdr"><div class="hdr-av">🍳</div><div><div class="hdr-title">냉털봇</div><div class="hdr-sub">재료 소진 레시피 AI</div></div></div>
          <div class="chat" id="chatBody">{msgs_html}</div>
          <div class="bottom-area">
            <div class="faq-lbl">✨ 자주 찾는 기능</div>
            <div class="faq-grid">
              <button class="faq-btn" onclick="sendFaq(event, '🥕 재료로 레시피 찾기')">🥕 재료로 레시피 찾기</button>
              <button class="faq-btn" onclick="sendFaq(event, '📅 오늘 뭐 먹지?')">📅 오늘 뭐 먹지?</button>
              <button class="faq-btn" onclick="sendFaq(event, '🔥 재료 소진 플랜')">🔥 재료 소진 플랜</button>
              <button class="faq-btn" onclick="sendFaq(event, '💪 다이어트 레시피')">💪 다이어트 레시피</button>
            </div>
            <div class="pref-header" onclick="togglePref(event)"><span id="prefArrow">▶</span> ⚙️ 취향 설정</div>
            <div class="pref-body" id="prefBody">
              <div class="pref-row"><label>알레르기</label><input type="text" id="allergyInput" value="{html_module.escape(allergies)}"></div>
              <div class="pref-row"><label>난이도</label><select id="diffInput">
                <option {'selected' if difficulty=='초보' else ''}>초보</option>
                <option {'selected' if difficulty=='보통' else ''}>보통</option>
                <option {'selected' if difficulty=='고수' else ''}>고수</option>
              </select></div>
              <div class="pref-row"><label>조리시간</label><select id="timeInput">
                <option {'selected' if cooking_time=='15분' else ''}>15분</option>
                <option {'selected' if cooking_time=='20분' else ''}>20분</option>
                <option {'selected' if cooking_time=='30분' else ''}>30분</option>
              </select></div>
            </div>
            <button class="action-btn" onclick="openSaucePage(event)">🧴 소스 및 양념 저장하기</button>
          </div>
          <div class="inp-area">
            <input type="text" id="msgInput" placeholder="재료를 입력하세요..." onkeydown="if(event.key==='Enter') sendMsg(event)" autocomplete="off">
            <button class="send-btn" onclick="sendMsg(event)"><svg viewBox="0 0 24 24"><path d="M2 21l21-9L2 3v7l15 2-15 2z"/></svg></button>
          </div>
        </div>
        <div class="sauce-page" id="saucePage">
          <div class="sauce-hdr">내 소스 저장하기 <button class="sauce-close" onclick="closeSaucePage(event)">✕</button></div>
          <div class="sauce-body">{sauce_items_html}</div>
          <button class="sauce-save-btn" onclick="saveSauces(event)">✅ 선택 완료 및 저장</button>
        </div>
        <div class="doors" id="doors">
          <div class="door door-l" id="doorL"><div class="d-handle"></div><div class="door-logo">🧊</div><div class="door-hint">탭하여 시작</div></div>
          <div class="door door-r" id="doorR"><div class="d-handle"></div><div class="door-logo">🍳</div><div class="door-hint">탭하여 시작</div></div>
        </div>
      </div>
    </div>
    <script>
      {auto_open_script}
      var isOpen = {'true' if is_open else 'false'};
      var apiChatUrl = {json.dumps(api_chat_url, ensure_ascii=False)};
      var savedSauces = {json.dumps(saved_sauces_text, ensure_ascii=False)};
      var chatHistory = {messages_json};
      var isSending = false;
      var cb = document.getElementById('chatBody'); if(cb) cb.scrollTop = cb.scrollHeight;
      if (isOpen) {{ setTimeout(function() {{ var inp = document.getElementById('msgInput'); if(inp) inp.focus(); }}, 300); }}

      function escapeHtml(text) {{
        return String(text)
          .replace(/&/g, '&amp;')
          .replace(/</g, '&lt;')
          .replace(/>/g, '&gt;')
          .replace(/"/g, '&quot;')
          .replace(/'/g, '&#39;');
      }}

      function handleFridgeClick() {{
        if (!isOpen) {{
            isOpen = true;
            try {{
                var btns = window.parent.document.querySelectorAll('button');
                for (var i = 0; i < btns.length; i++) {{
                    if (btns[i].innerText.includes('냉털 AI 시작하기')) {{ btns[i].click(); return; }}
                }}
            }} catch(e) {{ }}
            if (window.parent && window.parent.location) {{
                window.parent.location.href = window.parent.location.origin + window.parent.location.pathname + '?action=sync_open';
            }}
        }}
      }}

      function addMsg(role, text) {{
        var div = document.createElement('div'); div.className = 'm' + (role==='user'?' u':'');
        var safeText = escapeHtml(text).replace(/\\n/g, '<br>');
        div.innerHTML = (role==='bot'?'<div class="m-icon">🤖</div>':'') + '<div class="bub '+(role==='bot'?'b':'u')+'">'+safeText+'</div>' + (role==='user'?'<div class="m-icon">🙋</div>':'');
        cb.appendChild(div); cb.scrollTop = cb.scrollHeight;
        return div;
      }}

      function setSendingState(sending) {{
        isSending = sending;
        var inp = document.getElementById('msgInput');
        var btn = document.querySelector('.send-btn');
        if (inp) inp.disabled = sending;
        if (btn) btn.disabled = sending;
      }}

      async function sendToStreamlit(text, source) {{
        if (isSending) return;
        addMsg('user', text);
        chatHistory.push({{ role: 'user', text: text }});
        var loadingMsg = addMsg('bot', '🍳 레시피를 찾고 있어요...');
        var p = getPrefs();
        var payload = {{
          question: text,
          allergies: p.a,
          difficulty: p.d,
          cooking_time: p.t,
          saved_sauces: savedSauces,
          chat_history: chatHistory.slice(-8)
        }};

        try {{
          setSendingState(true);
          var response = await fetch(apiChatUrl, {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify(payload)
          }});
          var rawBody = await response.text();

          if (!response.ok) {{
            throw new Error('HTTP ' + response.status + '\\n' + rawBody);
          }}

          var data = JSON.parse(rawBody);
          var answer = data.answer || '레시피 서버 응답 형식이 올바르지 않습니다.';
          if (loadingMsg && loadingMsg.remove) loadingMsg.remove();
          addMsg('bot', answer);
          chatHistory.push({{ role: 'bot', text: answer }});
        }} catch (error) {{
          if (loadingMsg && loadingMsg.remove) loadingMsg.remove();
          var errorText = '서버 요청에 실패했습니다.\\n' + (error && error.message ? error.message : error);
          addMsg('bot', errorText);
          chatHistory.push({{ role: 'bot', text: errorText }});
        }} finally {{
          setSendingState(false);
          var inp = document.getElementById('msgInput');
          if (inp) inp.focus();
        }}
      }}

      function sendMsg(e) {{ 
          if (e && e.stopPropagation) e.stopPropagation(); 
          var inp = document.getElementById('msgInput'); var val = inp.value.trim(); 
          if(val) {{ sendToStreamlit(val, 'sendMsg'); inp.value=''; }} 
      }}
      function sendFaq(e, text) {{ if (e && e.stopPropagation) e.stopPropagation(); sendToStreamlit(text, 'sendFaq'); }}
      function getPrefs() {{ return {{ a: document.getElementById('allergyInput').value || '없음', d: document.getElementById('diffInput').value || '초보', t: document.getElementById('timeInput').value || '20분' }}; }}
      function togglePref(e) {{ 
          if (e && e.stopPropagation) e.stopPropagation(); 
          document.getElementById('prefBody').classList.toggle('open'); 
          document.getElementById('prefArrow').textContent = document.getElementById('prefBody').classList.contains('open') ? '▼' : '▶'; 
      }}
      function openSaucePage(e) {{ if (e && e.stopPropagation) e.stopPropagation(); document.getElementById('saucePage').classList.add('active'); }}
      function closeSaucePage(e) {{ if (e && e.stopPropagation) e.stopPropagation(); document.getElementById('saucePage').classList.remove('active'); }}
      function saveSauces(e) {{ 
          if (e && e.stopPropagation) e.stopPropagation(); 
          var checked = []; document.querySelectorAll('.sauce-body input:checked').forEach(el => checked.push(el.value));
          if (window.parent && window.parent.location) {{
              var url = window.parent.location.origin + window.parent.location.pathname + '?sauces=' + (checked.length ? encodeURIComponent(checked.join(',')) : 'none');
              window.parent.location.href = url;
          }}
      }}
    </script>
    </body>
    </html>
    """
    components.html(full_html, height=750, scrolling=False)
