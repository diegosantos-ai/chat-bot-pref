# Fase 10 - Composicao Generativa, Guardrails e Evidencias

## Objetivo

Introduzir a camada generativa minima do Chat Pref sobre o contexto recuperado, mantendo o contrato multi-tenant, guardrails executaveis e evidencias rastreaveis por `request_id`.

## O que foi entregue

- adaptador LLM isolado em `app/services/llm_service.py`
- composicao controlada com `LLM_PROVIDER=mock` como default e suporte opcional a `gemini`
- `PromptService` com `base_v1`, `fallback_v1` e `policy_v1`
- `TenantProfileService` para voz institucional e escopo do tenant demonstrativo
- `PolicyDecision` padronizado em `policy_pre` e `policy_post`
- `AuditEventRecord` versionado em `audit.v1` com `event_id`, `channel` e `policy_decision`
- correlacao minima por `request_id` com suporte a `X-Request-ID` em `POST /api/chat` e `POST /api/webhook`
- smoke da fase com cenarios controlados e rubrica objetiva de resposta

## Criterios de aceite validados

- adaptador de provedor LLM implementado e isolado do restante da aplicacao
- composicao de resposta limitada ao contexto recuperado e ao escopo institucional
- prompts e politicas versionados
- `policy_pre` e `policy_post` executados com `reason_codes`
- cenarios normais, fora de escopo, baixa confianca e risco validados
- evidencias registradas com correlacao minima por `request_id`
- comportamento alinhado ao escopo institucional do tenant ficticio

## Cenarios validados

- `SCN-01` pergunta normal com resposta contextual da base
- `SCN-02` pergunta fora de escopo com bloqueio `OUT_OF_SCOPE`
- `SCN-04` retrieval de baixa confianca com fallback `LOW_CONFIDENCE_RETRIEVAL`
- `SCN-05` acao transacional nao suportada com bloqueio `UNSUPPORTED_TRANSACTIONAL_ACTION`
- `SCN-06` situacao de crise ou risco com bloqueio `CRISIS_OR_MEDICAL_RISK`

Todos os cenarios foram aprovados com:

- `request_id` correlacionado no request, resposta e auditoria
- rubrica de qualidade em `passed`
- prompt e policy versionados identificaveis nos eventos

## Validacao executada

- `.venv/bin/python -m pytest tests -q`
- `.venv/bin/python scripts/smoke_tests.py --env prod --tenant-id prefeitura-vila-serena --tenant-manifest tenants/prefeitura-vila-serena/tenant.json --phase-report fase10 --json-out artifacts/fase10-smoke-prod.json`
- `.venv/bin/python scripts/smoke_tests.py --env dev --tenant-id prefeitura-vila-serena --tenant-manifest tenants/prefeitura-vila-serena/tenant.json --phase-report fase10 --json-out artifacts/fase10-smoke-dev.json`

## Artefatos

- `artifacts/fase10-smoke-prod.json`
- `artifacts/fase10-smoke-dev.json`

## Evidencia operacional

O smoke da fase aprovou `7/7` criterios de aceite em `prod` e `dev`, com:

- `26` testes automatizados aprovados
- `5/5` cenarios de guardrail aprovados
- prompts `base_v1` e `fallback_v1` rastreaveis
- `policy_v1` presente nos eventos de policy
- reescrita controlada para fallback quando a `policy_post` identificou baixa confianca
