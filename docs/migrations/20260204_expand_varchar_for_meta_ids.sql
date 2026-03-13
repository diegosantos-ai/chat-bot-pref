-- ========================================
-- Migration: Expandir colunas VARCHAR para Meta IDs
-- ========================================
-- Data: 2026-02-04
-- Problema: "value too long for type character varying(128)"
-- Os IDs da Meta (Instagram/Facebook) excedem 128 caracteres.
-- ========================================
-- Início da transação
BEGIN;
-- ========================================
-- TABELA: audit_events
-- ========================================
-- Expandir id_sessao para 256 (pode conter IDs compostos)
ALTER TABLE audit_events
ALTER COLUMN id_sessao TYPE VARCHAR(256);
-- Expandir id_mensagem_externa para 512 (IDs da Meta podem ser muito longos)
ALTER TABLE audit_events
ALTER COLUMN id_mensagem_externa TYPE VARCHAR(512);
-- Expandir id_thread para 256
ALTER TABLE audit_events
ALTER COLUMN id_thread TYPE VARCHAR(256);
-- Expandir id_post para 256
ALTER TABLE audit_events
ALTER COLUMN id_post TYPE VARCHAR(256);
-- Expandir id_comentario para 256
ALTER TABLE audit_events
ALTER COLUMN id_comentario TYPE VARCHAR(256);
-- Expandir id_autor_plataforma para 256
ALTER TABLE audit_events
ALTER COLUMN id_autor_plataforma TYPE VARCHAR(256);
-- ========================================
-- TABELA: conversas (se existir)
-- ========================================
-- Não tem as colunas de ID externo, então não precisa alterar
-- ========================================
-- Verificação
-- ========================================
-- Verificar as alterações
SELECT column_name,
    data_type,
    character_maximum_length
FROM information_schema.columns
WHERE table_name = 'audit_events'
    AND column_name IN (
        'id_sessao',
        'id_mensagem_externa',
        'id_thread',
        'id_post',
        'id_comentario',
        'id_autor_plataforma'
    )
ORDER BY column_name;
-- Commit da transação
COMMIT;
-- ========================================
-- Rollback (se necessário)
-- ========================================
-- Para reverter, execute:
-- 
-- BEGIN;
-- ALTER TABLE audit_events ALTER COLUMN id_sessao TYPE VARCHAR(128);
-- ALTER TABLE audit_events ALTER COLUMN id_mensagem_externa TYPE VARCHAR(128);
-- ALTER TABLE audit_events ALTER COLUMN id_thread TYPE VARCHAR(128);
-- ALTER TABLE audit_events ALTER COLUMN id_post TYPE VARCHAR(128);
-- ALTER TABLE audit_events ALTER COLUMN id_comentario TYPE VARCHAR(128);
-- ALTER TABLE audit_events ALTER COLUMN id_autor_plataforma TYPE VARCHAR(256);
-- COMMIT;