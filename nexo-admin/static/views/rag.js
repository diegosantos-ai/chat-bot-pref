/**
 * View: RAG Admin — ETL multi-tenant + upload + doc management.
 */
const RagAdminView = (() => {
    let etlTimer = null;

    function render(container, key) {
        container.innerHTML = `
      <div class="view-header"><h2 class="view-title">Base RAG & ETL</h2><p class="view-sub">Gestão da base de conhecimento dos tenants</p></div>
      <div class="tabs">
        <div class="tab active" data-tab="etl">ETL Job</div>
        <div class="tab" data-tab="upload">Upload de Documentos</div>
      </div>

      <div id="tab-etl">
        <div class="card">
          <div class="card__title flex justify-between" style="align-items:center">
            DISPARAR ETL <span id="etl-badge" class="badge badge-idle" style="margin-left:8px">IDLE</span>
          </div>
          <div class="flex gap-8 mt-8">
            <select class="form-input" id="etl-tenant" style="flex:1">
              <option value="all">★ TODOS OS TENANTS</option>
            </select>
            <button class="btn btn-primary btn-mono btn-lg" id="btn-etl">▶ RODAR ETL</button>
          </div>
          <div class="terminal mt-16" id="etl-log">Aguardando...</div>
        </div>
      </div>

      <div id="tab-upload" style="display:none">
        <div class="card">
          <div class="flex gap-8 mt-8 mb-16">
            <label class="form-label" style="margin:0;align-self:center">Tenant:</label>
            <select class="form-input" id="upload-tenant" style="max-width:320px">
              <option value="">-- Selecione --</option>
            </select>
          </div>
          <div class="drop-zone" id="drop-zone">
            <div class="drop-zone__icon">📄</div>
            <div class="drop-zone__label">Arraste ou clique para selecionar</div>
            <div class="drop-zone__hint">PDF · TXT · MD · DOCX</div>
          </div>
          <input type="file" id="file-input" accept=".pdf,.txt,.md,.docx" style="display:none" multiple>
          <div id="upload-msg" style="margin-top:12px;font-family:var(--font-mono);font-size:12px"></div>
        </div>
        <div class="card mt-16">
          <div class="card__title flex justify-between" style="align-items:center">
            DOCUMENTOS <button class="btn btn-ghost btn-sm" id="btn-refresh-docs" style="margin-left:auto">↻</button>
          </div>
          <div id="docs-list"></div>
        </div>
      </div>
    `;

        // Tabs
        container.querySelectorAll('.tab').forEach(t => {
            t.addEventListener('click', () => {
                container.querySelectorAll('.tab').forEach(x => x.classList.remove('active'));
                t.classList.add('active');
                container.querySelector('#tab-etl').style.display = t.dataset.tab === 'etl' ? '' : 'none';
                container.querySelector('#tab-upload').style.display = t.dataset.tab === 'upload' ? '' : 'none';
                if (t.dataset.tab === 'upload') loadDocs();
            });
        });

        // Load tenants
        async function loadTenants() {
            const [data] = await apiFetch('/api/admin/tenants');
            if (!data?.tenants) return;
            const etlSel = container.querySelector('#etl-tenant');
            const uploadSel = container.querySelector('#upload-tenant');
            data.tenants.forEach(t => {
                const o1 = el('option', '', `${t.client_name || t.tenant_id}`);
                o1.value = t.tenant_id;
                const o2 = o1.cloneNode(true);
                etlSel.appendChild(o1);
                uploadSel.appendChild(o2);
            });
        }

        // ETL
        function updateBadge(status) {
            const b = container.querySelector('#etl-badge');
            if (b) { b.className = `badge badge-${status.toLowerCase()}`; b.textContent = status; }
        }

        async function pollEtl(tenantId) {
            const [data] = await apiFetch(`/api/admin/rag/status?tenant_id=${tenantId}`);
            if (!data) return;
            const log = container.querySelector('#etl-log');
            if (log && data.log?.length) log.textContent = data.log.join('\n');
            updateBadge(data.status || 'IDLE');
            if (log) log.scrollTop = log.scrollHeight;
            if (data.status !== 'RUNNING') {
                clearInterval(etlTimer); etlTimer = null;
                container.querySelector('#btn-etl').disabled = false;
            }
        }

        container.querySelector('#btn-etl').addEventListener('click', async () => {
            const btn = container.querySelector('#btn-etl');
            const tenant = container.querySelector('#etl-tenant').value;
            const log = container.querySelector('#etl-log');
            btn.disabled = true; updateBadge('RUNNING');
            if (log) log.textContent = 'Iniciando ETL...';
            const [, err] = await apiFetch(`/api/admin/rag/trigger?tenant_id=${tenant}`, { method: 'POST' });
            if (err) { updateBadge('ERROR'); if (log) log.textContent = `Erro: ${err}`; btn.disabled = false; return; }
            etlTimer = setInterval(() => pollEtl(tenant), 1500);
        });

        // Upload
        const zone = container.querySelector('#drop-zone');
        const finpt = container.querySelector('#file-input');
        zone.addEventListener('click', () => finpt.click());
        zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('drag-over'); });
        zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
        zone.addEventListener('drop', e => { e.preventDefault(); zone.classList.remove('drag-over'); doUpload(e.dataTransfer.files); });
        finpt.addEventListener('change', () => doUpload(finpt.files));

        async function doUpload(files) {
            const tid = container.querySelector('#upload-tenant').value;
            const msgEl = container.querySelector('#upload-msg');
            if (!tid) { toast('Selecione um tenant primeiro', false); return; }
            for (const f of files) {
                msgEl.style.color = 'var(--steel-gray)';
                msgEl.textContent = `Enviando ${f.name}...`;
                const fd = new FormData(); fd.append('file', f);
                const adminKey2 = localStorage.getItem('nexo_admin_key') || '';
                try {
                    const res = await fetch(`/api/admin/rag/upload/${tid}`, { method: 'POST', headers: { 'X-Admin-Key': adminKey2 }, body: fd });
                    const data = await res.json();
                    if (res.ok) { msgEl.style.color = '#059669'; msgEl.textContent = `✓ ${f.name} (${fmtBytes(data.size)})`; }
                    else { msgEl.style.color = '#DC2626'; msgEl.textContent = `⚠ ${data.detail}`; }
                } catch (e) { msgEl.style.color = '#DC2626'; msgEl.textContent = `⚠ ${e.message}`; }
            }
            loadDocs();
        }

        async function loadDocs() {
            const tid = container.querySelector('#upload-tenant').value;
            const listEl = container.querySelector('#docs-list');
            if (!tid || !listEl) return;
            const [data] = await apiFetch(`/api/admin/rag/docs/${tid}`);
            if (!data?.docs?.length) { listEl.innerHTML = '<p style="color:var(--steel-gray);font-size:13px">Nenhum documento.</p>'; return; }
            listEl.innerHTML = `<div class="table-wrap"><table>
        <thead><tr><th>ARQUIVO</th><th>TAMANHO</th><th>DATA</th><th>AÇÕES</th></tr></thead>
        <tbody>${data.docs.map(d => `
          <tr>
            <td class="td-mono">${d.filename}</td>
            <td class="td-mono">${fmtBytes(d.size)}</td>
            <td class="td-mono">${fmtDate(new Date(d.modified * 1000).toISOString())}</td>
            <td><button class="btn btn-ghost btn-sm" style="color:#DC2626;border-color:#DC2626" data-del="${d.filename}">Deletar</button></td>
          </tr>`).join('')}
        </tbody></table></div>`;
            listEl.querySelectorAll('[data-del]').forEach(btn => {
                btn.addEventListener('click', async () => {
                    if (!confirm(`Deletar "${btn.dataset.del}"?`)) return;
                    const [, err] = await apiFetch(`/api/admin/rag/docs/${tid}/${encodeURIComponent(btn.dataset.del)}`, { method: 'DELETE' });
                    if (err) { toast(`Erro: ${err}`, false); return; }
                    toast('Documento removido'); loadDocs();
                });
            });
        }

        container.querySelector('#btn-refresh-docs').addEventListener('click', loadDocs);
        container.querySelector('#upload-tenant').addEventListener('change', loadDocs);
        loadTenants();
    }

    return { render };
})();
