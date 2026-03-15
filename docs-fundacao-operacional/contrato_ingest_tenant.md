# Contrato de Ingest por Tenant

## 1. Objetivo

Este documento registra o contrato mínimo da Fase 4 para cadastro de documentos, ingestão no Chroma e consulta por tenant.

Ele descreve apenas o que está implementado na base nova.

## 2. Princípios

- `tenant_id` é obrigatório em todo fluxo de documento, ingest e query RAG
- a base documental é separada do histórico de conversa
- a collection ativa do Chroma não é hardcoded
- ausência de base ingerida gera resposta controlada e rastreável

## 3. Estrutura local

### Documentos fonte

Path base:

```text
data/knowledge_base/<tenant_id>/documents/
```

Cada documento é salvo como um arquivo `.json` contendo:

- `title`
- `content`
- `keywords`
- `intents`
- timestamps de criação e atualização

### Status da ingestão

Path:

```text
data/knowledge_base/<tenant_id>/ingest_status.json
```

Esse arquivo registra:

- última ingestão executada
- quantidade de documentos
- quantidade de chunks
- collections removidas no reset

### Collections do Chroma

Path base:

```text
data/chroma/
```

Regra:

- a collection atual usa o prefixo configurável `chat_pref_docs`
- collections antigas com prefixos legados podem ser removidas no reset
- o nome efetivo da collection deriva do `tenant_id`

## 4. Endpoints ativos

### Status

- `GET /api/rag/status?tenant_id=<tenant_id>`

Retorna:

- collection atual
- diretório fonte
- quantidade de documentos
- quantidade de chunks
- status `ready`
- mensagem operacional

### Documentos

- `GET /api/rag/documents?tenant_id=<tenant_id>`
- `GET /api/rag/documents/{document_id}?tenant_id=<tenant_id>`
- `POST /api/rag/documents`
- `PUT /api/rag/documents/{document_id}`
- `DELETE /api/rag/documents/{document_id}?tenant_id=<tenant_id>`

### Ingestão

- `POST /api/rag/ingest`

Payload mínimo:

```json
{
  "tenant_id": "prefeitura-demo",
  "reset_collection": true
}
```

### Reset

- `POST /api/rag/reset`

Payload exemplo:

```json
{
  "tenant_id": "prefeitura-demo",
  "purge_documents": false,
  "remove_legacy_collections": true
}
```

### Query

- `POST /api/rag/query`

Payload exemplo:

```json
{
  "tenant_id": "prefeitura-demo",
  "query": "Qual o horário do alvará?",
  "min_score": 0.1,
  "top_k": 3,
  "boost_enabled": false
}
```

## 5. Comportamentos controlados

### Tenant sem documentos

O status e a query retornam mensagem explícita:

```text
Base de conhecimento do tenant '<tenant_id>' ainda não possui documentos.
```

### Tenant com documentos sem ingestão

O status e a query retornam mensagem explícita:

```text
Documentos do tenant '<tenant_id>' existem, mas a ingestão ainda não foi executada.
```

### Reset

O reset remove:

- a collection atual do tenant
- collections legadas compatíveis com o tenant
- opcionalmente os documentos fonte

## 6. Scripts locais

Os scripts mínimos da fase ficam em `scripts/`:

- `scripts/rag_status.py`
- `scripts/rag_ingest.py`
- `scripts/rag_reset.py`
- `scripts/rag_collections.py`

Exemplos:

```bash
.venv/bin/python scripts/rag_status.py --tenant-id prefeitura-demo
.venv/bin/python scripts/rag_ingest.py --tenant-id prefeitura-demo
.venv/bin/python scripts/rag_reset.py --tenant-id prefeitura-demo
.venv/bin/python scripts/rag_collections.py --contains prefeitura_demo
```

## 7. Limites atuais

Este contrato ainda não cobre:

- painel/admin completo servido pelo backend mínimo
- upload binário de arquivos
- chunking avançado
- embeddings externos
- avaliação formal de qualidade do RAG

## 8. Regra de evolução

Toda evolução futura deve preservar:

- ingest explícita por tenant
- reset explícito das collections
- falha controlada quando a base não estiver pronta
- separação entre documento fonte, collection vetorial e histórico de conversa
