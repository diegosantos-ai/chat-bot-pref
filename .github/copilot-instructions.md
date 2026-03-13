# Copilot Instructions

## Fonte de verdade

Leia nesta ordem:

1. `AGENTS.md`
2. `README.md`
3. `docs/contexto.md`
4. `docs/arquitetura.md`
5. `docs/planejamento_fases.md`

Use `.github/agents/`, `.ai/skills/` e `.ai/workflows/` como camada ativa de governança.

## Estado atual do projeto

O runtime ativo atual é uma base mínima reconstruída.

Escopo implementado:

- FastAPI mínimo
- `GET /`
- `GET /health`
- `POST /api/chat`
- `tenant_id` explícito no chat direto
- contexto de tenant por request
- persistência local por tenant
- auditoria mínima por tenant
- Docker funcional
- testes mínimos

Não assuma como ativos no runtime atual:

- webhook
- RAG
- painel/admin no caminho crítico
- integrações externas
- banco relacional
- observabilidade completa

## Guardrails de alteração

- mantenha mudanças mínimas e ligadas a uma fase/task
- não trate arquitetura futura como se já estivesse implementada
- não reintroduza arquivos, termos ou estruturas históricas removidas
- `tenant_id` é contrato explícito, não detalhe opcional
- não versione `.env` real nem segredos
- se a alteração impactar arquitetura, tenant, Docker ou operação, atualize a documentação correspondente

## Áreas ativas principais

- `app/main.py`
- `app/settings.py`
- `app/api/`
- `app/contracts/`
- `app/services/`
- `app/storage/`
- `app/tenant_context.py`
- `tests/`
- `docker-compose.yml`
- `docker-compose.local.yml`

## Áreas fora do caminho crítico atual

Diretórios como `admin-api/`, `admin-panel/`, `db/`, `panel/`, `prompts/`, `data/knowledge_base/` e afins não devem ser assumidos como parte do runtime mínimo validado sem confirmação explícita da task.

## Validação mínima recomendada

Use apenas validações coerentes com a task. Exemplos:

- `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
- `.venv/bin/python -m pytest tests -q`
- `docker compose -f docker-compose.yml config`
- `docker compose -f docker-compose.yml up -d --build`
- `curl http://localhost:8000/`
- `curl http://localhost:8000/health`
- `curl -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" -d '{"tenant_id":"prefeitura-demo","message":"Teste"}'`

## Forma de trabalho

- explique o bloco antes de mudanças maiores
- faça o menor corte que produza valor real
- valide imediatamente depois
- feche cada tarefa informando:
  - arquivos alterados
  - validação executada
  - status atual
  - próximo passo
