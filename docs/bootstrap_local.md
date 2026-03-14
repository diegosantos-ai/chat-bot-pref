# Bootstrap Local Minimo

## Objetivo

Subir o runtime validado atual com Docker e validar os fluxos minimos de:

- healthcheck
- chat com `tenant_id`
- composicao generativa minima com `LLM_PROVIDER=mock`
- guardrails e fallback controlado
- ingest RAG por tenant
- query RAG por tenant
- reset da base

## Escopo

O ambiente local atual sobe apenas o backend `chat-pref-api`.

Isso cobre:

- `GET /`
- `GET /health`
- `GET /metrics`
- `POST /api/chat`
- `POST /api/webhook`
- `POST /api/telegram/webhook`
- `GET /api/rag/status`
- `POST /api/rag/documents`
- `POST /api/rag/ingest`
- `POST /api/rag/query`
- `POST /api/rag/reset`

Fica fora deste bootstrap:

- painel administrativo como serviço validado
- banco relacional
- Redis
- integrações externas completas além do Telegram demonstrativo

## Arquivos de ambiente

- `.env.compose`: defaults usados pelo `docker compose`
- `.env.example`: referência para rodar fora do container
- `.env.prod.example`: referência mínima para publicação futura

Variáveis relevantes para o Telegram:

- `TELEGRAM_WEBHOOK_SECRET`
- `TELEGRAM_DEFAULT_TENANT_ID`
- `TELEGRAM_CHAT_TENANT_MAP`
- `TELEGRAM_DELIVERY_MODE`
- `TELEGRAM_BOT_TOKEN`

Variaveis relevantes para a Fase 10 e Fase 11:

- `LLM_PROVIDER`
- `LLM_MODEL`
- `LLM_API_KEY`
- `PROMPT_BASE_VERSION`
- `PROMPT_FALLBACK_VERSION`
- `POLICY_TEXT_VERSION`
- `LLM_MIN_CONTEXT_SCORE`
- `LLM_CONTEXT_TOP_K`

A persistência do ambiente padrão fica no volume Docker `chat_pref_data`.

## Subida padrao

```bash
docker compose -f docker-compose.yml up -d --build
until [ "$(docker inspect -f '{{.State.Health.Status}}' chat-pref-api 2>/dev/null)" = "healthy" ]; do sleep 1; done
curl -sS http://127.0.0.1:8000/health && echo
```

Resultado esperado:

- container `chat-pref-api` em `healthy`
- resposta `{"status":"healthy"}`

## Tenant demonstrativo de validacao

Use um tenant de exemplo apenas para teste local, como `prefeitura-demo`.

O tenant demonstrativo oficial desta fase e `prefeitura-vila-serena`. Para materializar o bundle versionado no runtime local antes de testar fora do Docker:

```bash
.venv/bin/python scripts/bootstrap_demo_tenant.py \
  --manifest tenants/prefeitura-vila-serena/tenant.json \
  --purge-documents \
  --ingest \
  --phase-report fase11
```

Para validar a Fase 11 com o smoke completo e relatorio gerencial da fase:

```bash
.venv/bin/python scripts/smoke_tests.py \
  --env prod \
  --tenant-id prefeitura-vila-serena \
  --tenant-manifest tenants/prefeitura-vila-serena/tenant.json \
  --phase-report fase11 \
  --json-out artifacts/fase11-smoke-prod.json
```

Variante `dev`:

```bash
.venv/bin/python scripts/smoke_tests.py \
  --env dev \
  --tenant-id prefeitura-vila-serena \
  --tenant-manifest tenants/prefeitura-vila-serena/tenant.json \
  --phase-report fase11 \
  --json-out artifacts/fase11-smoke-dev.json
```

Se o ambiente ja estiver levantado e voce quiser reaproveita-lo sem `down` automatico no fim do smoke:

```bash
.venv/bin/python scripts/smoke_tests.py \
  --env prod \
  --runtime-mode reuse \
  --tenant-id prefeitura-vila-serena \
  --tenant-manifest tenants/prefeitura-vila-serena/tenant.json \
  --phase-report fase11 \
  --json-out artifacts/fase11-smoke-prod.json
```

### 1. Validar estado inicial sem base

```bash
curl -sS "http://127.0.0.1:8000/api/rag/status?tenant_id=prefeitura-demo" && echo
curl -sS -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"prefeitura-demo","message":"Qual o horario do alvara?"}' && echo
```

Resultado esperado:

- `ready: false`
- fallback controlado informando que a base institucional ainda nao possui contexto suficiente

### 2. Criar um documento

```bash
curl -sS -X POST http://127.0.0.1:8000/api/rag/documents \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"prefeitura-demo","title":"Atendimento Alvara","content":"O setor de alvara atende das 8h as 17h.\n\nDocumentos podem ser protocolados ate as 16h.","keywords":["alvara","horario"],"intents":["INFO_REQUEST"]}' && echo
```

### 3. Ingerir a base do tenant

```bash
curl -sS -X POST http://127.0.0.1:8000/api/rag/ingest \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"prefeitura-demo","reset_collection":true}' && echo
curl -sS "http://127.0.0.1:8000/api/rag/status?tenant_id=prefeitura-demo" && echo
```

Resultado esperado:

- `documents_count > 0`
- `chunks_count > 0`
- `ready: true`

### 4. Consultar RAG e chat

```bash
curl -sS -X POST http://127.0.0.1:8000/api/rag/query \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"prefeitura-demo","query":"horario do alvara"}' && echo

curl -sS -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"prefeitura-demo","message":"Qual o horario do alvara?"}' && echo
```

Resultado esperado:

- query com `status: "ready"`
- chat respondendo com composicao controlada e referencia aos canais oficiais

### 5. Validar isolamento entre tenants

```bash
curl -sS -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"prefeitura-outro","message":"Qual o horario do alvara?"}' && echo
```

Resultado esperado:

- nao reutilizar o contexto de `prefeitura-demo`
- retornar mensagem controlada de base ausente para o outro tenant

### 6. Validar cenarios controlados das Fases 10 e 11

Rode exemplos simples com `X-Request-ID` para acompanhar a auditoria:

```bash
curl -sS -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: fase10-demo-normal" \
  -d '{"tenant_id":"prefeitura-vila-serena","message":"Qual o horario da sala de vacinacao da UBS?"}' && echo

curl -sS -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: fase10-demo-out-of-scope" \
  -d '{"tenant_id":"prefeitura-vila-serena","message":"Me diga onde investir meu dinheiro"}' && echo

curl -sS -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: fase10-demo-low-confidence" \
  -d '{"tenant_id":"prefeitura-vila-serena","message":"Tem estacionamento no centro?"}' && echo
```

Resultado esperado:

- cenario normal responde com contexto institucional da base
- pergunta fora de escopo responde com fallback institucional
- pergunta de baixa confianca responde com fallback de contexto insuficiente
- o mesmo `request_id` aparece na resposta e na auditoria do tenant

### 7. Validar observabilidade minima da Fase 11

Use o mesmo `request_id` de um cenario controlado para inspecionar metricas, logs e traces:

```bash
curl -sS http://127.0.0.1:8000/metrics | rg "chatpref_(chat_requests_total|policy_decisions_total|retrieval_total|llm_compositions_total|llm_compose_latency_seconds)"

docker exec chat-pref-api sh -lc 'find /app/data/runtime/logs -type f | sort | tail -n 4'
docker exec chat-pref-api sh -lc 'find /app/data/runtime/traces -type f | sort | tail -n 4'
```

Resultado esperado:

- `/metrics` exposto com as series minimas da Fase 11
- arquivo JSONL de logs estruturados por `request_id`
- arquivo JSONL de traces por `request_id`

### 8. Resetar a base

```bash
curl -sS -X POST http://127.0.0.1:8000/api/rag/reset \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"prefeitura-demo","purge_documents":true,"remove_legacy_collections":true}' && echo
curl -sS "http://127.0.0.1:8000/api/rag/status?tenant_id=prefeitura-demo" && echo
```

Resultado esperado:

- colecao atual removida
- possiveis colecoes legadas removidas
- `ready: false`

### 9. Simular webhook do Telegram localmente

O compose padrao sobe o Telegram em `dry_run`, sem depender de token real para o smoke.

```bash
curl -sS -X POST http://127.0.0.1:8000/api/telegram/webhook \
  -H "Content-Type: application/json" \
  -H "X-Telegram-Bot-Api-Secret-Token: telegram-demo-secret" \
  -d '{"update_id":"900001","message":{"message_id":"700001","chat":{"id":"55119990001","type":"private"},"from":{"id":"55119990001","first_name":"Demo"},"text":"Qual o horario do alvara?"}}' && echo
```

Resultado esperado:

- `status: "processed"`
- `tenant_id: "prefeitura-vila-serena"`
- `channel: "telegram"`
- `outbound_status: "dry_run"`

### 10. Configurar webhook real do Telegram

Para um bot real criado no BotFather, use o utilitario abaixo depois de expor uma URL publica HTTPS para a API:

```bash
.venv/bin/python scripts/telegram_webhook.py me
.venv/bin/python scripts/telegram_webhook.py set \
  --webhook-url https://seu-host.exemplo/api/telegram/webhook \
  --secret-token telegram-demo-secret
.venv/bin/python scripts/telegram_webhook.py info
```

Observacao:

- para entrega real, troque `TELEGRAM_DELIVERY_MODE=api`
- configure `TELEGRAM_BOT_TOKEN`
- mantenha `TELEGRAM_DEFAULT_TENANT_ID=prefeitura-vila-serena` ou use `TELEGRAM_CHAT_TENANT_MAP`

## Compose de desenvolvimento

Para subir a mesma API em modo de desenvolvimento (`ENV=dev`, `DEBUG=true`):

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml up --build
```

Para live reload de código, use a execução fora do container:

```bash
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload
```

## Encerramento

```bash
docker compose -f docker-compose.yml down
```
