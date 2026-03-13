-- ========================================
-- Schema — Pilot Atendimento MVE
-- ========================================
-- Versão: v1.2
-- Banco: PostgreSQL 15+
-- Atualizado: Suporte a Instagram/Facebook + campos TEXT
-- ========================================

-- ========================================
-- TIPOS ENUM
-- ========================================

CREATE TYPE intent_type AS ENUM (
    'GREETING',
    'COMPLIMENT',
    'INFO_REQUEST',
    'SCHEDULE_QUERY',
    'CONTACT_REQUEST',
    'COMPLAINT',
    'HUMAN_HANDOFF',
    'OUT_OF_SCOPE'
);

CREATE TYPE decision_type AS ENUM (
    'ANSWER_RAG',
    'ANSWER_DIRECT',
    'PUBLIC_ACK',
    'PUBLIC_REDIRECT',
    'FALLBACK',
    'ESCALATE',
    'NO_REPLY',
    'BLOCK'
);

CREATE TYPE response_type AS ENUM (
    'SUCCESS',
    'FALLBACK',
    'BLOCKED',
    'ESCALATED',
    'NO_REPLY',
    'ERROR'
);

CREATE TYPE policy_decision_type AS ENUM (
    'ALLOW',
    'ALLOW_LIMITED',
    'REDIRECT',
    'NO_REPLY',
    'BLOCK'
);

CREATE TYPE fallback_reason_type AS ENUM (
    'out_of_scope',
    'low_confidence',
    'no_docs_found',
    'policy_blocked'
);

CREATE TYPE channel_type AS ENUM (
    'web_widget',
    'instagram_dm',
    'instagram_comment',
    'facebook_dm',
    'facebook_comment'
);

CREATE TYPE surface_type AS ENUM (
    'inbox',
    'public_comment',
    'web'
);

-- ========================================
-- TABELA: usuarios_anonimos
-- ========================================
-- Usuários anonimizados (hash) com id sequencial para relacionamento.

CREATE TABLE usuarios_anonimos (
    id_usuario      BIGSERIAL PRIMARY KEY,
    hash_usuario    TEXT NOT NULL UNIQUE,
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ========================================
-- TABELA: audit_events
-- ========================================
-- Registra cada interação do chat para auditoria completa.
-- Uma linha por mensagem processada.

CREATE TABLE audit_events (
    -- Identificação
    id_evento           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_requisicao       UUID NOT NULL,                      -- UUID único por mensagem
    id_sessao           TEXT NOT NULL,                      -- Sessão do usuário
    id_usuario          BIGINT REFERENCES usuarios_anonimos(id_usuario),

    -- Canal e Superfície (Meta: IG/FB)
    canal               channel_type NOT NULL DEFAULT 'web_widget',
    tipo_superficie     surface_type NOT NULL DEFAULT 'inbox',
    id_mensagem_externa TEXT,                               -- ID da mensagem na plataforma (idempotência)
    id_thread           TEXT,                               -- ID do thread de DM
    id_post             TEXT,                               -- ID do post (comentários)
    id_comentario       TEXT,                               -- ID do comentário
    id_autor_plataforma TEXT,                               -- ID do autor na plataforma

    -- Classificação
    intencao            intent_type NOT NULL,
    confianca_classificador DECIMAL(4,3),                   -- Ex: 0.950

    -- Policy Guard
    decisao_politica    policy_decision_type NOT NULL,
    motivo_bloqueio     VARCHAR(128),                       -- Motivo do bloqueio (texto curto)
    id_regra_bloqueio   VARCHAR(64),                        -- ID da regra que bloqueou

    -- Decisão e Resposta
    decisao             decision_type NOT NULL,
    tipo_resposta       response_type NOT NULL,
    motivo_fallback     fallback_reason_type,               -- Motivo do fallback

    -- RAG
    id_base             VARCHAR(64),                        -- Ex: BA-RAG-PILOTO-2026.01.v1

    -- Modelo/LLM
    modelo              VARCHAR(64),                        -- Ex: gemini-2.0-flash
    temperatura         DECIMAL(3,2),                       -- Ex: 0.30
    versao_prompt       VARCHAR(32),                        -- Ex: PROMPTS-2026.01.v1

    -- Performance
    tempo_resposta_ms   INTEGER,                            -- Tempo total de resposta

    -- Erros
    codigo_erro         VARCHAR(32),                        -- Código do erro (nullable)
    tipo_excecao        VARCHAR(128),                       -- Tipo da exceção (nullable)

    -- Versionamento
    versao_app          VARCHAR(32),                        -- Versão da app ou git SHA

    -- Timestamps
    criado_em           TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Índices para queries comuns
CREATE UNIQUE INDEX idx_audit_id_requisicao ON audit_events(id_requisicao);
CREATE UNIQUE INDEX idx_audit_id_mensagem_externa ON audit_events(id_mensagem_externa) WHERE id_mensagem_externa IS NOT NULL;
CREATE INDEX idx_audit_criado_em ON audit_events(criado_em);
CREATE INDEX idx_audit_id_sessao_criado_em ON audit_events(id_sessao, criado_em DESC);
CREATE INDEX idx_audit_intencao ON audit_events(intencao);
CREATE INDEX idx_audit_tipo_resposta ON audit_events(tipo_resposta);
CREATE INDEX idx_audit_canal ON audit_events(canal);
CREATE INDEX idx_audit_tipo_superficie ON audit_events(tipo_superficie);
CREATE INDEX idx_audit_erros ON audit_events(codigo_erro) WHERE codigo_erro IS NOT NULL;

-- ========================================
-- TABELA: rag_queries
-- ========================================
-- Registra cada consulta ao sistema RAG.
-- Vinculada ao audit_event via request_id.

CREATE TABLE rag_queries (
    id_consulta         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_requisicao       UUID NOT NULL,                  -- FK para audit_events

    -- Base de conhecimento
    id_base             VARCHAR(64),                    -- Ex: BA-RAG-PILOTO-2026.01.v1 (redundância útil)

    -- Superfície (para análise de modo de resposta)
    tipo_superficie     surface_type,                   -- inbox ou public_comment

    -- Query
    texto_consulta      TEXT NOT NULL,                  -- Pergunta enviada ao RAG
    modelo_embedding    VARCHAR(64),                    -- Modelo usado para embedding

    -- Parâmetros da busca
    top_k               SMALLINT,                       -- Quantos docs foram pedidos

    -- Resultados
    documentos_recuperados JSONB,                       -- Array de docs com scores
    quantidade_documentos  SMALLINT DEFAULT 0,          -- Quantos docs retornados
    melhor_score         DECIMAL(4,3),                  -- Score do melhor match
    sem_documentos       BOOLEAN DEFAULT FALSE,         -- Filtro simples: nenhum doc encontrado

    -- Performance
    tempo_busca_ms      INTEGER,                        -- Tempo de busca

    -- Timestamps
    criado_em           TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- FK
    CONSTRAINT fk_rag_queries_audit_events
        FOREIGN KEY (id_requisicao)
        REFERENCES audit_events(id_requisicao)
        ON DELETE CASCADE
);

-- Índices
CREATE INDEX idx_rag_id_requisicao ON rag_queries(id_requisicao);
CREATE INDEX idx_rag_criado_em ON rag_queries(criado_em);
CREATE INDEX idx_rag_melhor_score ON rag_queries(melhor_score);
CREATE INDEX idx_rag_sem_documentos ON rag_queries(sem_documentos) WHERE sem_documentos = TRUE;

-- ========================================
-- TABELA: conversas
-- ========================================
-- Conteúdo de perguntas e respostas (sem identificação direta).

CREATE TABLE conversas (
    id_conversa         BIGSERIAL PRIMARY KEY,
    id_requisicao       UUID NOT NULL UNIQUE,
    id_usuario          BIGINT NOT NULL REFERENCES usuarios_anonimos(id_usuario),
    canal               channel_type NOT NULL,
    tipo_superficie     surface_type NOT NULL,
    mensagem_usuario    TEXT NOT NULL,
    mensagem_resposta   TEXT,
    tamanho_mensagem    INTEGER,
    tamanho_resposta    INTEGER,
    intencao            intent_type NOT NULL,
    decisao             decision_type NOT NULL,
    tipo_resposta       response_type NOT NULL,
    motivo_fallback     fallback_reason_type,
    motivo_politica     VARCHAR(64),
    sentimento          VARCHAR(32),
    emocao              VARCHAR(32),
    formalidade         VARCHAR(32),
    consulta_expandida  TEXT,
    encontrou_docs      BOOLEAN,
    melhor_score        DECIMAL(4,3),
    fontes              TEXT[],
    modelo              VARCHAR(64),
    temperatura         DECIMAL(3,2),
    criado_em           TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_conversas_audit_events
        FOREIGN KEY (id_requisicao)
        REFERENCES audit_events(id_requisicao)
        ON DELETE CASCADE
);

CREATE INDEX idx_conversas_id_usuario ON conversas(id_usuario);
CREATE INDEX idx_conversas_criado_em ON conversas(criado_em);
CREATE INDEX idx_conversas_decisao ON conversas(decisao);
CREATE INDEX idx_conversas_tipo_resposta ON conversas(tipo_resposta);

-- ========================================
-- COMENTÁRIOS (Documentação no banco)
-- ========================================

COMMENT ON TABLE usuarios_anonimos IS 'Usuários anonimizados para relacionamento por id sequencial';
COMMENT ON TABLE audit_events IS 'Registro de auditoria de todas as interações do chat';
COMMENT ON TABLE rag_queries IS 'Log de consultas ao sistema RAG';
COMMENT ON TABLE conversas IS 'Perguntas e respostas com conteúdo, sem identificação direta';

COMMENT ON COLUMN audit_events.id_requisicao IS 'UUID único por mensagem - obrigatório';
COMMENT ON COLUMN audit_events.id_usuario IS 'ID sequencial de usuário (anonimizado)';
COMMENT ON COLUMN audit_events.canal IS 'Canal de origem: web_widget, instagram_dm, instagram_comment, facebook_dm, facebook_comment';
COMMENT ON COLUMN audit_events.tipo_superficie IS 'Tipo de superfície: inbox (DM) ou public_comment';
COMMENT ON COLUMN audit_events.id_mensagem_externa IS 'ID da mensagem na plataforma externa - usado para idempotência';
COMMENT ON COLUMN audit_events.confianca_classificador IS 'Confiança do classificador (0.000 a 1.000)';
COMMENT ON COLUMN audit_events.id_regra_bloqueio IS 'ID da regra de policy que causou o bloqueio';
COMMENT ON COLUMN audit_events.motivo_fallback IS 'Motivo específico quando tipo_resposta=FALLBACK';

COMMENT ON COLUMN rag_queries.documentos_recuperados IS 'JSONB: [{doc_id, title, score, snippet}]';
COMMENT ON COLUMN rag_queries.tipo_superficie IS 'Superfície da requisição - afeta modo de resposta';

-- ========================================
-- TABELA: admin_users - 13/02/2025
-- ========================================
-- Usuários administradores do painel {bot_name}

CREATE TABLE admin_users (
    id              BIGSERIAL PRIMARY KEY,
    username        VARCHAR(64) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    role            VARCHAR(32) NOT NULL DEFAULT 'admin',
    ativo           BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now(),
    ultimo_login    TIMESTAMPTZ
);

CREATE INDEX idx_admin_username ON admin_users(username);
CREATE INDEX idx_admin_ativo ON admin_users(ativo) WHERE ativo = TRUE;

COMMENT ON TABLE admin_users IS 'Usuários administradores do painel {bot_name}';
COMMENT ON COLUMN admin_users.username IS 'Nome de usuário para login';
COMMENT ON COLUMN admin_users.password_hash IS 'Hash bcrypt da senha';
COMMENT ON COLUMN admin_users.role IS 'Papel: admin, operator, viewer';
COMMENT ON COLUMN admin_users.ativo IS 'Usuário ativo ou inativo';
COMMENT ON COLUMN admin_users.ultimo_login IS 'Último login do usuário';

-- ========================================
-- TABELA: scrap_configs - 13/02/2026
-- ========================================
-- Configurações de scraping salvas

CREATE TABLE scrap_configs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome            VARCHAR(255) NOT NULL,
    url_base        TEXT NOT NULL,
    workflow        JSONB NOT NULL,
    ativo           BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_scrap_configs_ativo ON scrap_configs(ativo);
CREATE INDEX idx_scrap_configs_nome ON scrap_configs(nome);

COMMENT ON TABLE scrap_configs IS 'Configurações de scraping com workflow de nós';
COMMENT ON COLUMN scrap_configs.nome IS 'Nome da configuração';
COMMENT ON COLUMN scrap_configs.url_base IS 'URL base para scraping';
COMMENT ON COLUMN scrap_configs.workflow IS 'JSONB: estrutura de nós do workflow';

-- ========================================
-- TABELA: scrap_schedules - 13/02/2026
-- ========================================
-- Agendamentos de scraping

CREATE TABLE scrap_schedules (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_id       UUID NOT NULL REFERENCES scrap_configs(id) ON DELETE CASCADE,
    schedule_type   VARCHAR(20) NOT NULL CHECK (schedule_type IN ('manual', 'periodic')),
    interval_minutes INTEGER,
    enabled         BOOLEAN NOT NULL DEFAULT TRUE,
    last_run        TIMESTAMPTZ,
    next_run        TIMESTAMPTZ,
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_scrap_schedules_config ON scrap_schedules(config_id);
CREATE INDEX idx_scrap_schedules_enabled ON scrap_schedules(enabled) WHERE enabled = TRUE;

COMMENT ON TABLE scrap_schedules IS 'Agendamentos de scraping';
COMMENT ON COLUMN scrap_schedules.schedule_type IS 'Tipo: manual ou periodic';
COMMENT ON COLUMN scrap_schedules.interval_minutes IS 'Intervalo em minutos (para periodic)';

-- ========================================
-- TABELA: scrap_results - 13/02/2026
-- ========================================
-- Resultados de execuções de scraping

CREATE TABLE scrap_results (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_id       UUID NOT NULL REFERENCES scrap_configs(id) ON DELETE CASCADE,
    status          VARCHAR(20) NOT NULL CHECK (status IN ('success', 'error', 'partial')),
    items_count     INTEGER,
    data            JSONB,
    executed_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_scrap_results_config ON scrap_results(config_id);
CREATE INDEX idx_scrap_results_executed ON scrap_results(executed_at DESC);

COMMENT ON TABLE scrap_results IS 'Resultados de execuções de scraping';
COMMENT ON COLUMN scrap_results.status IS 'Status: success, error, partial';
COMMENT ON COLUMN scrap_results.data IS 'JSONB: dados extraídos';

-- ========================================
-- TABELA: rag_documents - 13/02/2026
-- ========================================
-- Documentos RAG para o painel admin

CREATE TABLE rag_documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title           VARCHAR(500) NOT NULL,
    content         TEXT NOT NULL,
    keywords        TEXT[] DEFAULT '{}',
    intents         TEXT[] DEFAULT '{}',
    source          VARCHAR(100) DEFAULT 'manual',
    ativo           BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_rag_documents_ativo ON rag_documents(ativo);
CREATE INDEX idx_rag_documents_title ON rag_documents(title);

COMMENT ON TABLE rag_documents IS 'Documentos RAG para o painel admin';
