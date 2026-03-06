/**
 * View: Tenants — Wizard 3-step creation + CRUD table.
 */
const TenantsView = (() => {
    function render(container, key) {
        container.innerHTML = `
      <div class="view-header flex justify-between" style="align-items:flex-end">
        <div><h2 class="view-title">Tenants</h2><p class="view-sub">Gestão de tenants cadastrados</p></div>
        <button class="btn btn-primary btn-mono" id="btn-new-tenant">⊕ NOVO TENANT</button>
      </div>
      <div class="card" style="padding:0">
        <div class="table-wrap" style="padding:0 0">
          <table>
            <thead><tr>
              <th>TENANT ID</th><th>CLIENTE</th><th>BOT NAME</th><th>STATUS</th><th>CRIADO</th><th>AÇÕES</th>
            </tr></thead>
            <tbody id="tenants-tbody">
              <tr><td colspan="6" style="text-align:center;padding:32px;color:var(--steel-gray)">Carregando...</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    `;

        async function load() {
            const [data, err] = await apiFetch('/api/admin/tenants');
            const tbody = container.querySelector('#tenants-tbody');
            if (err || !data) { tbody.innerHTML = `<tr><td colspan="6" style="color:var(--steel-gray);padding:20px;text-align:center">Erro ao carregar: ${err}</td></tr>`; return; }
            if (!data.tenants?.length) { tbody.innerHTML = `<tr><td colspan="6" style="color:var(--steel-gray);padding:20px;text-align:center">Nenhum tenant cadastrado.</td></tr>`; return; }
            tbody.innerHTML = data.tenants.map(t => `
        <tr>
          <td class="td-mono text-orange">${t.tenant_id}</td>
          <td style="font-weight:600">${t.client_name || '—'}</td>
          <td class="td-mono">${t.bot_name || '—'}</td>
          <td><span class="badge badge-${t.is_active ? 'active' : 'offline'}">${t.is_active ? 'ATIVO' : 'INATIVO'}</span></td>
          <td class="td-mono">${fmtDate(t.created_at)}</td>
          <td>
            <div class="col-actions">
              <button class="btn btn-ghost btn-sm" data-action="toggle" data-id="${t.tenant_id}" data-active="${t.is_active}">${t.is_active ? 'Desativar' : 'Ativar'}</button>
              <button class="btn btn-ghost btn-sm" data-action="edit" data-id="${t.tenant_id}">Editar</button>
              <button class="btn btn-ghost btn-sm" style="color:#DC2626;border-color:#DC2626" data-action="delete" data-id="${t.tenant_id}">Deletar</button>
            </div>
          </td>
        </tr>
      `).join('');

            tbody.querySelectorAll('[data-action]').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    const id = btn.dataset.id;
                    if (btn.dataset.action === 'delete') {
                        if (!confirm(`Deletar tenant "${id}"? Esta ação é irreversível.`)) return;
                        const [, err] = await apiFetch(`/api/admin/tenants/${id}`, { method: 'DELETE' });
                        if (err) { toast(`Erro: ${err}`, false); return; }
                        toast(`Tenant ${id} deletado`); load();
                    } else if (btn.dataset.action === 'toggle') {
                        const isActive = btn.dataset.active === 'true';
                        const [, err] = await apiFetch(`/api/admin/tenants/${id}`, { method: 'PUT', body: JSON.stringify({ is_active: !isActive }) });
                        if (err) { toast(`Erro: ${err}`, false); return; }
                        toast(`Tenant ${isActive ? 'desativado' : 'ativado'}`); load();
                    } else if (btn.dataset.action === 'edit') {
                        openWizard(id, data.tenants.find(t => t.tenant_id === id));
                    }
                });
            });
        }

        // ---- Wizard ----
        function openWizard(editId = null, existing = null) {
            let step = 1;
            const formData = { ...existing };

            const overlay = el('div', 'overlay');
            overlay.innerHTML = `
        <div class="drawer">
          <button class="drawer__close" id="close-drawer">✕</button>
          <div class="drawer__title">${editId ? 'Editar Tenant' : 'Novo Tenant'}</div>
          <div class="drawer__sub">${editId ? editId : 'Preencha os dados em 3 etapas'}</div>
          <div class="wizard-steps">
            <div class="wizard-step active" data-step="1">1 — Identificação</div>
            <div class="wizard-step" data-step="2">2 — Contatos</div>
            <div class="wizard-step" data-step="3">3 — Confirmar</div>
          </div>
          <div id="wizard-body"></div>
        </div>`;
            document.body.appendChild(overlay);
            overlay.querySelector('#close-drawer').onclick = () => overlay.remove();

            function renderStep() {
                const body = overlay.querySelector('#wizard-body');
                const steps = overlay.querySelectorAll('.wizard-step');
                steps.forEach((s, i) => {
                    s.className = 'wizard-step' + (i + 1 < step ? ' done' : i + 1 === step ? ' active' : '');
                });

                if (step === 1) {
                    body.innerHTML = `
            <div class="form-group"><label class="form-label">Tenant ID *</label>
              <input class="form-input" id="f-tid" value="${formData.tenant_id || ''}" ${editId ? 'disabled' : ''} placeholder="ex: pref_nova_esperanca"></div>
            <div class="form-group"><label class="form-label">Nome do Cliente *</label>
              <input class="form-input" id="f-client" value="${formData.client_name || ''}" placeholder="Prefeitura de Nova Esperança"></div>
            <div class="form-group"><label class="form-label">Nome do Bot *</label>
              <input class="form-input" id="f-bot" value="${formData.bot_name || ''}" placeholder="EsperBot"></div>
            <button class="btn btn-primary btn-block mt-16" id="btn-next1">Próximo →</button>`;
                    body.querySelector('#btn-next1').onclick = () => {
                        formData.tenant_id = body.querySelector('#f-tid').value.trim();
                        formData.client_name = body.querySelector('#f-client').value.trim();
                        formData.bot_name = body.querySelector('#f-bot').value.trim();
                        if (!formData.tenant_id || !formData.client_name || !formData.bot_name) { toast('Preencha todos os campos obrigatórios', false); return; }
                        step = 2; renderStep();
                    };
                } else if (step === 2) {
                    body.innerHTML = `
            <div class="form-group"><label class="form-label">Telefone</label><input class="form-input" id="f-phone" value="${formData.contact_phone || ''}" placeholder="(00) 0000-0000"></div>
            <div class="form-group"><label class="form-label">Endereço</label><input class="form-input" id="f-addr" value="${formData.contact_address || ''}"></div>
            <div class="form-group"><label class="form-label">E-mail</label><input class="form-input" id="f-email" value="${formData.support_email || ''}" placeholder="suporte@pref.gov.br"></div>
            <div class="form-group"><label class="form-label">Fallback URL</label><input class="form-input" id="f-url" value="${formData.fallback_url || ''}" placeholder="https://pref.gov.br/atendimento"></div>
            <div class="flex gap-8 mt-16">
              <button class="btn btn-ghost" id="btn-back2">← Voltar</button>
              <button class="btn btn-primary" style="flex:1" id="btn-next2">Próximo →</button>
            </div>`;
                    body.querySelector('#btn-back2').onclick = () => { step = 1; renderStep(); };
                    body.querySelector('#btn-next2').onclick = () => {
                        formData.contact_phone = body.querySelector('#f-phone').value.trim();
                        formData.contact_address = body.querySelector('#f-addr').value.trim();
                        formData.support_email = body.querySelector('#f-email').value.trim();
                        formData.fallback_url = body.querySelector('#f-url').value.trim();
                        step = 3; renderStep();
                    };
                } else {
                    body.innerHTML = `
            <div class="terminal" style="min-height:auto;color:var(--tech-white);font-size:11px">
${JSON.stringify(formData, null, 2)}</div>
            <div class="flex gap-8 mt-16">
              <button class="btn btn-ghost" id="btn-back3">← Voltar</button>
              <button class="btn btn-primary btn-mono" style="flex:1" id="btn-save">✓ SALVAR</button>
            </div>`;
                    body.querySelector('#btn-back3').onclick = () => { step = 2; renderStep(); };
                    body.querySelector('#btn-save').onclick = async () => {
                        const btn = body.querySelector('#btn-save');
                        btn.disabled = true; btn.textContent = 'Salvando...';
                        const url = editId ? `/api/admin/tenants/${editId}` : '/api/admin/tenants';
                        const method = editId ? 'PUT' : 'POST';
                        const [, err] = await apiFetch(url, { method, body: JSON.stringify(formData) });
                        if (err) { toast(`Erro: ${err}`, false); btn.disabled = false; btn.textContent = '✓ SALVAR'; return; }
                        toast(editId ? 'Tenant atualizado!' : 'Tenant criado!');
                        overlay.remove(); load();
                    };
                }
            }
            renderStep();
        }

        container.querySelector('#btn-new-tenant').addEventListener('click', () => openWizard());
        load();
    }

    return { render };
})();
