# Contrato Operacional de Tenant

## 1. Objetivo

Este documento registra como o `tenant_id` funciona na base mínima atual do Chat Pref.

Ele descreve apenas o que já está implementado.

## 2. Entrada HTTP

Endpoint atual:

- `POST /api/chat`

Regra:

- `tenant_id` é obrigatório no payload

Exemplo:

```json
{
  "tenant_id": "prefeitura-demo",
  "message": "Teste"
}
```

## 3. Normalização

No contrato atual:

- `tenant_id` é `strip()` antes do uso
- `tenant_id` vazio é tratado como ausente
- `message` é `strip()` antes do uso
- `message` vazia gera erro de validação

## 4. Propagação

O fluxo atual usa `contextvars` para tenant:

1. o endpoint recebe a requisição
2. injeta o `tenant_id` no `tenant_context`
3. chama o `ChatService`
4. limpa o contexto no `finally`

Regra operacional:

- o serviço não deve depender de tenant implícito fora do contexto

## 5. Persistência

### Histórico de conversa

Path:

```text
data/runtime/<tenant_id>/<session_id>.jsonl
```

Cada linha representa uma troca mínima de chat.

### Auditoria

Path:

```text
data/runtime/audit/<tenant_id>/<session_id>.jsonl
```

Cada request atual grava dois eventos:

- `chat_request_received`
- `chat_response_generated`

## 6. Falhas controladas

Comportamentos esperados hoje:

- sem `tenant_id`: `400 tenant_id obrigatório`
- sem `message`: erro de validação
- sem `tenant_id` no contexto interno: erro estrutural do serviço

## 7. Limites atuais

Este contrato ainda não cobre:

- resolução de tenant por webhook
- persistência relacional
- RAG por tenant
- auditoria em banco
- regras multi-canal

## 8. Intenção arquitetural

O objetivo deste contrato é impedir que a nova base volte a depender de tenant implícito.

Toda evolução futura deve manter estas propriedades:

- `tenant_id` explícito nos fluxos críticos
- erro controlado na ausência de tenant
- segregação de persistência por tenant
- rastreabilidade mínima associada ao tenant
