-- Migration: Cache de Perfis Meta (Instagram/Facebook)
-- Data: 2026-02-14
-- Autor: Agente {bot_name}
-- 
-- Cria tabela para cachear perfis de usuários do Instagram/Facebook
-- evitando chamadas repetidas à API da Meta.

-- Cria tabela de cache de perfis
CREATE TABLE IF NOT EXISTS meta_user_profiles (
    id SERIAL PRIMARY KEY,
    platform_user_id VARCHAR(50) NOT NULL,
    platform VARCHAR(20) NOT NULL CHECK (platform IN ('instagram', 'facebook')),
    username VARCHAR(100),
    name VARCHAR(200),
    profile_picture_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform_user_id, platform)
);

-- Índices para busca eficiente
CREATE INDEX IF NOT EXISTS idx_meta_user_profiles_lookup 
ON meta_user_profiles(platform_user_id, platform);

CREATE INDEX IF NOT EXISTS idx_meta_user_profiles_updated 
ON meta_user_profiles(updated_at);

-- Trigger para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_meta_user_profiles_updated_at ON meta_user_profiles;
CREATE TRIGGER update_meta_user_profiles_updated_at
    BEFORE UPDATE ON meta_user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comentários para documentação
COMMENT ON TABLE meta_user_profiles IS 
'Cache de perfis do Instagram/Facebook para evitar chamadas repetidas à API da Meta. Dados são atualizados a cada 30 dias ou quando necessário.';

COMMENT ON COLUMN meta_user_profiles.platform_user_id IS 
'ID do usuário na plataforma (Instagram ou Facebook)';

COMMENT ON COLUMN meta_user_profiles.platform IS 
'Plataforma de origem: instagram ou facebook';

COMMENT ON COLUMN meta_user_profiles.username IS 
'Username/handle do usuário (ex: @prefeitura_sto)';

COMMENT ON COLUMN meta_user_profiles.name IS 
'Nome completo do perfil';
