-- Migration: 20260126_add_audit_schema
-- Applied by: operator (script)
-- Purpose: add relational audit schema expected by application v1.1

BEGIN;

-- 1) Extension
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 2) Create ENUM types if missing
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'intent_type') THEN
    CREATE TYPE intent_type AS ENUM ('GREETING','COMPLIMENT','INFO_REQUEST','SCHEDULE_QUERY','CONTACT_REQUEST','COMPLAINT','HUMAN_HANDOFF','OUT_OF_SCOPE');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'decision_type') THEN
    CREATE TYPE decision_type AS ENUM ('ANSWER_RAG','ANSWER_DIRECT','PUBLIC_ACK','PUBLIC_REDIRECT','FALLBACK','ESCALATE','NO_REPLY','BLOCK');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'response_type') THEN
    CREATE TYPE response_type AS ENUM ('SUCCESS','FALLBACK','BLOCKED','ESCALATED','NO_REPLY','ERROR');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'policy_decision_type') THEN
    CREATE TYPE policy_decision_type AS ENUM ('ALLOW','ALLOW_LIMITED','REDIRECT','NO_REPLY','BLOCK');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'fallback_reason_type') THEN
    CREATE TYPE fallback_reason_type AS ENUM ('out_of_scope','low_confidence','no_docs_found','policy_blocked');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'channel_type') THEN
    CREATE TYPE channel_type AS ENUM ('web_widget','instagram_dm','instagram_comment','facebook_dm','facebook_comment');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'surface_type') THEN
    CREATE TYPE surface_type AS ENUM ('inbox','public_comment','web');
  END IF;
END$$;

-- 3) usuarios_anonimos
CREATE TABLE IF NOT EXISTS usuarios_anonimos (
    id_usuario BIGSERIAL PRIMARY KEY,
    hash_usuario VARCHAR(128) NOT NULL UNIQUE,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 4) Alter existing audit_events safely: add columns expected by the app
ALTER TABLE public.audit_events
  ADD COLUMN IF NOT EXISTS id_evento UUID DEFAULT gen_random_uuid(),
  ADD COLUMN IF NOT EXISTS id_requisicao UUID,
  ADD COLUMN IF NOT EXISTS id_sessao VARCHAR(128),
  ADD COLUMN IF NOT EXISTS id_usuario BIGINT,
  ADD COLUMN IF NOT EXISTS canal channel_type,
  ADD COLUMN IF NOT EXISTS tipo_superficie surface_type,
  ADD COLUMN IF NOT EXISTS id_mensagem_externa VARCHAR(128),
  ADD COLUMN IF NOT EXISTS id_thread VARCHAR(128),
  ADD COLUMN IF NOT EXISTS id_post VARCHAR(128),
  ADD COLUMN IF NOT EXISTS id_comentario VARCHAR(128),
  ADD COLUMN IF NOT EXISTS id_autor_plataforma VARCHAR(128),
  ADD COLUMN IF NOT EXISTS intencao intent_type,
  ADD COLUMN IF NOT EXISTS confianca_classificador DECIMAL(4,3),
  ADD COLUMN IF NOT EXISTS decisao_politica policy_decision_type,
  ADD COLUMN IF NOT EXISTS motivo_bloqueio VARCHAR(128),
  ADD COLUMN IF NOT EXISTS id_regra_bloqueio VARCHAR(64),
  ADD COLUMN IF NOT EXISTS decisao decision_type,
  ADD COLUMN IF NOT EXISTS tipo_resposta response_type,
  ADD COLUMN IF NOT EXISTS motivo_fallback fallback_reason_type,
  ADD COLUMN IF NOT EXISTS id_base VARCHAR(64),
  ADD COLUMN IF NOT EXISTS modelo VARCHAR(64),
  ADD COLUMN IF NOT EXISTS temperatura DECIMAL(3,2),
  ADD COLUMN IF NOT EXISTS versao_prompt VARCHAR(32),
  ADD COLUMN IF NOT EXISTS tempo_resposta_ms INTEGER,
  ADD COLUMN IF NOT EXISTS codigo_erro VARCHAR(32),
  ADD COLUMN IF NOT EXISTS tipo_excecao VARCHAR(128),
  ADD COLUMN IF NOT EXISTS versao_app VARCHAR(32),
  ADD COLUMN IF NOT EXISTS criado_em TIMESTAMPTZ DEFAULT now();

-- 5) Indexes for audit_events (create only if missing)
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_audit_id_requisicao') THEN
    CREATE INDEX idx_audit_id_requisicao ON public.audit_events(id_requisicao);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_audit_id_mensagem_externa') THEN
    CREATE UNIQUE INDEX idx_audit_id_mensagem_externa ON public.audit_events(id_mensagem_externa) WHERE id_mensagem_externa IS NOT NULL;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_audit_criado_em') THEN
    CREATE INDEX idx_audit_criado_em ON public.audit_events(criado_em);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_audit_id_sessao_criado_em') THEN
    CREATE INDEX idx_audit_id_sessao_criado_em ON public.audit_events(id_sessao, criado_em DESC);
  END IF;
END$$;

-- 6) Create rag_queries (safe)
CREATE TABLE IF NOT EXISTS rag_queries (
    id_consulta UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_requisicao UUID,
    id_base VARCHAR(64),
    tipo_superficie surface_type,
    texto_consulta TEXT,
    modelo_embedding VARCHAR(64),
    top_k SMALLINT,
    documentos_recuperados JSONB,
    quantidade_documentos SMALLINT DEFAULT 0,
    melhor_score DECIMAL(4,3),
    sem_documentos BOOLEAN DEFAULT FALSE,
    tempo_busca_ms INTEGER,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_rag_queries_audit_events FOREIGN KEY (id_requisicao) REFERENCES audit_events(id_requisicao) ON DELETE CASCADE
);

-- 7) Indexes for rag_queries
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_rag_id_requisicao') THEN
    CREATE INDEX idx_rag_id_requisicao ON rag_queries(id_requisicao);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_rag_criado_em') THEN
    CREATE INDEX idx_rag_criado_em ON rag_queries(criado_em);
  END IF;
END$$;

-- 8) Create conversas (safe)
CREATE TABLE IF NOT EXISTS conversas (
    id_conversa BIGSERIAL PRIMARY KEY,
    id_requisicao UUID UNIQUE,
    id_usuario BIGINT,
    canal channel_type,
    tipo_superficie surface_type,
    mensagem_usuario TEXT,
    mensagem_resposta TEXT,
    tamanho_mensagem INTEGER,
    tamanho_resposta INTEGER,
    intencao intent_type,
    decisao decision_type,
    tipo_resposta response_type,
    motivo_fallback fallback_reason_type,
    motivo_politica VARCHAR(64),
    sentimento VARCHAR(32),
    emocao VARCHAR(32),
    formalidade VARCHAR(32),
    consulta_expandida TEXT,
    encontrou_docs BOOLEAN,
    melhor_score DECIMAL(4,3),
    fontes TEXT[],
    modelo VARCHAR(64),
    temperatura DECIMAL(3,2),
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_conversas_audit_events FOREIGN KEY (id_requisicao) REFERENCES audit_events(id_requisicao) ON DELETE CASCADE
);

COMMIT;

-- End of migration
