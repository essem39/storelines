(function() {

  function parseMarkdown(text) {
    if (!text) return '';
    let t = text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    t = t.replace(/\*\*([^*]+):\*\*/g, (m,h) => {
      const colors = ['#ff6900','#2563eb','#059669','#7c3aed','#dc2626','#0891b2'];
      const c = colors[Math.abs(h.charCodeAt(0)) % colors.length];
      return '<div style="margin:10px 0 4px;padding:6px 12px;background:'+c+'15;border-left:3px solid '+c+';border-radius:0 8px 8px 0;font-weight:700;font-size:12px;color:'+c+'">'+h+'</div>';
    });
    t = t.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    t = t.replace(/\*(.+?)\*/g, '<em style="color:#6b7280">$1</em>');
    let num = 0;
    t = t.replace(/(?:^|\n)(\d+)\.\s+(.+)/g, (m,n,item) => {
      num++;
      const colors = ['#ff6900','#2563eb','#059669','#7c3aed','#dc2626','#0891b2'];
      const c = colors[(num-1) % colors.length];
      return '<div style="display:flex;gap:10px;align-items:baseline;margin:4px 0;padding:6px 10px;background:'+c+'08;border-radius:8px;border:1px solid '+c+'20"><span style="background:'+c+';color:#fff;border-radius:50%;width:20px;height:20px;display:inline-flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;flex-shrink:0">'+num+'</span><span>'+item+'</span></div>';
    });
    t = t.replace(/(?:^|\n)[-•]\s+(.+)/g, (m,item) => '<div style="display:flex;gap:8px;align-items:baseline;margin:3px 0;padding:4px 8px;background:#fff7ed;border-radius:6px"><span style="color:#ff6900;font-weight:700;flex-shrink:0">›</span><span>'+item+'</span></div>');
    t = t.replace(/`(.+?)`/g, '<code style="background:#f1f5f9;padding:1px 6px;border-radius:4px;font-size:11px;font-family:monospace">$1</code>');
    t = t.replace(/\n/g, '<br>');
    return t;
  }

  const WORKER_URL = 'https://storepilot.esem39.workers.dev';

  const styles = `
    #storepilot-btn {
      position: fixed; bottom: 24px; right: 24px; z-index: 9999;
      width: 60px; height: 60px; border-radius: 50%;
      background: linear-gradient(135deg, #ff6900, #ff8c00);
      border: none; cursor: pointer;
      box-shadow: 0 4px 20px rgba(255,105,0,0.4);
      display: flex; align-items: center; justify-content: center;
      font-size: 26px; transition: transform 0.2s;
    }
    #storepilot-btn:hover { transform: scale(1.1); }
    #storepilot-chat {
      position: fixed; bottom: 96px; right: 24px; z-index: 9999;
      width: 360px; height: 540px;
      background: #fff; border-radius: 20px;
      box-shadow: 0 8px 40px rgba(0,0,0,0.18);
      display: none; flex-direction: column; overflow: hidden;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    #storepilot-chat.open { display: flex; }
    .sp-header {
      background: linear-gradient(135deg, #ff6900, #ff8c00);
      color: white; padding: 16px 18px;
      display: flex; align-items: center; justify-content: space-between;
    }
    .sp-header-left { display: flex; align-items: center; gap: 10px; }
    .sp-avatar {
      width: 36px; height: 36px; border-radius: 50%;
      background: rgba(255,255,255,0.25);
      display: flex; align-items: center; justify-content: center; font-size: 18px;
    }
    .sp-title { font-weight: 700; font-size: 15px; }
    .sp-subtitle { font-size: 11px; opacity: 0.85; }
    .sp-close { background: none; border: none; color: white; font-size: 20px; cursor: pointer; opacity: 0.8; }
    .sp-close:hover { opacity: 1; }
    .sp-messages {
      flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px;
    }
    .sp-msg { display: flex; gap: 8px; }
    .sp-msg.user { flex-direction: row-reverse; }
    .sp-msg-avatar {
      width: 28px; height: 28px; border-radius: 50%; flex-shrink: 0;
      background: linear-gradient(135deg, #ff6900, #ff8c00);
      display: flex; align-items: center; justify-content: center;
      font-size: 13px; color: white;
    }
    .sp-msg.user .sp-msg-avatar { background: #e2e8f0; color: #475569; }
    .sp-bubble {
      max-width: 260px; padding: 10px 14px; border-radius: 16px;
      font-size: 13px; line-height: 1.5; color: #1e293b;
      background: #f1f5f9;
    }
    .sp-msg.user .sp-bubble { background: linear-gradient(135deg, #ff6900, #ff8c00); color: white; border-radius: 16px 16px 4px 16px; }
    .sp-bubble a { color: #ff6900; text-decoration: none; font-weight: 600; }
    .sp-msg.user .sp-bubble a { color: white; text-decoration: underline; }
    .sp-bubble ul { margin: 6px 0; padding-left: 16px; }
    .sp-typing { display: flex; align-items: center; gap: 4px; padding: 10px 14px; }
    .sp-typing span { width: 7px; height: 7px; border-radius: 50%; background: #ff6900; animation: sp-bounce 1.2s infinite; }
    .sp-typing span:nth-child(2) { animation-delay: 0.2s; }
    .sp-typing span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes sp-bounce { 0%,60%,100%{transform:translateY(0)} 30%{transform:translateY(-8px)} }
    .sp-input-area {
      padding: 12px 16px; border-top: 1px solid #f1f5f9;
      display: flex; gap: 8px; align-items: flex-end;
    }
    .sp-input {
      flex: 1; border: 2px solid #e2e8f0; border-radius: 12px;
      padding: 8px 12px; font-size: 13px; outline: none; resize: none;
      font-family: inherit; line-height: 1.4; max-height: 80px;
    }
    .sp-input:focus { border-color: #ff6900; }
    .sp-send {
      width: 36px; height: 36px; border-radius: 50%; border: none;
      background: linear-gradient(135deg, #ff6900, #ff8c00);
      color: white; cursor: pointer; display: flex; align-items: center; justify-content: center;
      font-size: 16px; flex-shrink: 0; transition: transform 0.2s;
    }
    .sp-send:hover { transform: scale(1.1); }
    .sp-send:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
    .sp-mic {
      width: 36px; height: 36px; border-radius: 50%; border: 2px solid #ff6900;
      background: white; color: #ff6900; cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      font-size: 16px; flex-shrink: 0; transition: all 0.2s;
    }
    .sp-mic:hover { background: #ff6900; color: white; }
    .sp-mic.listening { background: #ff6900; color: white; animation: sp-pulse 1s infinite; }
    @keyframes sp-pulse { 0%,100%{box-shadow:0 0 0 0 rgba(255,105,0,0.4)} 50%{box-shadow:0 0 0 8px rgba(255,105,0,0)} }
    .sp-quick { display: flex; flex-wrap: wrap; gap: 6px; padding: 0 16px 10px; }
    .sp-quick-btn {
      font-size: 11px; padding: 5px 10px; border-radius: 20px; border: 1px solid #ff6900;
      color: #ff6900; background: white; cursor: pointer; transition: all 0.2s;
    }
    .sp-quick-btn:hover { background: #ff6900; color: white; }
  `;

  const styleEl = document.createElement('style');
  styleEl.textContent = styles;
  document.head.appendChild(styleEl);

  const btn = document.createElement('button');
  btn.id = 'storepilot-btn';
  btn.innerHTML = '📱';
  btn.title = 'StorePilot — помощник Xiaomi';
  document.body.appendChild(btn);

  const chat = document.createElement('div');
  chat.id = 'storepilot-chat';
  chat.innerHTML = `
    <div class="sp-header">
      <div class="sp-header-left">
        <div class="sp-avatar">📱</div>
        <div>
          <div class="sp-title">StorePilot</div>
          <div class="sp-subtitle">Помощник Xiaomi · Storelines.net</div>
        </div>
      </div>
      <button class="sp-close">✕</button>
    </div>
    <div class="sp-messages"></div>

    <div class="sp-input-area">
      <button class="sp-mic" title="Голосовой ввод">🎤</button>
      <textarea class="sp-input" placeholder="Напишите вопрос..." rows="1"></textarea>
      <button class="sp-send">➤</button>
    </div>
  `;
  document.body.appendChild(chat);

  const messages = chat.querySelector('.sp-messages');
  const input = chat.querySelector('.sp-input');
  const sendBtn = chat.querySelector('.sp-send');
  let history = [];
  let opened = false;

  function addMsg(role, text) {
    const div = document.createElement('div');
    div.className = `sp-msg ${role}`;
    const avatar = document.createElement('div');
    avatar.className = 'sp-msg-avatar';
    avatar.textContent = role === 'user' ? 'В' : '📱';
    const bubble = document.createElement('div');
    bubble.className = 'sp-bubble';
    bubble.innerHTML = parseMarkdown(text);
    div.appendChild(avatar);
    div.appendChild(bubble);
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
  }

  function showTyping() {
    const div = document.createElement('div');
    div.className = 'sp-msg bot';
    div.innerHTML = `<div class="sp-msg-avatar">📱</div><div class="sp-bubble sp-typing"><span></span><span></span><span></span></div>`;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
    return div;
  }

  async function send(text) {
    if (!text.trim() || sendBtn.disabled) return;
    addMsg('user', text);
    input.value = '';
    input.style.height = 'auto';
    sendBtn.disabled = true;
    history.push({ role: 'user', content: text });
    const typing = showTyping();
    try {
      const res = await fetch(`${WORKER_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: history })
      });
      const data = await res.json();
      typing.remove();
      const reply = data.response || 'Извините, произошла ошибка.';
      addMsg('bot', reply);
      history.push({ role: 'assistant', content: reply });
    } catch(e) {
      typing.remove();
      addMsg('bot', 'Ошибка соединения. Попробуйте позже.');
    }
    sendBtn.disabled = false;
  }

  // Открыть/закрыть
  btn.addEventListener('click', () => {
    chat.classList.toggle('open');
    if (!opened) {
      opened = true;
      addMsg('bot', 'Привет! Я StorePilot, помощник магазина Storelines.net 📱\n\nПомогу выбрать технику Xiaomi:\n\n📱 Смартфоны — Redmi, POCO, Xiaomi 14/15\n📟 Планшеты — Xiaomi Pad, Redmi Pad\n🎧 Наушники — Redmi Buds, колонки\n⌚ Часы — Xiaomi Watch, Redmi Watch\n📺 Телевизоры — Xiaomi TV, QLED\n🤖 Пылесосы — роботы-пылесосы\n🏠 Умный дом — роутеры, камеры\n🔋 Зарядки — PowerBank, кабели\n🛡️ Аксессуары — чехлы, стёкла\n\nНапишите что ищете — подберу лучший вариант! 🔥');
    }
  });

  chat.querySelector('.sp-close').addEventListener('click', () => {
    chat.classList.remove('open');
  });

  sendBtn.addEventListener('click', () => send(input.value));

  input.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send(input.value);
    }
  });

  input.addEventListener('input', () => {
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 80) + 'px';
  });

  // Микрофон
  const micBtn = chat.querySelector('.sp-mic');
  if (micBtn && ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window)) {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SR();
    recognition.lang = 'ru-RU';
    recognition.interimResults = false;
    recognition.onresult = (e) => {
      input.value = e.results[0][0].transcript;
      micBtn.classList.remove('listening');
      send(input.value);
    };
    recognition.onend = () => micBtn.classList.remove('listening');
    recognition.onerror = () => micBtn.classList.remove('listening');
    micBtn.addEventListener('click', () => {
      micBtn.classList.add('listening');
      recognition.start();
    });
  } else if (micBtn) {
    micBtn.style.display = 'none';
  }

})();
