# Copilot Instructions

## Fonte de verdade

Leia nesta ordem:

1. `AGENTS.md`
2. `README.md`
3. `docs/contexto.md`
4. `docs/arquitetura.md`
5. `docs/planejamento_fases.md`

Se a task tocar as Fases 9 a 12, leia tambem:

6. `docs/guardrail_rastreavel.md`
7. `docs/genai_com_metodo.md`

Se a task tocar as Fases 10 a 12, consulte tambem:

8. `docs/matriz_cenarios_validacao.md`
9. `docs/rubrica_qualidade_resposta.md`

Use `.github/agents/`, `.ai/skills/` e `.ai/workflows/` como camada ativa de governança.

## Estado atual do projeto

O runtime ativo atual é uma base mínima reconstruída, mas já validada além do chat direto.

Escopo implementado:

- FastAPI mínimo
- `GET /`
- `GET /health`
- `POST /api/chat`
- `POST /api/webhook`
- `POST /api/telegram/webhook`
- `GET /api/rag/status`
- `POST /api/rag/documents`
- `POST /api/rag/ingest`
- `POST /api/rag/query`
- `POST /api/rag/reset`
- `tenant_id` explícito no chat direto
- `X-Request-ID` propagado no chat e no webhook
- contexto de tenant por request
- persistência local por tenant
- auditoria `audit.v1` por tenant
- RAG tenant-aware com ingest limpa
- composição generativa mínima com `LLM_PROVIDER=mock`
- prompts e política textual versionados
- `policy_pre` e `policy_post` com `PolicyDecision`
- tenant demonstrativo e base documental fictícia
- integração Telegram demonstrativa com entrega `dry_run`
- Docker funcional
- smoke tests e retrieval checks

Não assuma como ativos no runtime atual:

- bot Telegram configurado com token real e webhook publico externo
- provedor LLM externo real validado como caminho padrão reproduzível
- logs estruturados
- `/metrics`
- traces com OpenTelemetry
- painel/admin no caminho crítico
- banco relacional como dependência operacional
- CI e deploy em nuvem como parte do runtime da branch

## Guardrails de alteração

- mantenha mudanças mínimas e ligadas a uma fase/task
- não trate arquitetura futura como se já estivesse implementada
- não reintroduza arquivos, termos ou estruturas históricas removidas
- `tenant_id` é contrato explícito, não detalhe opcional
- preserve o contrato mínimo de `request_id` nos fluxos que já o expõem
- não versione `.env` real nem segredos
- se a alteração impactar arquitetura, tenant, RAG, guardrails, Docker ou operação, atualize a documentação correspondente
- nas Fases 9 a 12, siga `docs/guardrail_rastreavel.md` e `docs/genai_com_metodo.md` como referência de contrato

## Áreas ativas principais

- `app/main.py`
- `app/settings.py`
- `app/api/`
- `app/contracts/`
- `app/services/`
- `app/storage/`
- `app/tenant_context.py`
- `app/tenant_resolver.py`
- `scripts/`
- `tenants/`
- `docs/`
- `tests/`
- `docker-compose.yml`
- `docker-compose.local.yml`

## Áreas fora do caminho crítico atual

Diretórios como `admin-api/`, `admin-panel/`, `db/`, `panel/`, `logging/`, `dashboards/`, `grafana/` e afins não devem ser assumidos como parte do runtime mínimo validado sem confirmação explícita da task.

## Validação mínima recomendada

Use apenas validações coerentes com a task. Exemplos:

- `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
- `.venv/bin/python -m pytest tests -q`
- `docker compose -f docker-compose.yml config`
- `docker compose -f docker-compose.yml up -d --build`
- `curl http://localhost:8000/`
- `curl http://localhost:8000/health`
- `curl -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" -d '{"tenant_id":"prefeitura-demo","message":"Teste"}'`
- `curl -X POST http://localhost:8000/api/webhook -H "Content-Type: application/json" -d '{"tenant_id":"prefeitura-demo","message":"Teste"}'`
- `curl "http://localhost:8000/api/rag/status?tenant_id=prefeitura-demo"`
- `.venv/bin/python scripts/smoke_tests.py --env prod --tenant-id prefeitura-vila-serena --tenant-manifest tenants/prefeitura-vila-serena/tenant.json --phase-report fase10`

## Forma de trabalho

- explique o bloco antes de mudanças maiores
- faça o menor corte que produza valor real
- valide imediatamente depois
- diferencie explicitamente o que ja existe no runtime, o que e contrato planejado e o que e apenas stack-alvo
- feche cada tarefa informando:
  - arquivos alterados
  - validação executada
  - status atual
  - próximo passo
