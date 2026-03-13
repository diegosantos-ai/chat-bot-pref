/**
 * View: Jobs Noturnos — histórico de execuções ETL com alertas.
 */
const JobsView = (() => {
    function render(container, key) {
        container.innerHTML = `
      <div class="view-header flex justify-between" style="align-items:flex-end">
        <div><h2 class="view-title">Jobs Noturnos</h2><p class="view-sub">Histórico de execuções do crawler de RAG</p></div>
        <div class="flex gap-8 flex-center">
          <select class="form-input" id="jobs-tenant-filter" style="width:200px">
            <option value="">Todos os tenants</option>
          </select>
          <button class="btn btn-ghost" id="btn-refresh-jobs">↻ Atualizar</button>
        </div>
      </div>
      <div id="jobs-alert" style="display:none" class="alert-banner"></div>
      <div class="card" style="padding:0">
        <div class="table-wrap">
          <table>
            <thead><tr>
              <th>DATA</th><th>TENANT</th><th>STATUS</th><th>DOCS</th><th>DURAÇÃO</th><th>AÇÃO</th>
            </tr></thead>
            <tbody id="jobs-tbody">
              <tr><td colspan="6" style="text-align:center;padding:32px;color:var(--steel-gray)">Carregando...</td></tr>
            </tbody>
          </table>
        </div>
      </div>
      <div id="job-log-detail" class="card mt-16" style="display:none">
        <div class="card__title">LOG DA EXECUÇÃO</div>
        <div class="terminal" id="job-log-content">—</div>
      </div>
    `;

        async function loadTenants() {
            const [data] = await apiFetch('/api/admin/tenants');
            const sel = container.querySelector('#jobs-tenant-filter');
            data?.tenants?.forEach(t => {
                const o = el('option', '', t.client_name || t.tenant_id);
                o.value = t.tenant_id; sel.appendChild(o);
            });
        }

        async function load() {
            const tid = container.querySelector('#jobs-tenant-filter').value;
            const url = tid ? `/api/admin/rag/jobs?tenant_id=${tid}` : '/api/admin/rag/jobs';
            const [data] = await apiFetch(url);
            const tbody = container.querySelector('#jobs-tbody');
            const alertEl = container.querySelector('#jobs-alert');

            if (!data?.jobs?.length) {
                tbody.innerHTML = `<tr><td colspan="6" style="padding:20px;color:var(--steel-gray);text-align:center">Nenhuma execução registrada ainda. Execute a migration e dispare um ETL.</td></tr>`;
                alertEl.style.display = 'none';
                return;
            }

            // Alert: any ERROR in last 24h
            const dayAgo = new Date(Date.now() - 86400000);
            const failures = data.jobs.filter(j => j.status === 'ERROR' && new Date(j.started_at) > dayAgo);
            if (failures.length) {
                alertEl.style.display = '';
                alertEl.textContent = `⚠ ${failures.length} job(s) com ERRO nas últimas 24h — verifique os logs abaixo.`;
            } else {
                alertEl.style.display = 'none';
            }

            tbody.innerHTML = data.jobs.map(j => {
                const started = new Date(j.started_at);
                const finished = j.finished_at ? new Date(j.finished_at) : null;
                const dur = finished ? `${Math.round((finished - started) / 1000)}s` : '—';
                return `
          <tr data-log="${encodeURIComponent(j.log_output || '')}">
            <td class="td-mono">${fmtDate(j.started_at)}</td>
            <td class="td-mono text-orange">${j.tenant_id || '<em>todos</em>'}</td>
            <td><span class="badge badge-${j.status?.toLowerCase()}">${j.status}</span></td>
            <td class="td-mono">${j.docs_processed ?? '—'}</td>
            <td class="td-mono">${dur}</td>
            <td><button class="btn btn-ghost btn-sm" data-view-log="${encodeURIComponent(j.log_output || '')}">Ver Log</button></td>
          </tr>`;
            }).join('');

            tbody.querySelectorAll('[data-view-log]').forEach(btn => {
                btn.addEventListener('click', e => {
                    e.stopPropagation();
                    const logContent = decodeURIComponent(btn.dataset.viewLog);
                    const panel = container.querySelector('#job-log-detail');
                    container.querySelector('#job-log-content').textContent = logContent || 'Nenhum log registrado.';
                    panel.style.display = '';
                    panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                });
            });
        }

        container.querySelector('#btn-refresh-jobs').addEventListener('click', load);
        container.querySelector('#jobs-tenant-filter').addEventListener('change', load);
        loadTenants().then(load);
    }

    return { render };
})();
