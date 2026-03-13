```skill
---
name: Connectors
description: Habilidade focada em criação e padronização de conectores n8n (REST, GraphQL, HTTP)
---

# Connectors

## Objetivo

Padronizar a criação, configuração e validação de conectores (HTTP Request, REST, GraphQL, APIs proprietárias) no n8n, promovendo segurança, reuso e separação em camadas.

## Princípios Centrais

- Preferir credenciais gerenciadas (`Credentials`) do n8n e variáveis de ambiente em vez de tokens inline.
- Projetar conectores idempotentes quando aplicável (ex.: usar request-id, deduplicação).
- Tratar limites de taxa (rate limits) e respostas paginadas com estratégias configuráveis.

## Padrão de Conector (Checklist)

1. Nome claro: `service.resource.action` (ex.: `github.issues.create`).
2. Documentar: propósito, entradas esperadas, saída esperada, erros comuns.
3. Credenciais: usar `n8n Credentials` com escopo mínimo.
4. Timeouts: configurar timeout e retry com backoff exponencial.
5. Logging: incluir campos para `request_id`, `status_code` e `latency`.

## Exemplo rápido (HTTP Request Node - REST)

- Trigger: Webhook (recebe payload) -> Transform (Set/Function) -> HTTP Request (GET/POST) -> Parse/Store

HTTP Request config (exemplo):
- URL: parametrizada via expression (ex.: `{{$json["apiUrl"]}}`).
- Auth: Use Credentials (API Key / OAuth2).
- Retry: 3 tentativas com backoff exponencial; registrar falhas.

## Paginação (estratégia comum)

- Cursor-based: iterar até `next_cursor == null`.
- Offset-based: paginar enquanto `length == page_size`.

## Tratamento de erros e limites de taxa

- Se receber `429` -> aplicar retry com backoff e usar cabeçalho `Retry-After` quando disponível.
- Para 5xx: aplicar retry limitado e escalonar se persistir.
- Registrar o erro com contexto e enviar alerta (Slack/Email) quando configurado.

## Boas práticas de implementação

- Centralize transformações (use nodes `Set`/`Function` apenas quando necessário).
- Separe credenciais por ambiente (dev/staging/prod) e documente como trocar no n8n.
- Versione conectores (ex.: `v1`, `v2`) se a API upstream muda.

## Anti-patterns

- Não hardcodear endpoints ou chaves em workflows.
- Não usar um único workflow para múltiplos propósitos sem camadas claras (trigger, enrich, persist).

``` 
