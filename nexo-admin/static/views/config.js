/**
 * View: Sistema — versão, status geral, admin key info.
 */
const ConfigAdminView = (() => {
    function render(container, key) {
        container.innerHTML = `
      <div class="view-header">
        <h2 class="view-title">Sistema</h2>
        <p class="view-sub">Informações do ambiente e configurações globais</p>
      </div>
      <div class="card">
        <div class="card__title">STATUS GERAL</div>
        <div id="sys-info"><p style="color:var(--steel-gray);font-size:13px">Carregando...</p></div>
      </div>
      <div class="card mt-16">
        <div class="card__title">SESSÃO ADMIN</div>
        <div class="form-group">
          <label class="form-label">Admin API Key (armazenada localmente)</label>
          <div class="input-wrap">
            <input type="password" class="form-input" id="session-key" value="${localStorage.getItem('nexo_admin_key') || ''}" readonly>
            <button type="button" class="btn-toggle-pw" data-for="session-key" title="Mostrar/ocultar">👁</button>
          </div>
        </div>
        <button class="btn btn-ghost btn-sm" id="btn-clear-key" style="color:#DC2626;border-color:#DC2626;margin-top:4px">
          Limpar sessão (logout)
        </button>
      </div>
    `;

        async function loadSysInfo() {
            const [data] = await apiFetch('/api/admin/system');
            const el2 = container.querySelector('#sys-info');
            if (!data) { el2.innerHTML = '<p style="color:#DC2626;font-size:13px">Falha ao carregar — verifique a conexão com o banco.</p>'; return; }
            el2.innerHTML = `
        <div class="table-wrap"><table>
          <tbody>
            <tr><td class="td-mono">API Version</td><td class="fw-600">${data.api_version}</td></tr>
            <tr><td class="td-mono">Python</td><td>${data.python_version}</td></tr>
            <tr><td class="td-mono">Tenants Ativos</td><td class="fw-600 text-orange">${data.tenants_active}</td></tr>
            <tr><td class="td-mono">Contratos Ativos</td><td class="fw-600">${data.contracts_active}</td></tr>
            <tr><td class="td-mono">Admin Key (hint)</td><td class="td-mono">${data.admin_key_hint}</td></tr>
            <tr><td class="td-mono">Database</td><td class="td-mono" style="font-size:11px">${data.database_url_hint}</td></tr>
          </tbody>
        </table></div>`;
        }

        // Toggle show/hide for key
        container.querySelector('.btn-toggle-pw').onclick = () => {
            const inp = document.getElementById('session-key');
            inp.type = inp.type === 'password' ? 'text' : 'password';
        };

        container.querySelector('#btn-clear-key').addEventListener('click', () => {
            if (confirm('Limpar sessão e sair do admin?')) {
                localStorage.removeItem('nexo_admin_key');
                location.reload();
            }
        });

        loadSysInfo();
    }

    return { render };
})();
