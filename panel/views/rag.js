/**
 * View: Base RAG & Documentos
 * Two tabs: ETL Trigger (with live log) + Doc Upload.
 */
const RagView = (() => {
    let etlPollTimer = null;

    function render(container, tenantId) {
        container.innerHTML = `
      <div class="view-header">
        <h2 class="view-title">Base RAG & Documentos</h2>
        <p class="view-sub">Gestão da base de conhecimento do tenant</p>
      </div>

      <div class="tabs">
        <div class="tab active" data-tab="etl">ETL Job</div>
        <div class="tab" data-tab="upload">Upload de Documentos</div>
      </div>

      <!-- ETL Tab -->
      <div id="tab-etl">
        <div class="card">
          <div class="card__title flex justify-between" style="align-items:center">
            STATUS: <span id="etl-badge" class="badge badge-idle" style="margin-left:8px">IDLE</span>
          </div>
          <button class="btn btn-primary btn-mono btn-lg btn-block" id="btn-etl">
            ▶ RODAR ETL AGORA
          </button>
          <div class="terminal mt-16" id="etl-log">Aguardando disparo do ETL...</div>
        </div>
      </div>

      <!-- Upload Tab -->
      <div id="tab-upload" style="display:none">
        <div class="card">
          <div class="card__title">ENVIO DE DOCUMENTOS</div>
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
            DOCUMENTOS INGERIDOS
            <button class="btn btn-ghost" id="btn-refresh-docs" style="padding:2px 10px;font-size:11px">↻</button>
          </div>
          <div id="docs-list"><p style="color:var(--steel-gray);font-size:13px">Carregando...</p></div>
        </div>
      </div>
    `;

        // Tab switching
        container.querySelectorAll('.tab').forEach(t => {
            t.addEventListener('click', () => {
                container.querySelectorAll('.tab').forEach(x => x.classList.remove('active'));
                t.classList.add('active');
                container.querySelector('#tab-etl').style.display = t.dataset.tab === 'etl' ? '' : 'none';
                container.querySelector('#tab-upload').style.display = t.dataset.tab === 'upload' ? '' : 'none';
                if (t.dataset.tab === 'upload') loadDocs();
            });
        });

        // --- ETL ---
        function updateEtlBadge(status) {
            const badge = container.querySelector('#etl-badge');
            if (!badge) return;
            badge.className = `badge badge-${status.toLowerCase()}`;
            badge.textContent = status;
        }

        async function pollEtl() {
            const [data] = await apiFetch('/api/panel/rag/status');
            if (!data) return;
            const log = container.querySelector('#etl-log');
            if (log && data.log) log.textContent = data.log.join('\n');
            updateEtlBadge(data.status || 'IDLE');
            if (data.status === 'RUNNING') {
                if (log) log.scrollTop = log.scrollHeight;
            } else {
                clearInterval(etlPollTimer);
                etlPollTimer = null;
                container.querySelector('#btn-etl').disabled = false;
            }
        }

        container.querySelector('#btn-etl').addEventListener('click', async () => {
            const btn = container.querySelector('#btn-etl');
            btn.disabled = true;
            updateEtlBadge('RUNNING');
            const log = container.querySelector('#etl-log');
            if (log) log.textContent = 'Iniciando...';

            const [, err] = await apiFetch(`/api/panel/rag/trigger?tenant_id=${encodeURIComponent(tenantId)}`, { method: 'POST' });
            if (err) {
                updateEtlBadge('ERROR');
                if (log) log.textContent = `Erro: ${err}`;
                btn.disabled = false;
                return;
            }
            etlPollTimer = setInterval(pollEtl, 1500);
        });

        // --- Upload ---
        const dropZone = container.querySelector('#drop-zone');
        const fileInput = container.querySelector('#file-input');

        dropZone.addEventListener('click', () => fileInput.click());
        dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
        dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
        dropZone.addEventListener('drop', e => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
            uploadFiles(e.dataTransfer.files);
        });
        fileInput.addEventListener('change', () => uploadFiles(fileInput.files));

        async function uploadFiles(files) {
            const msgEl = container.querySelector('#upload-msg');
            for (const file of files) {
                msgEl.style.color = 'var(--steel-gray)';
                msgEl.textContent = `Enviando ${file.name}...`;
                const fd = new FormData();
                fd.append('file', file);
                try {
                    const res = await fetch(`/api/panel/rag/upload?tenant_id=${encodeURIComponent(tenantId)}`, { method: 'POST', body: fd });
                    const data = await res.json();
                    if (res.ok) {
                        msgEl.style.color = '#059669';
                        msgEl.textContent = `✓ ${file.name} enviado (${fmtBytes(data.size)})`;
                    } else {
                        msgEl.style.color = '#DC2626';
                        msgEl.textContent = `⚠ Erro: ${data.detail || res.statusText}`;
                    }
                } catch (e) {
                    msgEl.style.color = '#DC2626';
                    msgEl.textContent = `⚠ Falha de rede: ${e.message}`;
                }
            }
            loadDocs();
        }

        async function loadDocs() {
            const [data, err] = await apiFetch(`/api/panel/rag/docs?tenant_id=${encodeURIComponent(tenantId)}`);
            const listEl = container.querySelector('#docs-list');
            if (!listEl) return;
            if (err || !data?.docs?.length) {
                listEl.innerHTML = `<p style="color:var(--steel-gray);font-size:13px">Nenhum documento encontrado.</p>`;
                return;
            }
            listEl.innerHTML = `<div class="table-wrap"><table>
        <thead><tr><th>ARQUIVO</th><th>TAMANHO</th><th>DATA</th></tr></thead>
        <tbody>${data.docs.map(d => `
          <tr>
            <td class="td-mono" style="font-size:12px">${d.filename}</td>
            <td class="td-mono">${fmtBytes(d.size)}</td>
            <td class="td-mono">${fmtDate(new Date(d.modified * 1000).toISOString())}</td>
          </tr>
        `).join('')}</tbody>
      </table></div>`;
        }

        container.querySelector('#btn-refresh-docs').addEventListener('click', loadDocs);
    }

    return { render };
})();
