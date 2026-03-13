# Fase 6 — Validacao Estrutural da Base Refatorada

## Objetivo

Executar uma validacao intermediaria da base refatorada antes da construcao do tenant demonstrativo.

## Escopo validado

- varredura de residuos historicos no runtime ativo
- startup local do backend fora do Docker
- resposta dos endpoints principais
- integracao minima de tenant no fluxo
- validacao do compose padrao e da variante local
- revisao do conjunto de commits estruturais das Fases 3, 4 e 5

## Evidencias executadas

### 1. Varredura de residuos historicos no runtime

Escopo da busca:

- `app/`
- `Dockerfile`
- `docker-compose.yml`
- `docker-compose.local.yml`
- `.env.compose`
- `.env.example`
- `.env.prod.example`

Comandos usados:

```bash
rg -n -S "pilot-atendimento|santa tereza|BA-RAG-PILOTO|terezia" app Dockerfile docker-compose.yml docker-compose.local.yml .env.compose .env.example .env.prod.example
rg -n -S "tenant_id[^\n]{0,80}['\"]default['\"]|tenant default|default tenant|DEFAULT 'default'" app Dockerfile docker-compose.yml docker-compose.local.yml .env.compose .env.example .env.prod.example
```

Resultado:

- `0` ocorrencias dos termos historicos proibidos no runtime validado
- `0` ocorrencias de `tenant default` explicito no runtime validado

Observacao:

- ainda existem referencias fora do runtime ativo em `db/`, `docs/`, `tests/` e em artefatos auxiliares; elas nao afetam o comportamento minimo validado, mas seguem como residuos a serem revisitados nas fases futuras

### 2. Startup local do backend

Comando usado:

```bash
env WEBHOOK_PAGE_TENANT_MAP='{"page-demo":"prefeitura-demo"}' .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8010
```

Validacoes locais executadas:

- `GET /`
- `GET /health`
- `POST /api/chat` sem `tenant_id`
- `POST /api/chat` com `tenant_id`
- `POST /api/webhook` com `page_id` mapeado

Resultados observados:

- backend sobe normalmente fora do Docker
- `/` respondeu `200`
- `/health` respondeu `{"status":"healthy"}`
- `/api/chat` sem `tenant_id` respondeu `400 tenant_id obrigatório`
- `/api/chat` com `tenant_id` respondeu mensagem controlada de base ausente
- `/api/webhook` com `page_id` mapeado resolveu `tenant_id` corretamente

### 3. Smoke tests automatizados

Script usado:

- [scripts/smoke_tests.py](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/scripts/smoke_tests.py)

Artefatos gerados:

- [artifacts/smoke-prod.json](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/artifacts/smoke-prod.json)
- [artifacts/smoke-dev.json](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/artifacts/smoke-dev.json)

Comandos usados:

```bash
.venv/bin/python scripts/smoke_tests.py --env prod --json-out artifacts/smoke-prod.json
.venv/bin/python scripts/smoke_tests.py --env dev --json-out artifacts/smoke-dev.json
```

Resultado:

- `prod`: `11/11` etapas aprovadas
- `dev`: `11/11` etapas aprovadas

Fluxos cobertos:

- subida do ambiente
- healthcheck do container
- `GET /`
- `GET /health`
- comportamento do RAG vazio
- criacao de documento
- ingest da base
- consulta direta ao RAG
- consulta via `/api/chat`
- reset da base
- encerramento do ambiente

### 4. Revisao do diff estrutural

Commits revisados:

- `f0b151e` — fechamento da Fase 3
- `2b22b06` — fechamento da Fase 4
- `748dc37` — fechamento da Fase 5

Leitura estrutural do diff:

- Fase 3 consolidou contrato explicito de `tenant_id`, webhook minimo, contexto de tenant, auditoria e retrieval por tenant
- Fase 4 separou historico de chat da base RAG, adicionou CRUD documental, ingest por tenant, reset controlado e scripts de operacao
- Fase 5 consolidou Dockerfile, Compose, variaveis padronizadas e bootstrap local minimo

Conclusao do review:

- o nucleo refatorado evoluiu de contrato multi-tenant minimo para RAG limpo por tenant e, depois, para ambiente local reproduzivel
- nao ha evidencia de dependencia estrutural do runtime minimo com identidades historicas antigas
- os residuos encontrados hoje estao fora do runtime validado atual

## Fechamento por task

- `CPP-F6-T1`: concluida com varredura intermediaria do runtime e ausencia de hit relevante nos termos historicos proibidos
- `CPP-F6-T2`: concluida com startup local do backend em `uvicorn`
- `CPP-F6-T3`: concluida com validacao de `/`, `/health`, `/api/chat` e `/api/webhook`
- `CPP-F6-T4`: concluida com validacao minima de `tenant_id` no chat e resolucao por `page_id` no webhook
- `CPP-F6-T5`: concluida com revisao objetiva dos commits estruturais das Fases 3 a 5
- `CPP-F6-T6`: concluida com consolidacao de evidencias em relatorio e artefatos JSON de smoke

## Riscos residuais

- `db/migrations/001_multi_tenant_rls.sql` ainda carrega referencias antigas de `default` em uma trilha de banco fora do runtime minimo atual
- `docs/` e `README.md` mantem a stack-alvo e itens planejados; isso e intencional na branch de desenvolvimento, mas exige disciplina para nao vender como runtime ativo
- `admin-panel/eslint_report.json` contem ruido historico e caminhos Windows, fora do escopo do runtime minimo validado

## Conclusao

A base refatorada passou por uma validacao estrutural intermediaria suficiente para abrir as fases de tenant demonstrativo e base documental ficticia.

No escopo ativo atual:

- backend sobe
- endpoints principais respondem
- tenant-aware minimo funciona
- compose padrao e compose local validam
- o runtime minimo nao depende de residuos historicos relevantes
