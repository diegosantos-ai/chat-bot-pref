/**
 * View: Logs de Conversa
 * Lists audit_logs with pagination and row expand.
 */
const LogsView = (() => {
    let currentPage = 1;
    const perPage = 25;

    function render(container, tenantId) {
        container.innerHTML = `
      <div class="view-header flex justify-between" style="align-items:flex-end">
        <div>
          <h2 class="view-title">Logs de Conversa</h2>
          <p class="view-sub">Auditoria de mensagens por tenant</p>
        </div>
        <div class="flex gap-8">
          <select class="form-input" id="filter-channel" style="width:140px">
            <option value="">Todos os canais</option>
            <option value="web_widget">Web</option>
            <option value="instagram_dm">Instagram</option>
            <option value="facebook_dm">Facebook</option>
          </select>
          <button class="btn btn-ghost" id="btn-refresh">↻ Atualizar</button>
        </div>
      </div>

      <div class="card" style="padding:0">
        <div id="logs-table-wrap" class="table-wrap" style="padding:0 24px">
          <table>
            <thead>
              <tr>
                <th>DATA/HORA</th>
                <th>SESSION ID</th>
                <th>CANAL</th>
                <th>MENSAGEM</th>
                <th>STATUS</th>
              </tr>
            </thead>
            <tbody id="logs-tbody">
              <tr><td colspan="5" style="text-align:center;padding:32px;color:var(--steel-gray)">Carregando...</td></tr>
            </tbody>
          </table>
        </div>
        <div id="logs-pagination" class="pagination" style="padding:12px 24px"></div>
      </div>

      <div id="log-detail" class="card mt-16" style="display:none">
        <div class="card__title">DETALHE DA CONVERSA</div>
        <div id="log-detail-content"></div>
      </div>
    `;

        async function load(page = 1) {
            currentPage = page;
            const channel = container.querySelector('#filter-channel').value;
            let url = `/api/panel/logs?tenant_id=${encodeURIComponent(tenantId)}&page=${page}&per_page=${perPage}`;
            if (channel) url += `&channel=${channel}`;

            const [data, err] = await apiFetch(url);
            const tbody = container.querySelector('#logs-tbody');
            const pagEl = container.querySelector('#logs-pagination');

            if (err || !data) {
                tbody.innerHTML = `<tr><td colspan="5" style="color:var(--steel-gray);padding:20px;text-align:center">Nenhum log disponível ainda.</td></tr>`;
                pagEl.innerHTML = '';
                return;
            }

            if (!data.items.length) {
                tbody.innerHTML = `<tr><td colspan="5" style="color:var(--steel-gray);padding:20px;text-align:center">Nenhuma conversa encontrada.</td></tr>`;
                pagEl.innerHTML = '';
                return;
            }

            tbody.innerHTML = data.items.map(row => `
        <tr data-id="${row.id || ''}" data-msg="${encodeURIComponent(row.user_message || '')}" data-resp="${encodeURIComponent(row.bot_response || '')}" data-intent="${row.intent || ''}">
          <td class="td-mono">${fmtDate(row.created_at)}</td>
          <td class="td-mono" style="color:var(--steel-gray);font-size:11px">${(row.session_id || '').slice(0, 12)}…</td>
          <td><span class="badge badge-idle">${row.channel || '—'}</span></td>
          <td style="max-width:320px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${row.user_message || '—'}</td>
          <td><span class="badge ${row.decision === 'RESOLVED' ? 'badge-done' : 'badge-idle'}">${row.status || 'OK'}</span></td>
        </tr>
      `).join('');

            // Pagination
            pagEl.innerHTML = '';
            const pages = data.pages || 1;
            if (pages > 1) {
                if (page > 1) pagEl.innerHTML += `<button class="pag-btn" data-page="${page - 1}">‹ Anterior</button>`;
                for (let p = Math.max(1, page - 2); p <= Math.min(pages, page + 2); p++) {
                    pagEl.innerHTML += `<button class="pag-btn ${p === page ? 'active' : ''}" data-page="${p}">${p}</button>`;
                }
                if (page < pages) pagEl.innerHTML += `<button class="pag-btn" data-page="${page + 1}">Próximo ›</button>`;
            }

            pagEl.querySelectorAll('.pag-btn[data-page]').forEach(btn => {
                btn.addEventListener('click', () => load(Number(btn.dataset.page)));
            });

            // Row expand
            tbody.querySelectorAll('tr').forEach(tr => {
                tr.addEventListener('click', () => {
                    const msg = decodeURIComponent(tr.dataset.msg || '');
                    const resp = decodeURIComponent(tr.dataset.resp || '');
                    const intent = tr.dataset.intent;
                    const detail = container.querySelector('#log-detail');
                    const dc = container.querySelector('#log-detail-content');
                    detail.style.display = 'block';
                    dc.innerHTML = `
            <div class="form-group">
              <label class="form-label">Usuário</label>
              <div class="terminal" style="min-height:60px;color:var(--tech-white)">${msg || '—'}</div>
            </div>
            <div class="form-group mt-8">
              <label class="form-label">Bot</label>
              <div class="terminal" style="min-height:60px;color:#4ADE80">${resp || '—'}</div>
            </div>
            <span class="text-mono" style="color:var(--steel-gray)">Intent: ${intent || '—'}</span>
          `;
                    detail.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                });
            });
        }

        container.querySelector('#btn-refresh').addEventListener('click', () => load(currentPage));
        container.querySelector('#filter-channel').addEventListener('change', () => load(1));
        load(1);
    }

    return { render };
})();
