/**
 * View: Contratos — CRUD com alerta de vencimento.
 */
const ContractsView = (() => {
    const PLANS = ['starter', 'pro', 'enterprise'];
    const STATUSES = ['active', 'trial', 'expired', 'cancelled'];

    function render(container, key) {
        container.innerHTML = `
      <div class="view-header flex justify-between" style="align-items:flex-end">
        <div><h2 class="view-title">Contratos</h2><p class="view-sub">Gestão de planos e vigências dos tenants</p></div>
        <button class="btn btn-primary btn-mono" id="btn-new-contract">⊕ NOVO CONTRATO</button>
      </div>
      <div id="contracts-alerts"></div>
      <div class="card" style="padding:0">
        <div class="table-wrap">
          <table>
            <thead><tr>
              <th>TENANT</th><th>PLANO</th><th>INÍCIO</th><th>VENCIMENTO</th><th>MSGS/MÊS</th><th>STATUS</th><th>AÇÕES</th>
            </tr></thead>
            <tbody id="contracts-tbody">
              <tr><td colspan="7" style="text-align:center;padding:32px;color:var(--steel-gray)">Carregando...</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    `;

        async function load() {
            const [data, err] = await apiFetch('/api/admin/contracts');
            const tbody = container.querySelector('#contracts-tbody');
            const alerts = container.querySelector('#contracts-alerts');
            if (err || !data) { tbody.innerHTML = `<tr><td colspan="7" style="padding:20px;color:var(--steel-gray);text-align:center">${err || 'Tabela não encontrada — execute migrations/init.sql'}</td></tr>`; return; }
            if (!data.contracts?.length) { tbody.innerHTML = `<tr><td colspan="7" style="padding:20px;color:var(--steel-gray);text-align:center">Nenhum contrato cadastrado.</td></tr>`; return; }

            // Expiry alerts
            const soon = data.contracts.filter(c => {
                if (!c.expires_at || c.status !== 'active') return false;
                return (new Date(c.expires_at) - new Date()) / 86400000 <= 30;
            });
            alerts.innerHTML = soon.length
                ? `<div class="alert-banner">⚠ ${soon.length} contrato(s) vencendo em até 30 dias: ${soon.map(c => c.client_name || c.tenant_id).join(', ')}</div>`
                : '';

            tbody.innerHTML = data.contracts.map(c => {
                const daysLeft = c.expires_at ? Math.ceil((new Date(c.expires_at) - new Date()) / 86400000) : null;
                const expStr = c.expires_at ? `${fmtDate(c.expires_at)} <span style="color:${daysLeft <= 30 ? 'var(--signal-orange)' : 'var(--steel-gray)'}"> (${daysLeft}d)</span>` : '—';
                return `
        <tr>
          <td class="td-mono text-orange">${c.tenant_id}<br><span style="color:var(--steel-gray);font-size:11px">${c.client_name || ''}</span></td>
          <td style="text-transform:capitalize;font-weight:600">${c.plan_type}</td>
          <td class="td-mono">${fmtDate(c.starts_at)}</td>
          <td class="td-mono">${expStr}</td>
          <td class="td-mono">${c.msg_limit?.toLocaleString('pt-BR') || '—'}</td>
          <td><span class="badge badge-${c.status}">${c.status.toUpperCase()}</span></td>
          <td>
            <div class="col-actions">
              <button class="btn btn-ghost btn-sm" data-action="edit" data-id="${c.id}">Editar</button>
              <button class="btn btn-ghost btn-sm" style="color:#DC2626;border-color:#DC2626" data-action="delete" data-id="${c.id}">Deletar</button>
            </div>
          </td>
        </tr>`;
            }).join('');

            tbody.querySelectorAll('[data-action]').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    const id = btn.dataset.id;
                    if (btn.dataset.action === 'delete') {
                        if (!confirm('Deletar este contrato?')) return;
                        const [, err] = await apiFetch(`/api/admin/contracts/${id}`, { method: 'DELETE' });
                        if (err) { toast(`Erro: ${err}`, false); return; }
                        toast('Contrato deletado'); load();
                    } else if (btn.dataset.action === 'edit') {
                        const c = data.contracts.find(x => String(x.id) === String(id));
                        openForm(c);
                    }
                });
            });
        }

        function openForm(existing = null) {
            const overlay = el('div', 'overlay');
            const c = existing || {};
            overlay.innerHTML = `
        <div class="drawer">
          <button class="drawer__close" id="close-drawer">✕</button>
          <div class="drawer__title">${existing ? 'Editar Contrato' : 'Novo Contrato'}</div>
          <div class="drawer__sub">${existing ? `#${existing.id}` : 'Vincular plano a um tenant'}</div>
          <div class="form-group">
            <label class="form-label">Tenant ID *</label>
            <input class="form-input" id="c-tenant" value="${c.tenant_id || ''}" ${existing ? 'disabled' : ''} placeholder="pref_nova_esperanca">
          </div>
          <div class="form-group">
            <label class="form-label">Tipo de Plano</label>
            <select class="form-input" id="c-plan">
              ${PLANS.map(p => `<option value="${p}" ${c.plan_type === p ? 'selected' : ''}>${p.charAt(0).toUpperCase() + p.slice(1)}</option>`).join('')}
            </select>
          </div>
          <div class="form-grid-2">
            <div class="form-group"><label class="form-label">Início</label><input class="form-input" id="c-start" type="date" value="${c.starts_at?.slice(0, 10) || ''}"></div>
            <div class="form-group"><label class="form-label">Vencimento</label><input class="form-input" id="c-end" type="date" value="${c.expires_at?.slice(0, 10) || ''}"></div>
          </div>
          <div class="form-group"><label class="form-label">Limite de Mensagens / Mês</label><input class="form-input" id="c-limit" type="number" value="${c.msg_limit || 10000}"></div>
          <div class="form-group">
            <label class="form-label">Status</label>
            <select class="form-input" id="c-status">
              ${STATUSES.map(s => `<option value="${s}" ${c.status === s ? 'selected' : ''}>${s.toUpperCase()}</option>`).join('')}
            </select>
          </div>
          <button class="btn btn-primary btn-mono btn-block btn-lg mt-16" id="btn-save-c">✓ SALVAR</button>
        </div>`;
            document.body.appendChild(overlay);
            overlay.querySelector('#close-drawer').onclick = () => overlay.remove();
            overlay.querySelector('#btn-save-c').onclick = async () => {
                const payload = {
                    tenant_id: overlay.querySelector('#c-tenant').value.trim(),
                    plan_type: overlay.querySelector('#c-plan').value,
                    starts_at: overlay.querySelector('#c-start').value,
                    expires_at: overlay.querySelector('#c-end').value || null,
                    msg_limit: parseInt(overlay.querySelector('#c-limit').value) || 10000,
                    status: overlay.querySelector('#c-status').value,
                };
                const url = existing ? `/api/admin/contracts/${existing.id}` : '/api/admin/contracts';
                const method = existing ? 'PUT' : 'POST';
                const [, err] = await apiFetch(url, { method, body: JSON.stringify(payload) });
                if (err) { toast(`Erro: ${err}`, false); return; }
                toast(existing ? 'Contrato atualizado!' : 'Contrato criado!');
                overlay.remove(); load();
            };
        }

        container.querySelector('#btn-new-contract').addEventListener('click', () => openForm());
        load();
    }

    return { render };
})();
