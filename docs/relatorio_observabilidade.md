# Relatorio - Observabilidade, Deploy e Runbook

## Resumo breve
- Logs estruturados JSON + StatsD opcional ativados por env.
- Views SQL atualizadas e aplicadas com p95.
- Dashboard inicial no Grafana com KPIs (latencia p95, fallback rate, erros).
- Deploy preparado com Dockerfile e health-checks.
- Runbook criado com deploy, rollback e incidentes.
- Guardrails de crise testados com respostas estaticas e bloqueios seguros.

## O que foi feito
- Logging JSON global: `app/logging_config.py` e `app/main.py`.
- StatsD opcional: `app/metrics.py` e hook em `app/analytics.py`.
- Configs novas: `app/settings.py` e `.env.example`.
- Views analytics: `analytics/v1/views.sql` (p95 adicionado) e aplicadas.
- Queries analytics: `analytics/v1/queries.sql` (p95 adicionado).
- Dashboard Grafana: `grafana/dashboard_terezia.json` com datasource UID configurado.
- Deploy Docker: `Dockerfile` + `.dockerignore`.
- Runbook: `docs/runbook.md` com contatos e procedimentos.
- Testes de crise/PII: `tests/e2e/test_pipeline_e2e.py` (suicidio, violencia, PII em publico).

## Como conferir
- Health-check: `http://localhost:8000/health`
- Prometheus: `http://localhost:8000/metrics`
- Views SQL: execute `python scripts/create_views.py`
- Dashboard: importar `grafana/dashboard_terezia.json` no Grafana.
- Testes E2E: `pytest tests/e2e/test_pipeline_e2e.py`

## Serviços auxiliares (PostgreSQL + ChromaDB)

### PostgreSQL
- Conectividade validada via `scripts/ops/validate_infrastructure.py` (9/9 OK).
- `pgcrypto` instalado: `pgcrypto_installed=True` (necessário para `gen_random_uuid()`).
- Schema aplicado e tabelas presentes: `audit_events`, `rag_queries`, `usuarios_anonimos`, `conversas`.

### ChromaDB
- Arquitetura atual: **embarcado** (ChromaDB `PersistentClient`), sem serviço separado.
- Persistência validada em `./chroma_data` com collection `settings.RAG_COLLECTION_NAME`.

### Backups (agendado e testado)
- Scripts:
  - `scripts/backup_postgres.py` (backup lógico via `COPY` em CSV, sem depender de `psql/pg_dump`)
  - `scripts/backup_chroma.py` (zip do diretório `CHROMA_PERSIST_DIR`)
  - `scripts/backup_all.ps1` (orquestra ambos + log)
- Saída:
  - `artifacts/backups/postgres/<timestamp>/`
  - `artifacts/backups/chroma/<timestamp>/`
  - Logs do agendamento: `artifacts/backups/task_logs/`
- Agendamento Windows (Task Scheduler):
  - Tarefa criada: `TerezIA-Backup` (diário 02:00)
  - Execução manual testada com sucesso (último resultado 0)

## Checklist (OK)
- [x] Logs estruturados JSON configurados e ativos via env.
- [x] Exportador Prometheus ativo em `/metrics`.
- [x] StatsD opcional configurado e integrado ao analytics.
- [x] Views de observabilidade criadas e aplicadas (inclui p95).
- [x] Dashboard inicial Grafana pronto com KPIs principais.
- [x] Health-check respondendo em `/health`.
- [x] Deploy via Docker preparado (Dockerfile + .dockerignore).
- [x] Runbook criado com deploy, rollback e incidentes.
- [x] Testes de crise (suicidio/violencia) retornam respostas estaticas aprovadas.
- [x] Sem vazamento de PII em respostas publicas (NO_REPLY).
- [x] Testes automatizados de crise/PII criados e verdes.

## Arquivos principais
- `app/logging_config.py`
- `app/metrics.py`
- `app/analytics.py`
- `app/settings.py`
- `.env.example`
- `analytics/v1/views.sql`
- `analytics/v1/queries.sql`
- `grafana/dashboard_terezia.json`
- `Dockerfile`
- `.dockerignore`
- `docs/runbook.md`
