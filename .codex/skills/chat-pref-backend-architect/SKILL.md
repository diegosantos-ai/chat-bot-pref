---
name: chat-pref-backend-architect
description: Usar no repositorio Chat Pref quando a tarefa tocar FastAPI, `app/api/`, `app/services/`, `tenant_id`, `request_id`, `tenant_context`, `tenant_resolver` ou contratos HTTP do runtime validado. Acionar em mudancas de chat, webhook, Telegram, observabilidade correlacionada ou refatoracao pequena do backend.
---

# Chat Pref Backend Architect

Preservar o runtime validado do Chat Pref enquanto endpoints, services e contratos HTTP evoluem com `tenant_id` explicito e `request_id` correlacionado.

## Ler antes de editar

- `AGENTS.md`
- `README.md`
- `docs-fundacao-operacional/contexto.md`
- `docs-fundacao-operacional/arquitetura.md`
- `docs-fundacao-operacional/planejamento_fases.md`
- Se a task tocar LLMOps: `docs-LLMOps/README.md`, `docs-LLMOps/CONTEXTO-LLMOps.md`, `docs-LLMOps/ARQUITETURA-LLMOps.md` e `docs-LLMOps/PLANEJAMENTO-LLMOps.md`
- `.github/agents/backend-architect.agent.md`
- `.ai/skills/validate-runtime.md`
- `.ai/skills/validate-tenant-flow.md`
- `.ai/workflows/refatoracao-fase.md`

## Workflow

1. Identificar endpoint, service e contrato afetados.
2. Rastrear a entrada, a propagacao e o consumo de `tenant_id`.
3. Rastrear `request_id` quando o fluxo tocar `POST /api/chat`, `POST /api/webhook`, `POST /api/telegram/webhook`, auditoria, logs ou traces.
4. Alterar a menor fronteira possivel entre `app/api/`, `app/services/`, `app/tenant_context.py` e `app/tenant_resolver.py`.
5. Preservar o comportamento funcional herdado da Fundacao Operacional.
6. Validar somente o fluxo impactado.

## Guardrails

- Nao introduzir default silencioso para tenant, base RAG ou collection.
- Nao tratar `app/orchestrator/`, `app/classifier/` ou tracking experimental como runtime ativo sem validacao correspondente.
- Preservar a separacao entre operacao, auditoria operacional e experimentacao.
- Se o pedido estiver amplo, usar primeiro `chat-pref-phase-workflow`.

## Validacao sugerida

- Subida do backend com `python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000` ou o interpretador do ambiente do repo
- `python3 -m pytest tests -q` ou escopo menor quando a task permitir
- `GET /`, `GET /health` e o endpoint impactado
- `python3 scripts/check_runtime_residues.py` quando a mudanca for estrutural
