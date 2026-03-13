/**
 * View: Configuração do Tenant
 * GET/PUT /api/panel/config
 */
const ConfigView = (() => {
    const FIELDS = [
        { key: 'bot_name', label: 'Nome do Bot', placeholder: 'Ex: EsperBot' },
        { key: 'client_name', label: 'Nome do Cliente', placeholder: 'Ex: Prefeitura de Nova Esperança' },
        { key: 'contact_phone', label: 'Telefone de Contato', placeholder: '(00) 0000-0000' },
        { key: 'contact_address', label: 'Endereço', placeholder: 'Rua das Acácias, 100' },
        { key: 'support_email', label: 'E-mail de Suporte', placeholder: 'suporte@prefeitura.gov.br' },
        { key: 'fallback_url', label: 'URL de Fallback', placeholder: 'https://prefeitura.gov.br/atendimento' },
    ];

    function render(container, tenantId) {
        const fieldsHtml = FIELDS.map((f, i) => `
      <div class="form-group">
        <label class="form-label" for="cfg-${f.key}">${f.label}</label>
        <input id="cfg-${f.key}" class="form-input" type="text"
          name="${f.key}" placeholder="${f.placeholder}" autocomplete="off">
      </div>
    `).join('');

        container.innerHTML = `
      <div class="view-header">
        <h2 class="view-title">Configuração do Tenant</h2>
        <p class="view-sub">Perfil e variáveis do bot — tenant: <span class="text-orange">${tenantId}</span></p>
      </div>

      <div class="card">
        <div class="card__title">PERFIL DO BOT</div>
        <div id="cfg-msg" style="display:none;margin-bottom:16px"></div>
        <div class="form-grid">${fieldsHtml}</div>
        <button class="btn btn-primary btn-mono btn-block btn-lg mt-20" id="btn-save-config">
          SALVAR CONFIGURAÇÃO
        </button>
      </div>
    `;

        async function loadConfig() {
            const [data, err] = await apiFetch(`/api/panel/config?tenant_id=${encodeURIComponent(tenantId)}`);
            if (err || !data) return;
            FIELDS.forEach(f => {
                const inp = container.querySelector(`#cfg-${f.key}`);
                if (inp && data[f.key] !== undefined) inp.value = data[f.key] || '';
            });
        }

        function showMsg(text, isError = false) {
            const el = container.querySelector('#cfg-msg');
            el.style.display = 'block';
            el.style.color = isError ? '#DC2626' : '#059669';
            el.style.fontFamily = 'var(--font-mono)';
            el.style.fontSize = '12px';
            el.textContent = text;
            setTimeout(() => { el.style.display = 'none'; }, 4000);
        }

        container.querySelector('#btn-save-config').addEventListener('click', async () => {
            const btn = container.querySelector('#btn-save-config');
            btn.disabled = true;
            btn.textContent = 'SALVANDO...';

            const payload = {};
            FIELDS.forEach(f => {
                const inp = container.querySelector(`#cfg-${f.key}`);
                payload[f.key] = inp ? inp.value.trim() : '';
            });

            const [data, err] = await apiFetch(`/api/panel/config?tenant_id=${encodeURIComponent(tenantId)}`, {
                method: 'PUT',
                body: JSON.stringify(payload),
            });

            btn.disabled = false;
            btn.textContent = 'SALVAR CONFIGURAÇÃO';

            if (err) {
                showMsg(`⚠️ Erro: ${err}`, true);
            } else {
                showMsg('✓ Configuração salva com sucesso.');
            }
        });

        loadConfig();
    }

    return { render };
})();
