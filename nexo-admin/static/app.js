/**
 * Nexo Admin — SPA Router & Auth Manager
 */
const Admin = (() => {
    let adminKey = '';
    let currentView = 'tenants';

    const VIEW_TITLES = {
        tenants: 'Tenants',
        contracts: 'Contratos',
        credentials: 'Credenciais Meta',
        rag: 'Base RAG & ETL',
        jobs: 'Jobs Noturnos',
        logs: 'Logs & Auditoria',
        health: 'Health & Métricas',
        config: 'Sistema',
    };

    const VIEWS = {
        tenants: TenantsView,
        contracts: ContractsView,
        credentials: CredentialsView,
        rag: RagAdminView,
        jobs: JobsView,
        logs: LogsAdminView,
        health: HealthAdminView,
        config: ConfigAdminView,
    };

    // ---- Auth -----------------------------------------------
    function getKey() { return localStorage.getItem('nexo_admin_key') || ''; }
    function saveKey(k) { localStorage.setItem('nexo_admin_key', k); adminKey = k; }
    function clearKey() { localStorage.removeItem('nexo_admin_key'); adminKey = ''; }

    async function validateKey(key) {
        try {
            const res = await fetch('/api/admin/system', {
                headers: { 'X-Admin-Key': key }
            });
            return res.ok;
        } catch {
            return false;
        }
    }

    // ---- Login screen ---------------------------------------
    function showLogin() {
        document.getElementById('login-screen').style.display = 'flex';
        document.getElementById('admin-shell').style.display = 'none';
    }
    function showShell() {
        document.getElementById('login-screen').style.display = 'none';
        document.getElementById('admin-shell').style.display = '';
    }

    function bindLogin() {
        document.getElementById('login-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const key = document.getElementById('key-input').value.trim();
            const errEl = document.getElementById('login-error');
            if (!key) return;

            const btn = e.target.querySelector('button');
            btn.textContent = 'Verificando...';
            btn.disabled = true;

            const valid = await validateKey(key);
            btn.textContent = 'ENTRAR NO ADMIN ▶';
            btn.disabled = false;

            if (valid) {
                errEl.style.display = 'none';
                saveKey(key);
                showShell();
                navigate('tenants');
                checkAlerts();
            } else {
                errEl.style.display = 'block';
                document.getElementById('key-input').focus();
            }
        });
    }

    // ---- Alert badges ---------------------------------------
    async function checkAlerts() {
        // Contracts expiring ≤30 days
        const [data] = await apiFetch('/api/admin/contracts');
        if (data?.contracts?.length) {
            const soon = data.contracts.filter(c => {
                if (!c.expires_at || c.status !== 'active') return false;
                const days = (new Date(c.expires_at) - new Date()) / 86400000;
                return days <= 30;
            });
            const badge = document.getElementById('badge-contracts');
            if (badge) { badge.style.display = soon.length ? '' : 'none'; }
        }

        // Jobs with errors in last 24h
        const [jobs] = await apiFetch('/api/admin/rag/jobs?limit=20');
        if (jobs?.jobs?.length) {
            const dayAgo = new Date(Date.now() - 86400000);
            const failed = jobs.jobs.filter(j => j.status === 'ERROR' && new Date(j.started_at) > dayAgo);
            const badge = document.getElementById('badge-jobs');
            if (badge) { badge.style.display = failed.length ? '' : 'none'; }
        }
    }

    // ---- Router ---------------------------------------------
    function navigate(view) {
        if (!VIEWS[view]) return;
        currentView = view;
        document.querySelectorAll('.nav-item[data-view]').forEach(el => {
            el.classList.toggle('active', el.dataset.view === view);
        });
        const titleEl = document.getElementById('header-title');
        if (titleEl) titleEl.textContent = VIEW_TITLES[view] || view;
        const container = document.getElementById('main-content');
        container.innerHTML = '';
        const wrapper = document.createElement('div');
        wrapper.className = 'view';
        container.appendChild(wrapper);
        VIEWS[view].render(wrapper, adminKey);
    }

    // ---- Boot -----------------------------------------------
    async function init() {
        bindLogin();
        const stored = getKey();
        if (stored) {
            const valid = await validateKey(stored);
            if (valid) {
                adminKey = stored;
                showShell();
                navigate('tenants');
                checkAlerts();
                return;
            } else {
                clearKey();
            }
        }
        showLogin();
    }

    document.getElementById('btn-logout')?.addEventListener('click', () => {
        clearKey();
        showLogin();
    });

    document.querySelectorAll('.nav-item[data-view]').forEach(el => {
        el.addEventListener('click', () => navigate(el.dataset.view));
    });

    return { init, getKey, navigate };
})();

// ---- Global helpers ----------------------------------------
async function apiFetch(url, opts = {}) {
    const key = localStorage.getItem('nexo_admin_key') || '';
    try {
        const res = await fetch(url, {
            headers: { 'Content-Type': 'application/json', 'X-Admin-Key': key, ...opts.headers },
            ...opts,
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: res.statusText }));
            return [null, err.detail || 'Erro'];
        }
        return [await res.json(), null];
    } catch (e) {
        return [null, e.message];
    }
}

function el(tag, cls = '', html = '') {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html) e.innerHTML = html;
    return e;
}

function fmtDate(iso) {
    if (!iso) return '—';
    return new Date(iso).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' });
}

function fmtBytes(bytes) {
    if (!bytes) return '—';
    const units = ['B', 'KB', 'MB', 'GB'];
    let i = 0, v = bytes;
    while (v >= 1024 && i < units.length - 1) { v /= 1024; i++; }
    return `${v.toFixed(1)} ${units[i]}`;
}

function toast(msg, ok = true) {
    const t = el('div', `toast ${ok ? 'toast-ok' : 'toast-err'}`, msg);
    document.body.appendChild(t);
    setTimeout(() => t.classList.add('toast-show'), 10);
    setTimeout(() => { t.classList.remove('toast-show'); setTimeout(() => t.remove(), 400); }, 3500);
}

document.addEventListener('DOMContentLoaded', Admin.init);
