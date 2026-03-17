-- ========================================
-- Schema Migration: Multi-Tenant RLS & Core Tables
-- ========================================
-- Descrição: Migração inicial para transformar o banco em Multi-Tenant
-- Adiciona tabelas base (tenants), colunas tenant_id, e ativa Row-Level Security (RLS)
-- em todas as tabelas sensíveis de dados do cliente.
-- ========================================

BEGIN;

-- 1. Criar tabela core 'tenants'
CREATE TABLE IF NOT EXISTS tenants (
    tenant_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Inserir o tenant base (Default fallback ou migration safe)
-- IDs reais serão gerenciados via painel administrativo ou script de setup
INSERT INTO tenants (tenant_id, name) VALUES ('default', 'Default System Tenant') ON CONFLICT DO NOTHING;

-- 2. Adicionar 'tenant_id' em tabelas existentes
-- Omitirmos audit_events temporalmente para evitar quebras se já tiver dados, ou forçamos com default.
-- Como é uma migração para MVP limpo, adicionamos com constraint NOT NULL e um valor default genérico.

ALTER TABLE usuarios_anonimos
ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(50) NOT NULL DEFAULT 'default' REFERENCES tenants(tenant_id);

ALTER TABLE audit_events
ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(50) NOT NULL DEFAULT 'default' REFERENCES tenants(tenant_id);

ALTER TABLE rag_queries
ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(50) NOT NULL DEFAULT 'default' REFERENCES tenants(tenant_id);

ALTER TABLE conversas
ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(50) NOT NULL DEFAULT 'default' REFERENCES tenants(tenant_id);

ALTER TABLE scrap_configs
ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(50) NOT NULL DEFAULT 'default' REFERENCES tenants(tenant_id);

ALTER TABLE scrap_schedules
ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(50) NOT NULL DEFAULT 'default' REFERENCES tenants(tenant_id);

ALTER TABLE scrap_results
ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(50) NOT NULL DEFAULT 'default' REFERENCES tenants(tenant_id);

ALTER TABLE rag_documents
ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(50) NOT NULL DEFAULT 'default' REFERENCES tenants(tenant_id);

ALTER TABLE admin_users
ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(50) NOT NULL DEFAULT 'default' REFERENCES tenants(tenant_id);


-- 3. Remover os DEFAULTs após as restrições terem sido cumpridas (obrigar inserts nominais no código)
ALTER TABLE usuarios_anonimos ALTER COLUMN tenant_id DROP DEFAULT;
ALTER TABLE audit_events ALTER COLUMN tenant_id DROP DEFAULT;
ALTER TABLE rag_queries ALTER COLUMN tenant_id DROP DEFAULT;
ALTER TABLE conversas ALTER COLUMN tenant_id DROP DEFAULT;
ALTER TABLE scrap_configs ALTER COLUMN tenant_id DROP DEFAULT;
ALTER TABLE scrap_schedules ALTER COLUMN tenant_id DROP DEFAULT;
ALTER TABLE scrap_results ALTER COLUMN tenant_id DROP DEFAULT;
ALTER TABLE rag_documents ALTER COLUMN tenant_id DROP DEFAULT;
ALTER TABLE admin_users ALTER COLUMN tenant_id DROP DEFAULT;


-- 4. Habilitar a Extensão de RLS global (Row Level Security)
-- Isso força que as políticas abaixo sejam mandatórias.

ALTER TABLE usuarios_anonimos ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE rag_queries ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversas ENABLE ROW LEVEL SECURITY;
ALTER TABLE scrap_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE scrap_schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE scrap_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE rag_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_users ENABLE ROW LEVEL SECURITY;


-- 5. Criar as Políticas de Isolamento (Policies)
-- A checagem será feita via variável de contexto 'app.tenant_id' definida pela aplicação.

-- usuarios_anonimos
DROP POLICY IF EXISTS tenant_isolation_policy ON usuarios_anonimos;
CREATE POLICY tenant_isolation_policy ON usuarios_anonimos
    FOR ALL
    USING (tenant_id = current_setting('app.tenant_id', true));

-- audit_events
DROP POLICY IF EXISTS tenant_isolation_policy ON audit_events;
CREATE POLICY tenant_isolation_policy ON audit_events
    FOR ALL
    USING (tenant_id = current_setting('app.tenant_id', true));

-- rag_queries
DROP POLICY IF EXISTS tenant_isolation_policy ON rag_queries;
CREATE POLICY tenant_isolation_policy ON rag_queries
    FOR ALL
    USING (tenant_id = current_setting('app.tenant_id', true));

-- conversas
DROP POLICY IF EXISTS tenant_isolation_policy ON conversas;
CREATE POLICY tenant_isolation_policy ON conversas
    FOR ALL
    USING (tenant_id = current_setting('app.tenant_id', true));

-- scrap_configs
DROP POLICY IF EXISTS tenant_isolation_policy ON scrap_configs;
CREATE POLICY tenant_isolation_policy ON scrap_configs
    FOR ALL
    USING (tenant_id = current_setting('app.tenant_id', true));

-- scrap_schedules
DROP POLICY IF EXISTS tenant_isolation_policy ON scrap_schedules;
CREATE POLICY tenant_isolation_policy ON scrap_schedules
    FOR ALL
    USING (tenant_id = current_setting('app.tenant_id', true));

-- scrap_results
DROP POLICY IF EXISTS tenant_isolation_policy ON scrap_results;
CREATE POLICY tenant_isolation_policy ON scrap_results
    FOR ALL
    USING (tenant_id = current_setting('app.tenant_id', true));

-- rag_documents
DROP POLICY IF EXISTS tenant_isolation_policy ON rag_documents;
CREATE POLICY tenant_isolation_policy ON rag_documents
    FOR ALL
    USING (tenant_id = current_setting('app.tenant_id', true));

-- admin_users (Nota: pode haver necessidade de um superadmin com bypass RLS no futuro, mas mantemos estrito agora)
DROP POLICY IF EXISTS tenant_isolation_policy ON admin_users;
CREATE POLICY tenant_isolation_policy ON admin_users
    FOR ALL
    USING (tenant_id = current_setting('app.tenant_id', true));


-- 6. Adicionar tabela de credenciais isoladas (Para as APIs Meta)
CREATE TABLE IF NOT EXISTS tenant_credentials (
    tenant_id VARCHAR(50) PRIMARY KEY REFERENCES tenants(tenant_id) ON DELETE CASCADE,

    -- META API (Page/App Credentials)
    meta_page_id VARCHAR(255),
    meta_access_token VARCHAR(500),
    meta_app_secret VARCHAR(255),
    meta_webhook_verify_token VARCHAR(255),

    -- Instagram specific
    meta_ig_page_id VARCHAR(255),
    meta_ig_access_token VARCHAR(500),
    meta_ig_app_secret VARCHAR(255),
    meta_ig_webhook_verify_token VARCHAR(255),

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Tabela puramente de configurações técnicas/vazamento de tenant_id, não precisa de policy de isolation row level
-- pois o app backend fará query direta pelo ID ao receber proxy ingress headers/body, mas ativamos por precaução de blindagem.
ALTER TABLE tenant_credentials ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation_policy ON tenant_credentials;
CREATE POLICY tenant_isolation_policy ON tenant_credentials
    FOR ALL
    USING (tenant_id = current_setting('app.tenant_id', true));


-- 7. Criar índices para otimização de joins com tenants
CREATE INDEX IF NOT EXISTS idx_usuarios_anonimos_tenant_id ON usuarios_anonimos(tenant_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_tenant_id ON audit_events(tenant_id);
CREATE INDEX IF NOT EXISTS idx_rag_queries_tenant_id ON rag_queries(tenant_id);
CREATE INDEX IF NOT EXISTS idx_conversas_tenant_id ON conversas(tenant_id);
CREATE INDEX IF NOT EXISTS idx_scrap_configs_tenant_id ON scrap_configs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_rag_documents_tenant_id ON rag_documents(tenant_id);

COMMIT;
