```skill
---
name: Templates
description: Coleção de templates de workflows n8n, separados por camadas, com explicações e checklist
---

# Templates

## Objetivo

Fornecer templates prontos e bem documentados para cenários comuns: conexões API, OAuth2, webhooks, Authy, integrações (Google/Slack/Stripe), e padrões em camadas (trigger, logic, persistence, observability).

## Estrutura por Camadas (recomendado)

1. Trigger: nó que inicia o fluxo (Webhook, Cron, Trigger específico).
2. Ingestão/Enrichment: nodes que validam e enriquecem dados (Set, HTTP Request, Function).
3. Business Logic: transformações e regras (Function, IF, Switch).
4. Persistence: gravação em DB / fila (HTTP Request / DB node).
5. Observability: logging, métricas, alertas (HTTP Request para monitoramento ou Slack node).

## Template A — Webhook → API → Persistência (ex.: criar recurso remoto e gravar local)

- Propósito: Receber evento, chamar API externa, armazenar resultado.
- Camadas: Trigger (Webhook) → Transform (Set) → HTTP Request (POST) → Parse → DB/Storage Node → Notificação (Slack/Email)
- Pré-requisitos: credencial API configurada, endpoint de persistência disponível.
- Checklist de produção: retries, idempotência, validação de payload, testes unitários.

## Template B — OAuth2 Flow (ex.: Google API)

- Propósito: Demonstrar configuração de OAuth2 em credenciais e uso em chamadas subsequentes.
- Camadas: Trigger (Webhook/Manual) → OAuth2 Credentials (n8n) → HTTP Request (com token) → Refresh handling
- Notas: documentar scopes, redirect URI e como trocar credenciais entre ambientes.

## Template C — Authy OTP Verification

- Propósito: Envio e verificação de OTP usando Authy.
- Camadas: Trigger (Webhook ou Form) → HTTP Request (Authy send) → Wait/Retry → HTTP Request (Authy verify) → Branch (success/fail) → Persist/Notify

## Template D — Stripe Webhook Handler (segurança)

- Verificar assinatura (`Stripe-Signature`) no header antes de processar.
- Validar idempotência usando `event.id`.

## Documentação de cada template

Para cada template entregue, incluir sempre:
- Propósito e resumo do fluxo
- Diagrama simples (lista de nodes)
- Variáveis/credenciais necessárias
- Passo a passo de deploy (staging → produção)
- Checklist de segurança e observability

``` 
