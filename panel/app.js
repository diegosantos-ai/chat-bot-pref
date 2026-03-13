/**
 * Chat Pref — SPA Router & App Init
 * Manages view switching, tenant loading, and global state.
 */

const App = (() => {
    // ---- State -----------------------------------------------
    let currentView = 'chat';
    let tenantId = '';

    const VIEW_TITLES = {
        chat: 'Chat Test',
        logs: 'Logs de Conversa',
        config: 'Configuração do Tenant',
        rag: 'Base RAG & Documentos',
        health: 'Status dos Serviços',
        training: 'Treinamento',
    };

    const VIEWS = { chat: ChatView, logs: LogsView, config: ConfigView, rag: RagView, health: HealthView, training: TrainingView };

    // ---- DOM refs --------------------------------------------
    const mainEl = () => document.getElementById('main-content');
    const headerTitle = () => document.getElementById('header-title');
    const headerTenant = () => document.getElementById('header-tenant');
    const tenantSelect = () => document.getElementById('tenant-select');

    // ---- Tenant management -----------------------------------
    async function loadTenants() {
        try {
            const res = await fetch('/api/panel/tenants');
            const data = await res.json();
            const sel = tenantSelect();
            sel.innerHTML = '';
            data.tenants.forEach(t => {
                const opt = document.createElement('option');
                opt.value = t.tenant_id;
                opt.textContent = t.client_name || t.tenant_id;
                sel.appendChild(opt);
            });
            if (data.tenants.length > 0) {
                tenantId = data.tenants[0].tenant_id;
                sel.value = tenantId;
                updateHeaderTenant();
            }
        } catch {
            const sel = tenantSelect();
            sel.innerHTML = '<option value="prefeitura_nova_esperanca">Prefeitura de Nova Esperança</option>';
            tenantId = 'prefeitura_nova_esperanca';
            updateHeaderTenant();
        }
    }

    function updateHeaderTenant() {
        const sel = tenantSelect();
        const label = sel.options[sel.selectedIndex]?.text || tenantId;
        if (headerTenant()) headerTenant().textContent = label;
    }

    // ---- Router ----------------------------------------------
    function navigate(view) {
        if (!VIEWS[view]) return;
        currentView = view;

        // Update nav
        document.querySelectorAll('.nav-item').forEach(el => {
            el.classList.toggle('active', el.dataset.view === view);
        });

        // Update header
        if (headerTitle()) headerTitle().textContent = VIEW_TITLES[view] || view;
        updateHeaderTenant();

        // Render view
        const container = mainEl();
        container.innerHTML = '';
        const wrapper = document.createElement('div');
        wrapper.className = 'view';
        container.appendChild(wrapper);
        VIEWS[view].render(wrapper, tenantId);
    }

    // ---- Boot ------------------------------------------------
    async function init() {
        // Bind nav clicks
        document.querySelectorAll('.nav-item[data-view]').forEach(el => {
            el.addEventListener('click', () => navigate(el.dataset.view));
        });

        // Bind tenant select
        const sel = tenantSelect();
        if (sel) {
            sel.addEventListener('change', () => {
                tenantId = sel.value;
                updateHeaderTenant();
                navigate(currentView); // re-render current view with new tenant
            });
        }

        await loadTenants();
        navigate('chat');
    }

    // ---- Public ----------------------------------------------
    return {
        init,
        getTenant: () => tenantId,
        navigate,
    };
})();

// ---- Global helpers ----------------------------------------

/** Fetch with JSON, returns [data, error] */
async function apiFetch(url, opts = {}) {
    try {
        const res = await fetch(url, {
            headers: { 'Content-Type': 'application/json', ...opts.headers },
            ...opts,
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: res.statusText }));
            return [null, err.detail || 'Erro desconhecido'];
        }
        return [await res.json(), null];
    } catch (e) {
        return [null, e.message];
    }
}

/** Create DOM element shorthand */
function el(tag, cls, html = '') {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html) e.innerHTML = html;
    return e;
}

/** Format ISO date to local short string */
function fmtDate(iso) {
    if (!iso) return '—';
    return new Date(iso).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' });
}

/** Format bytes to human-readable */
function fmtBytes(bytes) {
    if (!bytes) return '—';
    const units = ['B', 'KB', 'MB', 'GB'];
    let i = 0;
    let v = bytes;
    while (v >= 1024 && i < units.length - 1) { v /= 1024; i++; }
    return `${v.toFixed(1)} ${units[i]}`;
}

document.addEventListener('DOMContentLoaded', App.init);
