# Contrato Operacional de Tenant

## 1. Objetivo

Este documento registra como o `tenant_id` funciona na base mínima atual do Chat Pref.

Ele descreve apenas o que já está implementado.

## 2. Entrada HTTP

Endpoints atuais:

- `POST /api/chat`
- `POST /api/webhook`
- `POST /api/telegram/webhook`

Regra:

- no chat direto, `tenant_id` é obrigatório no payload
- no webhook, o tenant pode chegar explicitamente ou ser resolvido por `page_id`
- no Telegram, o tenant é resolvido por `TELEGRAM_DEFAULT_TENANT_ID` ou `TELEGRAM_CHAT_TENANT_MAP`

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

Exemplo de update Telegram:

```json
{
  "update_id": "900001",
  "message": {
    "message_id": "700001",
    "chat": {
      "id": "55119990001",
      "type": "private"
    },
    "text": "Qual o horario do alvara?"
  }
}
```

## 3. Normalização

No contrato atual:

- `tenant_id` é `strip()` antes do uso
- `page_id` é `strip()` antes da resolução no webhook
- `chat_id`, `message_id` e `update_id` do Telegram são normalizados como string
- `tenant_id` vazio é tratado como ausente
- `message` é `strip()` antes do uso
- `message` vazia gera erro de validação

## 4. Resolução e propagação

O fluxo atual usa `contextvars` para tenant:

1. o endpoint recebe a requisição
2. o chat direto usa o `tenant_id` recebido no payload
3. o webhook resolve o tenant por `tenant_id` explícito ou `page_id -> tenant_id`
4. o Telegram resolve o tenant por `TELEGRAM_DEFAULT_TENANT_ID` ou `TELEGRAM_CHAT_TENANT_MAP`
5. injeta o tenant no `tenant_context`
6. chama o `ChatService`
7. limpa o contexto no `finally`

Regras operacionais:

- o serviço não deve depender de tenant implícito fora do contexto
- o `ChatService` confirma o tenant após uma fronteira assíncrona antes de processar o request
- o webhook não usa tenant default silencioso
- o Telegram só usa tenant default quando ele estiver explicitamente configurado em settings

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
- a collection de base documental é separada do histórico de conversa
- o fluxo consulta primeiro a collection do tenant ativo
- o chat não grava automaticamente a conversa como base RAG

### Auditoria

Path:

```text
data/runtime/audit/<tenant_id>/<session_id>.jsonl
```

Cada request atual grava três eventos:

- `chat_request_received`
- `chat_retrieval_completed` ou `chat_retrieval_unavailable`
- `chat_response_generated`

No canal Telegram, o mesmo request ainda registra:

- `telegram_update_received`
- `telegram_message_delivery` ou `telegram_message_delivery_failed`

Payloads do Telegram devem carregar, no minimo:

- `telegram_chat_id`
- `telegram_message_id`
- `telegram_update_id`
- `channel=telegram`

## 6. Falhas controladas

Comportamentos esperados hoje:

- sem `tenant_id` no chat direto: `400 tenant_id obrigatório`
- sem `message`: erro de validação
- webhook sem `tenant_id` e sem `page_id`: `400 tenant_id obrigatório ou page_id configurado no webhook`
- webhook com `page_id` sem mapeamento: `400 tenant_id não resolvido para page_id informado`
- webhook com `tenant_id` divergente do `page_id` mapeado: `400 tenant_id divergente do page_id informado`
- Telegram sem tenant resolvido por settings: `400 tenant_id nao resolvido para o chat do Telegram`
- Telegram com secret inválido: `403 Invalid telegram secret`
- chat sem base documental ingerida: resposta controlada com mensagem explícita do estado da base
- sem `tenant_id` no contexto interno: erro estrutural do serviço

## 7. Limites atuais

Este contrato ainda não cobre:

- persistência relacional
- webhook Meta específico
- bot Telegram com token real e webhook público
- upload binário de documentos
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
- correlação mínima por `request_id`, `tenant_id`, `channel` e identificadores do Telegram quando o canal estiver em uso
