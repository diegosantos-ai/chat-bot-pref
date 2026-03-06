/**
 * View: Logs & Auditoria — cross-tenant com filtros avançados e export CSV.
 */
const LogsAdminView = (() => {
    let currentPage = 1;
    const PER_PAGE = 50;

    function render(container, key) {
        container.innerHTML = `
      <div class="view-header"><h2 class="view-title">Logs & Auditoria</h2><p class="view-sub">Auditoria cross-tenant de conversas</p></div>
      <div class="card">
        <div class="form-grid-3" style="align-items:flex-end">
          <div class="form-group"><label class="form-label">Tenant</label>
            <select class="form-input" id="f-tenant"><option value="">Todos</option></select></div>
          <div class="form-group"><label class="form-label">Canal</label>
            <select class="form-input" id="f-channel">
              <option value="">Todos</option>
              <option value="web_widget">Web</option>
              <option value="instagram_dm">Instagram</option>
              <option value="facebook_dm">Facebook</option>
            </select></div>
          <div class="form-group"><label class="form-label">Intent (contém)</label>
            <input class="form-input" id="f-intent" placeholder="ex: horario"></div>
          <div class="form-group"><label class="form-label">De</label>
            <input class="form-input" id="f-from" type="datetime-local"></div>
          <div class="form-group"><label class="form-label">Até</label>
            <input class="form-input" id="f-to" type="datetime-local"></div>
          <div class="form-group" style="display:flex;gap:8px;align-items:flex-end">
            <button class="btn btn-primary" id="btn-filter" style="flex:1">Filtrar</button>
            <button class="btn btn-ghost" id="btn-export" title="Exportar CSV">⬇ CSV</button>
          </div>
        </div>
      </div>
      <div class="card mt-16" style="padding:0">
        <div class="table-wrap">
          <table><thead><tr>
            <th>DATA</th><th>TENANT</th><th>CANAL</th><th>MENSAGEM</th><th>INTENT</th><th>STATUS</th>
          </tr></thead>
          <tbody id="logs-tbody">
            <tr><td colspan="6" style="text-align:center;padding:32px;color:var(--steel-gray)">Clique em "Filtrar" para carregar os logs.</td></tr>
          </tbody></table>
        </div>
        <div id="logs-pagination" class="pagination" style="padding:12px 24px"></div>
      </div>
      <div id="log-detail" class="card mt-16" style="display:none">
        <div class="card__title">DETALHE DA CONVERSA</div>
        <div id="log-detail-content"></div>
      </div>
    `;

        async function loadTenants() {
            const [data] = await apiFetch('/api/admin/tenants');
            const sel = container.querySelector('#f-tenant');
            data?.tenants?.forEach(t => {
                const o = el('option', '', t.client_name || t.tenant_id); o.value = t.tenant_id; sel.appendChild(o);
            });
        }

        function buildUrl(page) {
            const tid = container.querySelector('#f-tenant').value;
            const ch = container.querySelector('#f-channel').value;
            const int = container.querySelector('#f-intent').value;
            const from = container.querySelector('#f-from').value;
            const to = container.querySelector('#f-to').value;
            const params = new URLSearchParams({ page, per_page: PER_PAGE });
            if (tid) params.set('tenant_id', tid);
            if (ch) params.set('channel', ch);
            if (int) params.set('intent', int);
            if (from) params.set('date_from', new Date(from).toISOString());
            if (to) params.set('date_to', new Date(to).toISOString());
            return `/api/admin/logs?${params}`;
        }

        async function load(page = 1) {
            currentPage = page;
            const [data] = await apiFetch(buildUrl(page));
            const tbody = container.querySelector('#logs-tbody');
            const pagEl = container.querySelector('#logs-pagination');
            if (!data?.items?.length) {
                tbody.innerHTML = `<tr><td colspan="6" style="padding:20px;color:var(--steel-gray);text-align:center">Nenhum log encontrado com esses filtros.</td></tr>`;
                pagEl.innerHTML = ''; return;
            }
            tbody.innerHTML = data.items.map(r => `
        <tr data-msg="${encodeURIComponent(r.user_message || '')}" data-resp="${encodeURIComponent(r.bot_response || '')}" data-intent="${r.intent || ''}">
          <td class="td-mono">${fmtDate(r.created_at)}</td>
          <td class="td-mono text-orange">${r.tenant_id}</td>
          <td><span class="badge badge-idle">${r.channel || '—'}</span></td>
          <td style="max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${r.user_message || '—'}</td>
          <td class="td-mono" style="font-size:11px">${r.intent || '—'}</td>
          <td><span class="badge ${r.status === 'OK' ? 'badge-done' : 'badge-idle'}">${r.status || '—'}</span></td>
        </tr>`).join('');

            // Pagination
            const pages = data.pages || 1;
            pagEl.innerHTML = '';
            if (pages > 1) {
                if (page > 1) pagEl.innerHTML += `<button class="pag-btn" data-p="${page - 1}">‹</button>`;
                for (let p = Math.max(1, page - 2); p <= Math.min(pages, page + 2); p++)
                    pagEl.innerHTML += `<button class="pag-btn ${p === page ? 'active' : ''}" data-p="${p}">${p}</button>`;
                if (page < pages) pagEl.innerHTML += `<button class="pag-btn" data-p="${page + 1}">›</button>`;
                pagEl.querySelectorAll('[data-p]').forEach(b => b.addEventListener('click', () => load(Number(b.dataset.p))));
            }

            // Row expand
            tbody.querySelectorAll('tr').forEach(tr => {
                tr.addEventListener('click', () => {
                    const msg = decodeURIComponent(tr.dataset.msg || '');
                    const resp = decodeURIComponent(tr.dataset.resp || '');
                    const detail = container.querySelector('#log-detail');
                    detail.style.display = '';
                    container.querySelector('#log-detail-content').innerHTML = `
            <div class="form-group"><label class="form-label">Usuário</label>
              <div class="terminal" style="min-height:60px;color:var(--tech-white)">${msg || '—'}</div></div>
            <div class="form-group mt-8"><label class="form-label">Bot</label>
              <div class="terminal" style="min-height:60px;color:#4ADE80">${resp || '—'}</div></div>
            <span class="text-mono text-sm">Intent: ${tr.dataset.intent || '—'}</span>`;
                    detail.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                });
            });
        }

        container.querySelector('#btn-filter').addEventListener('click', () => load(1));
        container.querySelector('#btn-export').addEventListener('click', async () => {
            const tid = container.querySelector('#f-tenant').value;
            const ch = container.querySelector('#f-channel').value;
            const from = container.querySelector('#f-from').value;
            const to = container.querySelector('#f-to').value;
            const params = new URLSearchParams();
            if (tid) params.set('tenant_id', tid);
            if (ch) params.set('channel', ch);
            if (from) params.set('date_from', new Date(from).toISOString());
            if (to) params.set('date_to', new Date(to).toISOString());
            const adminKey3 = localStorage.getItem('nexo_admin_key') || '';
            const res = await fetch(`/api/admin/logs/export?${params}`, { headers: { 'X-Admin-Key': adminKey3 } });
            if (!res.ok) { toast('Erro ao exportar CSV', false); return; }
            const blob = await res.blob();
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = 'logs_export.csv'; a.click();
        });

        loadTenants();
    }

    return { render };
})();
