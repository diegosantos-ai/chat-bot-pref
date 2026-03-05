/**
 * View: Chat Test
 * Sends messages to POST /api/chat and renders conversation bubbles.
 */
const ChatView = (() => {
    let sessionId = crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2);

    function render(container, tenantId) {
        container.innerHTML = `
      <div class="view-header">
        <h2 class="view-title">Chat Test</h2>
        <p class="view-sub">Simule conversas com o bot do tenant selecionado</p>
      </div>

      <div class="card">
        <div class="card__title">Sessão: <span id="chat-session" class="text-mono">${sessionId}</span>
          <button class="btn btn-ghost" id="btn-new-session" style="float:right;padding:2px 10px;font-size:11px;">
            Nova sessão
          </button>
        </div>

        <div class="chat-area" id="chat-area">
          <div class="chat-msg bot">
            <div class="chat-bubble">Olá! Sou o assistente da sua prefeitura. Como posso ajudar?</div>
            <span class="chat-meta">bot · agora</span>
          </div>
        </div>

        <div class="chat-input-row mt-16">
          <input id="chat-input" class="form-input" type="text"
            placeholder="Digite uma pergunta..."
            autocomplete="off" aria-label="Mensagem">
          <button class="btn btn-primary btn-mono" id="btn-send">Enviar ▶</button>
        </div>
      </div>
    `;

        const area = container.querySelector('#chat-area');
        const input = container.querySelector('#chat-input');
        const btnSend = container.querySelector('#btn-send');

        function scrollBottom() { area.scrollTop = area.scrollHeight; }

        function addBubble(text, role) {
            const now = new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
            const wrap = el('div', `chat-msg ${role}`);
            wrap.innerHTML = `<div class="chat-bubble">${text}</div><span class="chat-meta">${role} · ${now}</span>`;
            area.appendChild(wrap);
            scrollBottom();
            return wrap;
        }

        function showTyping() {
            const wrap = el('div', 'chat-msg bot');
            wrap.id = 'typing-indicator';
            wrap.innerHTML = '<div class="chat-typing"><span></span><span></span><span></span></div>';
            area.appendChild(wrap);
            scrollBottom();
        }
        function removeTyping() {
            const t = container.querySelector('#typing-indicator');
            if (t) t.remove();
        }

        async function sendMessage() {
            const text = input.value.trim();
            if (!text) return;
            input.value = '';
            addBubble(text, 'user');
            showTyping();
            btnSend.disabled = true;

            const [data, err] = await apiFetch('/api/chat', {
                method: 'POST',
                body: JSON.stringify({
                    session_id: sessionId,
                    message: text,
                    channel: 'web_widget',
                    surface_type: 'INBOX',
                }),
            });

            removeTyping();
            btnSend.disabled = false;

            if (err) {
                addBubble(`⚠️ Erro: ${err}`, 'bot');
            } else {
                addBubble(data.message || data.resposta || JSON.stringify(data), 'bot');
            }
        }

        btnSend.addEventListener('click', sendMessage);
        input.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) sendMessage(); });

        container.querySelector('#btn-new-session').addEventListener('click', () => {
            sessionId = crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2);
            container.querySelector('#chat-session').textContent = sessionId;
            area.innerHTML = `<div class="chat-msg bot">
        <div class="chat-bubble">Nova sessão iniciada. Como posso ajudar?</div>
        <span class="chat-meta">bot · agora</span>
      </div>`;
        });

        input.focus();
    }

    return { render };
})();
