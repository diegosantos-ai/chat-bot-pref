/**
 * View: Status dos Serviços
 * Shows real-time health of DB, ChromaDB and Redis with auto-refresh.
 */
const HealthView = (() => {
    let refreshTimer = null;

    function render(container, tenantId) {
        container.innerHTML = `
      <div class="view-header flex justify-between" style="align-items:flex-end">
        <div>
          <h2 class="view-title">Status dos Serviços</h2>
          <p class="view-sub">Verificação das dependências compartilhadas</p>
        </div>
        <div class="flex gap-8 flex-center">
          <span class="text-mono" style="color:var(--steel-gray)" id="last-check">—</span>
          <button class="btn btn-ghost" id="btn-refresh-health">↻ Verificar</button>
        </div>
      </div>

      <div class="service-grid" id="service-grid">
        ${['postgres', 'chromadb', 'redis'].map(s => `
          <div class="service-card" id="card-${s}">
            <div class="service-card__name">${s.toUpperCase()}</div>
            <div class="service-card__status">—</div>
            <div class="service-card__latency">Verificando...</div>
          </div>
        `).join('')}
      </div>

      <div class="card mt-16">
        <div class="card__title">AUTO-REFRESH</div>
        <p style="font-size:13px;color:var(--steel-gray)">
          Verificação automática a cada <span class="text-orange fw-600">30 segundos</span>.
          Os serviços são compartilhados pela infraestrutura <span class="text-mono">infra_nexo-network</span>.
        </p>
      </div>
    `;

        async function checkHealth() {
            const [data, err] = await apiFetch('/api/panel/health/details');
            const now = new Date().toLocaleTimeString('pt-BR');
            const lastEl = container.querySelector('#last-check');
            if (lastEl) lastEl.textContent = `Última verificação: ${now}`;

            const services = { postgres: 'PostgreSQL', chromadb: 'ChromaDB', redis: 'Redis' };
            Object.entries(services).forEach(([key, name]) => {
                const card = container.querySelector(`#card-${key}`);
                if (!card) return;
                const info = data?.[key] || { status: 'OFFLINE', latency_ms: null };
                const status = info.status || 'OFFLINE';
                const latency = info.latency_ms != null ? `${info.latency_ms} ms` : (info.error ? info.error.slice(0, 60) : 'N/A');
                card.className = `service-card ${status === 'ONLINE' ? 'online' : status === 'DEGRADED' ? 'warn' : 'offline'}`;
                card.querySelector('.service-card__name').textContent = name;
                card.querySelector('.service-card__status').innerHTML = `<span class="badge badge-${status === 'ONLINE' ? 'online' : status === 'DEGRADED' ? 'warn' : 'offline'}">${status}</span>`;
                card.querySelector('.service-card__latency').textContent = latency;
            });
        }

        container.querySelector('#btn-refresh-health').addEventListener('click', checkHealth);

        // Clean up previous timers if view is re-rendered
        if (refreshTimer) clearInterval(refreshTimer);
        refreshTimer = setInterval(checkHealth, 30_000);
        checkHealth();
    }

    return { render };
})();
