-- Migration: Alteração de VARCHAR para TEXT
-- Data: 2026-02-04
-- Versão: v1.2

-- Alterar tabela usuarios_anonimos
ALTER TABLE usuarios_anonimos 
ALTER COLUMN hash_usuario TYPE TEXT;

-- Alterar tabela audit_events
ALTER TABLE audit_events 
ALTER COLUMN id_sessao TYPE TEXT,
ALTER COLUMN id_mensagem_externa TYPE TEXT,
ALTER COLUMN id_thread TYPE TEXT,
ALTER COLUMN id_post TYPE TEXT,
ALTER COLUMN id_comentario TYPE TEXT,
ALTER COLUMN id_autor_plataforma TYPE TEXT;

-- Verificação (opcional - descomente para executar)
-- \d+ usuarios_anonimos
-- \d+ audit_events
