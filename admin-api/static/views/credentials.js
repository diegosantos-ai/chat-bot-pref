/**
 * View: Credenciais Meta — gerenciar page_id, access_token, app_secret por tenant.
 */
const CredentialsView = (() => {
    const FIELDS = [
        { key: 'page_id_facebook', label: 'Page ID — Facebook', sensitive: false },
        { key: 'app_secret_facebook', label: 'App Secret — Facebook', sensitive: true },
        { key: 'access_token_facebook', label: 'Access Token — Facebook', sensitive: true },
        { key: 'page_id_instagram', label: 'Page ID — Instagram', sensitive: false },
        { key: 'app_secret_instagram', label: 'App Secret — Instagram', sensitive: true },
        { key: 'access_token_instagram', label: 'Access Token — Instagram', sensitive: true },
        { key: 'webhook_verify_token', label: 'Webhook Verify Token', sensitive: true },
    ];

    function render(container, key) {
        container.innerHTML = `
      <div class="view-header">
        <h2 class="view-title">Credenciais Meta</h2>
        <p class="view-sub">Page IDs, Access Tokens e Webhooks por tenant</p>
      </div>
      <div class="card">
        <div class="card__title">SELECIONAR TENANT</div>
        <select class="form-input" id="cred-tenant-select" style="max-width:360px">
          <option value="">-- Selecione --</option>
        </select>
      </div>
      <div id="cred-form" style="display:none">
        <div class="card mt-16">
          <div class="card__title">FACEBOOK</div>
          <div class="form-grid-2" id="fb-fields"></div>
        </div>
        <div class="card mt-16">
          <div class="card__title">INSTAGRAM</div>
          <div class="form-grid-2" id="ig-fields"></div>
        </div>
        <div class="card mt-16">
          <div class="card__title">WEBHOOK</div>
          <div id="wh-fields"></div>
        </div>
        <div id="cred-msg" style="font-family:var(--font-mono);font-size:12px;margin-top:12px"></div>
        <button class="btn btn-primary btn-mono btn-block btn-lg mt-16" id="btn-save-creds">✓ SALVAR CREDENCIAIS</button>
      </div>
    `;

        // Load tenant list
        async function loadTenants() {
            const [data] = await apiFetch('/api/admin/tenants');
            const sel = container.querySelector('#cred-tenant-select');
            if (data?.tenants) {
                data.tenants.forEach(t => {
                    const opt = document.createElement('option');
                    opt.value = t.tenant_id;
                    opt.textContent = `${t.client_name || t.tenant_id} (${t.tenant_id})`;
                    sel.appendChild(opt);
                });
            }
        }

        function buildField(f, val = '') {
            return `
        <div class="form-group">
          <label class="form-label">${f.label}</label>
          <div class="input-wrap">
            <input id="cred-${f.key}" class="form-input" type="${f.sensitive ? 'password' : 'text'}"
              value="${val || ''}" placeholder="${f.sensitive ? '••••••••' : '—'}" autocomplete="off">
            ${f.sensitive ? `<button type="button" class="btn-toggle-pw" data-for="cred-${f.key}" title="Mostrar/ocultar">👁</button>` : ''}
          </div>
        </div>`;
        }

        async function loadCreds(tenantId) {
            const [data] = await apiFetch(`/api/admin/credentials/${tenantId}?masked=true`);
            const creds = data || {};

            const fb = container.querySelector('#fb-fields');
            const ig = container.querySelector('#ig-fields');
            const wh = container.querySelector('#wh-fields');

            fb.innerHTML = ['page_id_facebook', 'app_secret_facebook', 'access_token_facebook']
                .map(k => buildField(FIELDS.find(f => f.key === k), creds[k] || '')).join('');
            ig.innerHTML = ['page_id_instagram', 'app_secret_instagram', 'access_token_instagram']
                .map(k => buildField(FIELDS.find(f => f.key === k), creds[k] || '')).join('');
            wh.innerHTML = buildField(FIELDS.find(f => f.key === 'webhook_verify_token'), creds['webhook_verify_token'] || '');

            container.querySelector('#cred-form').style.display = '';

            // Toggle show/hide
            container.querySelectorAll('.btn-toggle-pw').forEach(btn => {
                btn.onclick = () => {
                    const inp = document.getElementById(btn.dataset.for);
                    inp.type = inp.type === 'password' ? 'text' : 'password';
                };
            });
        }

        container.querySelector('#cred-tenant-select').addEventListener('change', e => {
            if (e.target.value) loadCreds(e.target.value);
            else container.querySelector('#cred-form').style.display = 'none';
        });

        container.querySelector('#btn-save-creds').addEventListener('click', async () => {
            const tenantId = container.querySelector('#cred-tenant-select').value;
            if (!tenantId) return;
            const payload = {};
            FIELDS.forEach(f => {
                const inp = document.getElementById(`cred-${f.key}`);
                if (inp && inp.value.trim() && !inp.value.includes('*')) {
                    payload[f.key] = inp.value.trim();
                }
            });
            const msgEl = container.querySelector('#cred-msg');
            const btn = container.querySelector('#btn-save-creds');
            btn.disabled = true; btn.textContent = 'Salvando...';
            const [, err] = await apiFetch(`/api/admin/credentials/${tenantId}`, { method: 'PUT', body: JSON.stringify(payload) });
            btn.disabled = false; btn.textContent = '✓ SALVAR CREDENCIAIS';
            if (err) {
                msgEl.style.color = '#DC2626';
                msgEl.textContent = `⚠ Erro: ${err}`;
            } else {
                msgEl.style.color = '#059669';
                msgEl.textContent = '✓ Credenciais salvas com sucesso.';
                toast('Credenciais salvas!');
            }
        });

        loadTenants();
    }

    return { render };
})();
