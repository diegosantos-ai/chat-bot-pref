# Contrato Operacional de Tenant

## 1. Objetivo

Este documento registra como o `tenant_id` funciona na base mínima atual do Chat Pref.

Ele descreve apenas o que já está implementado.

## 2. Entrada HTTP

Endpoints atuais:

- `POST /api/chat`
- `POST /api/webhook`

Regra:

- no chat direto, `tenant_id` é obrigatório no payload
- no webhook, o tenant pode chegar explicitamente ou ser resolvido por `page_id`

Exemplo de chat direto:

```json
{
  "tenant_id": "prefeitura-demo",
  "message": "Teste"
}
```

Exemplo de webhook com resolução por `page_id`:

```json
{
  "page_id": "page-prefeitura-demo",
  "message": "Teste"
}
```

## 3. Normalização

No contrato atual:

- `tenant_id` é `strip()` antes do uso
- `page_id` é `strip()` antes da resolução no webhook
- `tenant_id` vazio é tratado como ausente
- `message` é `strip()` antes do uso
- `message` vazia gera erro de validação

## 4. Resolução e propagação

O fluxo atual usa `contextvars` para tenant:

1. o endpoint recebe a requisição
2. o chat direto usa o `tenant_id` recebido no payload
3. o webhook resolve o tenant por `tenant_id` explícito ou `page_id -> tenant_id`
4. injeta o tenant no `tenant_context`
5. chama o `ChatService`
6. limpa o contexto no `finally`

Regras operacionais:

- o serviço não deve depender de tenant implícito fora do contexto
- o `ChatService` confirma o tenant após uma fronteira assíncrona antes de processar o request
- o webhook não usa tenant default silencioso

## 5. Persistência

### Histórico de conversa

Path:

```text
data/runtime/<tenant_id>/<session_id>.jsonl
```

Cada linha representa uma troca mínima de chat.

### Retrieval por tenant no Chroma

Path base:

```text
data/chroma/
```

Regras:

- cada tenant usa uma collection própria no Chroma
- o nome da collection deriva do `tenant_id`
- o fluxo consulta primeiro a collection do tenant ativo
- o fluxo grava a mensagem atual na collection do mesmo tenant após responder

### Auditoria

Path:

```text
data/runtime/audit/<tenant_id>/<session_id>.jsonl
```

Cada request atual grava três eventos:

- `chat_request_received`
- `chat_retrieval_completed`
- `chat_response_generated`

## 6. Falhas controladas

Comportamentos esperados hoje:

- sem `tenant_id` no chat direto: `400 tenant_id obrigatório`
- sem `message`: erro de validação
- webhook sem `tenant_id` e sem `page_id`: `400 tenant_id obrigatório ou page_id configurado no webhook`
- webhook com `page_id` sem mapeamento: `400 tenant_id não resolvido para page_id informado`
- webhook com `tenant_id` divergente do `page_id` mapeado: `400 tenant_id divergente do page_id informado`
- sem `tenant_id` no contexto interno: erro estrutural do serviço

## 7. Limites atuais

Este contrato ainda não cobre:

- persistência relacional
- webhook Meta específico
- RAG completo com base documental externa
- auditoria em banco
- regras multi-canal avançadas

## 8. Intenção arquitetural

O objetivo deste contrato é impedir que a nova base volte a depender de tenant implícito.

Toda evolução futura deve manter estas propriedades:

- `tenant_id` explícito nos fluxos críticos
- erro controlado na ausência de tenant
- segregação de persistência por tenant
- segregação de retrieval por tenant
- rastreabilidade mínima associada ao tenant
