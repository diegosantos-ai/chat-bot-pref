-- Migration 002: Add per-platform Meta credentials and bot identity fields to tenant tables
-- Run AFTER 001_multi_tenant_rls.sql

-- ========================================================
-- 1. Adicionar colunas de identidade na tabela `tenants`
-- ========================================================
ALTER TABLE tenants
    ADD COLUMN IF NOT EXISTS bot_name         VARCHAR(100) NOT NULL DEFAULT 'Assistente Virtual',
    ADD COLUMN IF NOT EXISTS client_name      VARCHAR(150) NOT NULL DEFAULT 'Prefeitura',
    ADD COLUMN IF NOT EXISTS fallback_url     TEXT         NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS contact_phone    VARCHAR(30)  NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS contact_address  TEXT         NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS support_email    VARCHAR(150) NOT NULL DEFAULT '';

-- ========================================================
-- 2. Adicionar colunas de credenciais Meta separadas por plataforma
--    na tabela `tenant_credentials`
-- ========================================================
ALTER TABLE tenant_credentials
    ADD COLUMN IF NOT EXISTS meta_ig_page_id         VARCHAR(50),
    ADD COLUMN IF NOT EXISTS meta_fb_page_id         VARCHAR(50),
    ADD COLUMN IF NOT EXISTS meta_access_token_ig    TEXT,
    ADD COLUMN IF NOT EXISTS meta_access_token_fb    TEXT;

-- Index para lookup por page_id (usado pelo TenantResolver)
CREATE INDEX IF NOT EXISTS idx_tc_ig_page_id ON tenant_credentials(meta_ig_page_id)
    WHERE meta_ig_page_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tc_fb_page_id ON tenant_credentials(meta_fb_page_id)
    WHERE meta_fb_page_id IS NOT NULL;

-- ========================================================
-- 3. Atualizar a query do TenantResolver:
--    Inclui meta_ig_page_id e meta_fb_page_id nas buscas
--    (coberto pelo índice acima)
-- ========================================================

COMMENT ON COLUMN tenants.bot_name IS 'Nome do bot exibido para o cidadão (ex: TerezIA, ZéDoPovo, etc.)';
COMMENT ON COLUMN tenants.client_name IS 'Nome da prefeitura cliente (ex: Prefeitura de Santa Tereza)';
COMMENT ON COLUMN tenants.fallback_url IS 'URL do site da prefeitura para fallback de scraping';
COMMENT ON COLUMN tenants.contact_phone IS 'Telefone de contato exibido nos prompts de redirecionamento';
COMMENT ON COLUMN tenants.contact_address IS 'Endereço físico da prefeitura exibido nos prompts';
COMMENT ON COLUMN tenants.support_email IS 'Email para escalation de atendimento humano';
COMMENT ON COLUMN tenant_credentials.meta_ig_page_id IS 'Page ID do Instagram para roteamento de webhook';
COMMENT ON COLUMN tenant_credentials.meta_fb_page_id IS 'Page ID do Facebook para roteamento de webhook';
COMMENT ON COLUMN tenant_credentials.meta_access_token_ig IS 'Access Token da API Graph para Instagram';
COMMENT ON COLUMN tenant_credentials.meta_access_token_fb IS 'Access Token da API Graph para Facebook';
