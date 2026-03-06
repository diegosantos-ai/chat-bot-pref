-- ================================================
-- Nexo Admin — Migrações Iniciais
-- ================================================

-- 1. Tabela de Contratos
CREATE TABLE IF NOT EXISTS contracts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(64) NOT NULL,
    plan_type VARCHAR(32) NOT NULL DEFAULT 'starter', -- starter, pro, enterprise
    starts_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ,
    msg_limit INTEGER DEFAULT 500,
    status VARCHAR(32) NOT NULL DEFAULT 'active',    -- active, trial, expired, cancelled
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_contracts_tenant ON contracts(tenant_id);
CREATE INDEX IF NOT EXISTS idx_contracts_status ON contracts(status);

-- 2. Tabela de Log de Jobs RAG ETL
CREATE TABLE IF NOT EXISTS rag_job_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(64), -- NULL se for job global
    status VARCHAR(32) NOT NULL, -- RUNNING, SUCCESS, ERROR
    docs_processed INTEGER DEFAULT 0,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    log_output TEXT,
    error_msg TEXT
);

CREATE INDEX IF NOT EXISTS idx_rag_job_tenant ON rag_job_log(tenant_id);

-- 3. Garantir colunas básicas em tenants (caso migrations anteriores tenham falhado)
-- Nota: is_active já existe segundo app/tenant_config.py, mas ALTER TABLE IF NOT EXISTS é seguro.
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now();

-- 4. Garantir que tenant_credentials exista
CREATE TABLE IF NOT EXISTS tenant_credentials (
    tenant_id VARCHAR(64) PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
