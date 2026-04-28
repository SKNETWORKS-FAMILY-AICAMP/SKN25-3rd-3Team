// =============================================================
// 냉털봇 프론트엔드 (4차 — 로그인/즐겨찾기 추가)
// =============================================================
(function () {
  // ---- 1. 데이터 / 설정 로드 ----
  const cfgEl = document.getElementById('data-config');
  const CHAT_API = cfgEl.dataset.chatApi;
  const PREFS_API = cfgEl.dataset.prefsApi;
  const RESET_API = cfgEl.dataset.resetApi;

  const savedSauces = JSON.parse(
    document.getElementById('data-saved-sauces').textContent
  );
  const initialMessages = JSON.parse(
    document.getElementById('data-messages').textContent
  );
  const auth = JSON.parse(document.getElementById('data-auth').textContent);
  const initialFavIds = JSON.parse(
    document.getElementById('data-favorite-ids').textContent
  );
  const favoriteMongoIds = new Set(initialFavIds);

  let chatHistory = initialMessages.slice();
  let isSending = false;

  // ---- 2. DOM refs ----
  const fridge = document.getElementById('fridge');
  const chatBody = document.getElementById('chatBody');
  const msgInput = document.getElementById('msgInput');
  const sendBtn = document.getElementById('sendBtn');
  const bigToggle = document.getElementById('bigToggle');
  const prefToggle = document.getElementById('prefToggle');
  const prefBody = document.getElementById('prefBody');
  const prefArrow = document.getElementById('prefArrow');
  const allergyInput = document.getElementById('allergyInput');
  const diffInput = document.getElementById('diffInput');
  const timeInput = document.getElementById('timeInput');
  const openSauceBtn = document.getElementById('openSauce');
  const closeSauceBtn = document.getElementById('closeSauce');
  const saucePage = document.getElementById('saucePage');
  const sauceBody = document.getElementById('sauceBody');
  const saveSaucesBtn = document.getElementById('saveSauces');
  const resetBtn = document.getElementById('resetChat');

  chatBody.scrollTop = chatBody.scrollHeight;

  // ---- 3. CSRF ----
  function getCookie(name) {
    const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return m ? decodeURIComponent(m.pop()) : '';
  }

  // ---- 4. 메시지 렌더링 ----
  function escapeHtml(text) {
    return String(text)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function buildBadge(source) {
    const labels = { db: 'DB', web: 'WEB', llm: 'LLM 추정' };
    const label = labels[source];
    if (!label) return '';
    return `<span class="src-badge ${source}">${label}</span><br>`;
  }

  function buildCandidateCards(candidates, source) {
    if (!candidates || candidates.length === 0) return '';
    const cards = candidates.map((c) => {
      const isFav = c.mongo_recipe_id && favoriteMongoIds.has(c.mongo_recipe_id);
      const cls = isFav ? 'on' : '';
      const aria = isFav ? '저장 취소' : '저장';
      const dataJson = escapeHtml(JSON.stringify({
        mongo_recipe_id: c.mongo_recipe_id || '',
        title: c.title,
        url: c.url,
        ingredients_summary: c.ingredients_summary,
        source,
      }));
      const titleSafe = escapeHtml(c.title);
      const ingSafe = escapeHtml(c.ingredients_summary || '').slice(0, 120);
      const linkBlock = c.url
        ? `<a class="cand-link" href="${escapeHtml(c.url)}" target="_blank" rel="noopener">원문 ↗</a>`
        : '';
      return `
        <div class="cand-card">
          <button type="button" class="star-btn ${cls}" data-recipe='${dataJson}' aria-label="${aria}">★</button>
          <div class="cand-title">${titleSafe}</div>
          <div class="cand-ing">${ingSafe}</div>
          ${linkBlock}
        </div>`;
    }).join('');
    return `<div class="cand-list">${cards}</div>`;
  }

  function addMsg(role, text, options) {
    options = options || {};
    const div = document.createElement('div');
    div.className = 'm' + (role === 'user' ? ' u' : '');

    const safe = escapeHtml(text).replace(/\n/g, '<br>');
    if (role === 'bot') {
      const badge = options.source ? buildBadge(options.source) : '';
      const cards = buildCandidateCards(options.candidates, options.source);
      div.innerHTML =
        '<div class="m-icon">🤖</div>' +
        '<div class="bub b">' + badge + safe + cards + '</div>';
    } else {
      div.innerHTML =
        '<div class="bub u">' + safe + '</div>' +
        '<div class="m-icon">🙋</div>';
    }
    chatBody.appendChild(div);
    chatBody.scrollTop = chatBody.scrollHeight;
    bindStarButtons(div);
    return div;
  }

  // ---- 4-1. 별 버튼 바인딩 (저장 토글) ----
  function bindStarButtons(scope) {
    scope.querySelectorAll('.star-btn').forEach((btn) => {
      if (btn.dataset.bound) return;
      btn.dataset.bound = '1';
      btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        if (!auth.isAuthenticated) {
          if (confirm('레시피 저장은 로그인 후 이용할 수 있어요. 로그인하시겠어요?')) {
            location.href = '/accounts/login/';
          }
          return;
        }

        const data = JSON.parse(btn.dataset.recipe);
        const isOn = btn.classList.contains('on');

        if (isOn) {
          // 삭제 — favoriteMongoIds 만 제거 (DELETE는 favorite id 필요해서 별도 페이지에서)
          // 단순화: 다시 누르면 '저장 취소' 안내만 띄우고 페이지 안내
          if (confirm('저장을 취소하려면 ★ 내 저장 레시피 페이지에서 삭제해주세요. 페이지로 이동할까요?')) {
            location.href = '/favorites/';
          }
          return;
        }

        try {
          btn.disabled = true;
          const res = await fetch('/api/favorites/', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify(data),
          });
          if (res.status === 403 || res.status === 302) {
            alert('로그인이 필요합니다.');
            location.href = '/accounts/login/';
            return;
          }
          const j = await res.json();
          if (j.ok) {
            btn.classList.add('on');
            btn.setAttribute('aria-label', '저장 취소');
            if (data.mongo_recipe_id) {
              favoriteMongoIds.add(data.mongo_recipe_id);
            }
            showToast(j.duplicate ? '이미 저장되어 있어요!' : '★ 저장 완료');
          } else {
            alert(j.error || '저장 실패');
          }
        } catch (err) {
          alert('네트워크 오류: ' + err.message);
        } finally {
          btn.disabled = false;
        }
      });
    });
  }

  // ---- 4-2. 토스트 알림 ----
  function showToast(msg) {
    let toast = document.getElementById('toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'toast';
      toast.className = 'toast';
      document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.classList.add('show');
    clearTimeout(toast._timer);
    toast._timer = setTimeout(() => toast.classList.remove('show'), 2000);
  }

  // ---- 5. 냉장고 토글 ----
  function openFridge() {
    fridge.classList.add('open');
    bigToggle.textContent = '🚪 냉장고 닫기';
    setTimeout(() => msgInput && msgInput.focus(), 1100);
  }
  function closeFridge() {
    fridge.classList.remove('open');
    bigToggle.textContent = '🧊 냉털 AI 시작하기';
  }
  bigToggle.addEventListener('click', (e) => {
    e.stopPropagation();
    fridge.classList.contains('open') ? closeFridge() : openFridge();
  });
  fridge.addEventListener('click', (e) => {
    if (!fridge.classList.contains('open')) {
      e.stopPropagation();
      openFridge();
    }
  });
  document.getElementById('chatInner').addEventListener('click', (e) => e.stopPropagation());
  document.getElementById('saucePage').addEventListener('click', (e) => e.stopPropagation());

  // ---- 6. 취향 토글 ----
  prefToggle.addEventListener('click', () => {
    prefBody.classList.toggle('open');
    prefArrow.textContent = prefBody.classList.contains('open') ? '▼' : '▶';
  });

  // ---- 7. 메시지 전송 ----
  function setSending(v) {
    isSending = v;
    msgInput.disabled = v;
    sendBtn.disabled = v;
  }

  async function sendQuestion(text) {
    if (isSending || !text) return;
    addMsg('user', text);
    chatHistory.push({ role: 'user', text });
    const loading = addMsg('bot', '🍳 레시피를 찾고 있어요...');

    const payload = {
      question: text,
      allergies: allergyInput.value || '없음',
      difficulty: diffInput.value || '초보',
      cooking_time: timeInput.value || '20분',
      saved_sauces: savedSauces && savedSauces.length ? savedSauces.join(', ') : '없음',
      chat_history: chatHistory.slice(-8),
    };

    setSending(true);
    try {
      const res = await fetch(CHAT_API, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify(payload),
      });
      const raw = await res.text();
      if (!res.ok) throw new Error('HTTP ' + res.status + '\n' + raw);
      const data = JSON.parse(raw);
      const answer = data.answer || '레시피 서버 응답 형식이 올바르지 않습니다.';

      loading.remove();
      addMsg('bot', answer, { source: data.source, candidates: data.candidates });
      chatHistory.push({ role: 'bot', text: answer });
    } catch (err) {
      loading.remove();
      addMsg('bot', '서버 요청에 실패했습니다.\n' + (err && err.message || err));
    } finally {
      setSending(false);
      msgInput.focus();
    }
  }

  sendBtn.addEventListener('click', () => {
    const v = msgInput.value.trim();
    if (v) { sendQuestion(v); msgInput.value = ''; }
  });
  msgInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendBtn.click();
    }
  });
  document.querySelectorAll('.faq-btn').forEach((btn) => {
    btn.addEventListener('click', () => sendQuestion(btn.dataset.faq));
  });

  // ---- 8. 소스 저장 ----
  const SAUCE_LIST = [
    ['기본 양념 및 소스', ['진간장','국간장','고추장','된장','쌈장','굴소스','식초','사과식초','발사믹식초','맛술','미림','케첩','마요네즈','설탕','소금','후추','고춧가루','다진 마늘','액젓 (멸치액젓)','액젓 (까나리액젓)','올리고당 / 물엿']],
    ['기름류', ['식용유','올리브오일','참기름','들기름','버터','고추기름','아보카도유','트러플 오일','라드']],
    ['트렌디 & 에스닉 소스', ['스리라차','두반장','타바스코','쯔유','피시소스','바질 페스토','홀그레인 머스터드','우스터소스','XO소스','머스타드']],
    ['편의형 만능 소스', ['불닭 소스','참치액','연두','치킨스톡','돈가스 소스','데리야끼 소스','스테이크 소스','청주']],
    ['드레싱 및 기타', ['오리엔탈 드레싱','참깨 드레싱','허니 머스터드','파마산 치즈 가루','와사비 (고추냉이)']],
  ];

  function renderSauceList() {
    let html = '';
    for (const [cat, items] of SAUCE_LIST) {
      html += `<div class="cat-label">${cat}</div><div class="check-grid">`;
      for (const it of items) {
        const checked = savedSauces.indexOf(it) !== -1 ? 'checked' : '';
        html += `<label class="check-item"><input type="checkbox" value="${it}" ${checked}><span>${it}</span></label>`;
      }
      html += '</div>';
    }
    sauceBody.innerHTML = html;
  }

  openSauceBtn.addEventListener('click', () => {
    renderSauceList();
    saucePage.classList.add('active');
  });
  closeSauceBtn.addEventListener('click', () => saucePage.classList.remove('active'));

  saveSaucesBtn.addEventListener('click', async () => {
    const checked = Array.from(sauceBody.querySelectorAll('input:checked')).map((el) => el.value);
    savedSauces.length = 0;
    Array.prototype.push.apply(savedSauces, checked);

    try {
      await fetch(PREFS_API, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({ saved_sauces: checked }),
      });
    } catch (e) { console.warn('소스 저장 실패', e); }

    saucePage.classList.remove('active');
    const note = checked.length
      ? `소스 저장 완료! 🎉 현재 사용 가능: ${checked.join(', ')}`
      : '선택된 소스가 없어요 😅 보유 중인 소스를 체크해 주세요!';
    addMsg('bot', note);
    chatHistory.push({ role: 'bot', text: note });
  });

  // ---- 9. 대화 비우기 ----
  resetBtn.addEventListener('click', async () => {
    if (!confirm('대화 내역을 모두 비우시겠어요?')) return;
    try {
      await fetch(RESET_API, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') },
      });
    } catch (e) { console.warn(e); }
    chatBody.innerHTML = '';
    chatHistory = [];
    addMsg('bot', '안녕하세요! 🧅 냉장고 속 재료를 알려주시면 딱 맞는 레시피를 찾아드릴게요!');
    addMsg('bot', '냉장고 문을 열고 재료를 직접 입력해보세요 👇');
  });
})();
