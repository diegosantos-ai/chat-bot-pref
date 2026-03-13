/**
 * View: Health & Métricas — status dos serviços + uso por tenant.
 */
const HealthAdminView = (() => {
    let timer = null;

    function render(container, key) {
        container.innerHTML = `
      <div class="view-header flex justify-between" style="align-items:flex-end">
        <div><h2 class="view-title">Health & Métricas</h2><p class="view-sub">Status das dependências e uso por tenant</p></div>
        <div class="flex gap-8 flex-center">
          <span class="text-mono text-sm" id="last-check">—</span>
          <button class="btn btn-ghost" id="btn-check">↻ Verificar</button>
        </div>
      </div>
      <div class="service-grid" id="service-grid">
        ${['postgres', 'chromadb', 'redis'].map(s => `
          <div class="service-card" id="card-${s}">
            <div class="service-card__name">${s.toUpperCase()}</div>
            <div class="service-card__status">—</div>
            <div class="service-card__latency">Verificando...</div>
          </div>`).join('')}
      </div>
      <div class="card mt-16">
        <div class="card__title flex justify-between" style="align-items:center">
          MENSAGENS NAS ÚLTIMAS 24H (POR TENANT)
          <button class="btn btn-ghost btn-sm" id="btn-refresh-metrics">↻</button>
        </div>
        <div id="metrics-table"><p style="color:var(--steel-gray);font-size:13px">Carregando...</p></div>
      </div>
    `;

        async function checkHealth() {
            const [data] = await apiFetch('/api/admin/health/details');
            const now = new Date().toLocaleTimeString('pt-BR');
            const lastEl = container.querySelector('#last-check');
            if (lastEl) lastEl.textContent = `Verificado às ${now}`;
            const map = { postgres: 'PostgreSQL', chromadb: 'ChromaDB', redis: 'Redis' };
            Object.entries(map).forEach(([k, name]) => {
                const card = container.querySelector(`#card-${k}`);
                if (!card) return;
                const info = data?.[k] || { status: 'OFFLINE' };
                const status = info.status || 'OFFLINE';
                const lat = info.latency_ms != null ? `${info.latency_ms} ms` : (info.error?.slice(0, 60) || 'N/A');
                card.className = `service-card ${status === 'ONLINE' ? 'online' : status === 'DEGRADED' ? 'warn' : 'offline'}`;
                card.querySelector('.service-card__status').innerHTML = `<span class="badge badge-${status === 'ONLINE' ? 'online' : status === 'DEGRADED' ? 'warn' : 'offline'}">${status}</span>`;
                card.querySelector('.service-card__latency').textContent = lat;
            });
        }

        async function loadMetrics() {
            const [data] = await apiFetch('/api/admin/metrics');
            const el2 = container.querySelector('#metrics-table');
            if (!data?.messages_24h?.length) { el2.innerHTML = '<p style="color:var(--steel-gray);font-size:13px">Nenhuma mensagem nas últimas 24h.</p>'; return; }
            el2.innerHTML = `<div class="table-wrap"><table>
        <thead><tr><th>TENANT ID</th><th>MENSAGENS 24H</th><th>%</th></tr></thead>
        <tbody>${(() => {
                    const total = data.messages_24h.reduce((s, r) => s + Number(r.msgs_24h), 0);
                    return data.messages_24h.map(r => {
                        const pct = total ? ((r.msgs_24h / total) * 100).toFixed(1) : 0;
                        return `<tr>
              <td class="td-mono text-orange">${r.tenant_id}</td>
              <td class="td-mono fw-600">${Number(r.msgs_24h).toLocaleString('pt-BR')}</td>
              <td><div style="display:flex;align-items:center;gap:8px">
                <div style="flex:1;height:6px;background:var(--off-white)">
                  <div style="height:100%;width:${pct}%;background:var(--signal-orange)"></div>
                </div>
                <span class="td-mono">${pct}%</span>
              </div></td>
            </tr>`;
                    }).join('');
                })()}</tbody>
        <tfoot><tr style="border-top:2px solid var(--off-white)">
          <td class="fw-600">TOTAL</td>
          <td class="td-mono fw-600">${data.messages_24h.reduce((s, r) => s + Number(r.msgs_24h), 0).toLocaleString('pt-BR')}</td>
          <td></td>
        </tr></tfoot>
      </table></div>`;
        }

        container.querySelector('#btn-check').addEventListener('click', checkHealth);
        container.querySelector('#btn-refresh-metrics').addEventListener('click', loadMetrics);

        if (timer) clearInterval(timer);
        timer = setInterval(checkHealth, 30_000);
        checkHealth();
        loadMetrics();
    }

    return { render };
})();
