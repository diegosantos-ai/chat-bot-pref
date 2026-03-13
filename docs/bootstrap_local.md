# Bootstrap Local Minimo

## Objetivo

Subir o runtime validado atual com Docker e validar os fluxos minimos de:

- healthcheck
- chat com `tenant_id`
- ingest RAG por tenant
- query RAG por tenant
- reset da base

## Escopo

O ambiente local atual sobe apenas o backend `chat-pref-api`.

Isso cobre:

- `GET /`
- `GET /health`
- `POST /api/chat`
- `POST /api/webhook`
- `GET /api/rag/status`
- `POST /api/rag/documents`
- `POST /api/rag/ingest`
- `POST /api/rag/query`
- `POST /api/rag/reset`

Fica fora deste bootstrap:

- painel administrativo como serviço validado
- banco relacional
- Redis
- observabilidade
- integrações externas completas

## Arquivos de ambiente

- `.env.compose`: defaults usados pelo `docker compose`
- `.env.example`: referência para rodar fora do container
- `.env.prod.example`: referência mínima para publicação futura

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
  --phase-report fase8
```

Para validar a base documental ficticia com o smoke completo e relatorio gerencial da fase:

```bash
.venv/bin/python scripts/smoke_tests.py \
  --env prod \
  --tenant-id prefeitura-vila-serena \
  --tenant-manifest tenants/prefeitura-vila-serena/tenant.json \
  --phase-report fase8 \
  --json-out artifacts/fase8-smoke-prod.json
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
- mensagem controlada informando que o tenant ainda nao possui documentos

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
- chat respondendo com `Contexto recuperado`

### 5. Validar isolamento entre tenants

```bash
curl -sS -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"prefeitura-outro","message":"Qual o horario do alvara?"}' && echo
```

Resultado esperado:

- nao reutilizar o contexto de `prefeitura-demo`
- retornar mensagem controlada de base ausente para o outro tenant

### 6. Resetar a base

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
