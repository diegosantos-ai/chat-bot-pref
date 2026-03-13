-- Views de Observabilidade — CityBot
-- Execute no banco de produção (PostgreSQL)

-- 1) Eventos das últimas 24h
CREATE OR REPLACE VIEW v_events_last_24h AS
SELECT *
FROM audit_events
WHERE criado_em >= now() - INTERVAL '24 hours';

-- 2) Desempenho por canal (24h)
CREATE OR REPLACE VIEW v_perf_channel_24h AS
SELECT
  canal,
  AVG(tempo_resposta_ms)::INT AS avg_ms,
  PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY tempo_resposta_ms) AS p90_ms,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY tempo_resposta_ms) AS p95_ms,
  COUNT(*) AS total
FROM audit_events
WHERE criado_em >= now() - INTERVAL '24 hours'
GROUP BY canal;

-- 3) Fallbacks por motivo (24h)
CREATE OR REPLACE VIEW v_fallbacks_24h AS
SELECT
  motivo_fallback,
  COUNT(*) AS total
FROM audit_events
WHERE criado_em >= now() - INTERVAL '24 hours'
  AND tipo_resposta = 'FALLBACK'
GROUP BY motivo_fallback
ORDER BY total DESC NULLS LAST;

-- 4) Erros por tipo (24h)
CREATE OR REPLACE VIEW v_errors_24h AS
SELECT
  tipo_excecao,
  codigo_erro,
  COUNT(*) AS total
FROM audit_events
WHERE criado_em >= now() - INTERVAL '24 hours'
  AND codigo_erro IS NOT NULL
GROUP BY tipo_excecao, codigo_erro
ORDER BY total DESC;

-- 5) Crises e bloqueios (48h)
CREATE OR REPLACE VIEW v_crisis_48h AS
SELECT
  criado_em,
  canal,
  tipo_superficie,
  decisao_politica,
  motivo_bloqueio,
  decisao,
  tipo_resposta,
  id_requisicao
FROM audit_events
WHERE criado_em >= now() - INTERVAL '48 hours'
  AND (
    decisao_politica = 'BLOCK' OR
    decisao = 'ESCALATE' OR
    COALESCE(motivo_bloqueio,'') ILIKE '%suic%' OR
    COALESCE(motivo_bloqueio,'') ILIKE '%viol%'
  )
ORDER BY criado_em DESC;

-- 6) RAG sem documentos (24h)
CREATE OR REPLACE VIEW v_rag_no_docs_24h AS
SELECT
  e.criado_em,
  e.canal,
  e.tipo_resposta,
  r.top_k,
  r.quantidade_documentos,
  r.sem_documentos,
  r.melhor_score,
  e.id_requisicao
FROM rag_queries r
JOIN audit_events e ON e.id_requisicao = r.id_requisicao
WHERE e.criado_em >= now() - INTERVAL '24 hours'
  AND r.sem_documentos = TRUE
ORDER BY e.criado_em DESC;

-- 7) Distribuição de intents (7 dias)
CREATE OR REPLACE VIEW v_intents_7d AS
SELECT
  intencao,
  COUNT(*) AS total
FROM audit_events
WHERE criado_em >= now() - INTERVAL '7 days'
GROUP BY intencao
ORDER BY total DESC;
