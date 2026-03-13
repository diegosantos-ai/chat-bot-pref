# Copilot Instructions

## Fonte de verdade
- Leia primeiro `AGENTS.md`, `docs/contexto.md`, `docs/arquitetura.md` e `docs/planejamento_fases.md`.
- Leia o `README.md` da raiz como referencia principal.
- Use `.github/agents/`, `.ai/skills/` e `.ai/workflows/` como camada ativa de governanca de agentes.
- Trate `.agent_legacy/` apenas como referencia historica congelada.

## Escopo atual
- O projeto esta em refatoracao controlada para consolidar arquitetura FastAPI + RAG + multi-tenant.
- `tenant_id` e contrato arquitetural explicito. Nao introduza fallback silencioso.
- Prioridade atual: diagnostico, sanitizacao do runtime, consolidacao do fluxo de tenant, preparo para demo e validacao.

## Guardrails de alteracao
- Mantenha mudancas minimas, rastreaveis e ligadas a uma fase/task do planejamento.
- Nao altere runtime sem necessidade direta da task.
- Nao versiona credenciais reais, `.env` real ou tokens em areas ativas.
- Nao use `.agent_legacy/` como base para novos arquivos sem filtragem explicita do que e reaproveitavel.
- Se a mudanca afetar arquitetura, tenant, ingest, Docker, GitHub Actions ou AWS/Terraform, atualize a documentacao correspondente.

## Areas principais
- `app/`: backend FastAPI, orchestrator, RAG, auditoria, tenant context/resolver.
- `db/`: schema e migrations.
- `scripts/`: utilitarios operacionais.
- `admin-panel/` e `nexo-admin/`: interfaces auxiliares.
- `.github/workflows/`: CI/CD.
- `.ai/`: skills e workflows operacionais para agentes.

## Validacao minima
- Use apenas validacoes coerentes com a task.
- Exemplos comuns:
  - `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
  - `pytest`
  - `docker compose config`
  - buscas por hardcodes e residuos historicos com `rg`
- Sempre registre o que foi alterado, como validou, estado atual e proximo passo.
