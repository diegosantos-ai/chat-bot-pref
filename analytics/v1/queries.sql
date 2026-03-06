-- Analytics SQL: Auditoria e Observabilidade (CityBot)
-- Banco: PostgreSQL 15+
-- Uso: Execute sob o schema criado por db/schema.sql

-- 1) Últimas 100 interações (visão geral)
SELECT
  criado_em,
  id_requisicao,
  id_sessao,
  canal,
  tipo_superficie,
  intencao,
  decisao_politica,
  decisao,
  tipo_resposta,
  motivo_fallback,
  codigo_erro,
  tempo_resposta_ms,
  modelo,
  versao_prompt,
  versao_app
FROM audit_events
ORDER BY criado_em DESC
LIMIT 100;

-- 2) Volume por tipo de resposta nas últimas 24h
SELECT
  tipo_resposta,
  COUNT(*) AS total
FROM audit_events
WHERE criado_em >= now() - INTERVAL '24 hours'
GROUP BY tipo_resposta
ORDER BY total DESC;

-- 3) Fallbacks por motivo nas últimas 24h
SELECT
  motivo_fallback,
  COUNT(*) AS total
FROM audit_events
WHERE criado_em >= now() - INTERVAL '24 hours'
  AND tipo_resposta = 'FALLBACK'
GROUP BY motivo_fallback
ORDER BY total DESC;

-- 4) Possíveis crises (bloqueios/escalações) nas últimas 48h
-- Ajuste o filtro de block_reason conforme regras do policy_guard
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

-- 5) Erros por tipo de exceção nas últimas 24h
SELECT
  tipo_excecao,
  codigo_erro,
  COUNT(*) AS total
FROM audit_events
WHERE criado_em >= now() - INTERVAL '24 hours'
  AND codigo_erro IS NOT NULL
GROUP BY tipo_excecao, codigo_erro
ORDER BY total DESC;

-- 6) Tempo médio de resposta por canal (últimas 24h)
SELECT
  canal,
  AVG(tempo_resposta_ms)::INT AS avg_ms,
  PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY tempo_resposta_ms) AS p90_ms,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY tempo_resposta_ms) AS p95_ms
FROM audit_events
WHERE criado_em >= now() - INTERVAL '24 hours'
GROUP BY canal
ORDER BY avg_ms;

-- 7) Interações públicas com possível PII (heurística) nas últimas 24h
-- Ajuste o regex conforme política de privacidade/PAI
SELECT
  criado_em,
  canal,
  tipo_superficie,
  id_requisicao,
  motivo_bloqueio
FROM audit_events
WHERE criado_em >= now() - INTERVAL '24 hours'
  AND tipo_superficie = 'public_comment'
  AND (
    COALESCE(motivo_bloqueio,'') ILIKE '%pii%' OR
    COALESCE(motivo_bloqueio,'') ILIKE '%privac%'
  )
ORDER BY criado_em DESC;

-- 8) Join com RAG: consultas sem documentos retornados (últimas 24h)
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

-- 9) Join com RAG: top_score baixo (sinal de conteúdo faltante)
SELECT
  e.criado_em,
  e.canal,
  r.melhor_score,
  r.quantidade_documentos,
  e.tipo_resposta,
  e.id_requisicao
FROM rag_queries r
JOIN audit_events e ON e.id_requisicao = r.id_requisicao
WHERE e.criado_em >= now() - INTERVAL '7 days'
  AND r.melhor_score IS NOT NULL
ORDER BY r.melhor_score ASC
LIMIT 100;

-- 10) Distribuição de intents (7 dias)
SELECT
  intencao,
  COUNT(*) AS total
FROM audit_events
WHERE criado_em >= now() - INTERVAL '7 days'
GROUP BY intencao
ORDER BY total DESC;
