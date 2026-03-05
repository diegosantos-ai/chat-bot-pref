# Runbook - {bot_name}

## Escopo
- Deploy e rollback da API
- Health-checks e observabilidade
- Resposta a incidentes (erros, queda, dados)

## Contatos / Escalonamento
- Dev responsável: Diego Santos — (45) 99929-8275 — santos.diego.86@gmail.com
- Ops/Infra: Diego Santos — (45) 99929-8275 — santos.diego.86@gmail.com
- Responsável pela validação: Diego Santos — (45) 99929-8275 — santos.diego.86@gmail.com
- Horário comercial: 09h–18h | Fora do horário: acionar Ops

## Pré-requisitos
- `.env` preenchido (chaves Meta, DB, Gemini, etc.)
- Banco PostgreSQL acessível (`DATABASE_URL`)
- Porta APP_PORT liberada (padrao 8000)
- Prometheus scraping habilitado na rota `/metrics`
- Grafana apontando para o Postgres com as views criadas

## Deploy (Docker)
1) Build da imagem:
```bash
docker build -t terezia-api:latest .
```
2) Rodar container (exemplo):
```bash
docker run -d --name terezia-api -p 8000:8000 --env-file .env terezia-api:latest
```
   - Variáveis chave: `LOG_LEVEL`, `LOG_JSON`, `DATABASE_URL`, `GEMINI_API_KEY`.
3) Health-check:
```bash
curl -f http://localhost:8000/health
```
4) Prometheus: verificar `http://localhost:8000/metrics`.
5) Grafana: importar `grafana/dashboard_terezia.json` e usar datasource Postgres existente.

## Rollback
1) Manter a imagem anterior tagueada (ex: `terezia-api:prev`).  
2) Para retornar:
```bash
docker stop terezia-api && docker rm terezia-api
docker run -d --name terezia-api -p 8000:8000 --env-file .env terezia-api:prev
```
3) Validar `/health` e dashboard.
4) Se o problema for dados ou schema, restaurar backup do Postgres (ver seção “Backup/Restore”).

## Logs e Observabilidade
- Logs: JSON no stdout (config em `LOG_JSON=true`, `LOG_LEVEL`).
- Métricas: Prometheus em `/metrics` via `prometheus-fastapi-instrumentator`.
- StatsD (opcional): ativar com `METRICS_STATSD_ENABLED=true` apontando para host/porta.
- Views SQL: executar `python scripts/create_views.py` (usa `analytics/v1/views.sql`).
- Principais KPIs no dashboard:
  - Latência p95 por canal (query no dashboard).
  - Fallback rate por canal (24h).
  - Erros por canal (24h).
  - RAG sem documentos (24h).

## Resposta a Incidentes
1) **API fora** (`/health` falha): verificar container/logs; se imagem nova, rollback imediato.
2) **Erros 5xx altos**: olhar logs JSON e painel de erros por canal; validar credenciais de DB/Meta.
3) **Latência alta**: verificar DB (`pg_stat_activity`), fila de logs, recursos do host; escalar recursos; checar Prometheus.
4) **Fallback spike**: ver painel de fallbacks; conferir base RAG e políticas (policy guard).
5) **Crises (suicídio/violência)**: verificar bloqueios no dashboard, garantir respostas estáticas foram enviadas.

## Backup e Restauração (PostgreSQL)
- Backup (Windows, sem depender de `psql/pg_dump`):
```bash
python scripts/backup_postgres.py --gzip --verify
python scripts/backup_chroma.py
```
- Agendamento (Windows Task Scheduler):
  - Tarefa: `{bot_name}-Backup` (diário 02:00)
  - Runner: `scripts/backup_all.ps1 -Gzip -Verify`
- Saída padrão:
  - `artifacts/backups/postgres/<timestamp>/`
  - `artifacts/backups/chroma/<timestamp>/`
  - `artifacts/backups/task_logs/` (logs do agendamento)
- Testar restauração em base de teste antes de produção (procedimento depende da estratégia do DBA/infra).

## Testes rápidos pós-deploy
- `/health` -> 200
- `/api/chat/simple?message=teste` -> resposta 200
- Prometheus `/metrics` acessível
- Grafana carrega painel com dados das últimas 24h
