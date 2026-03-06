```skill
---
name: Debugging
description: Procedimentos e checklists para depurar workflows n8n, autenticação, nodes e integrações
---

# Debugging

## Objetivo

Fornecer um processo sistemático para diagnosticar e resolver problemas em workflows n8n (execuções falhas, erros de auth, rate-limit, nodes com comportamento inesperado).

## Processo de Debug (passos)

1. Reproduzir localmente: usar `Execute Node` e `Execute Workflow` no editor do n8n.
2. Coletar logs: em self-hosted, habilitar loglevel `debug` temporariamente; em n8n Cloud, coletar Execution data e node errors.
3. Isolar componente: testar apenas o node que falha com inputs controlados.
4. Verificar credenciais: testar credenciais via `Test` em `Credentials` e validar escopos.
5. Validar rede: checar conectividade, DNS e firewall entre n8n e endpoints externos.

## Debugging por cenário comum

- Erro 401/403: revisar token, scopes, relógio do servidor (clock skew) e renovar credenciais.
- Erro 429: identificar cabeçalhos de rate-limit, aplicar retry/backoff e reduzir paralelismo.
- Erro 5xx: inspecionar payload, reduzir tamanho de lote e reintentar com backoff.
- Webhooks não acionando: verificar URL pública (ngrok/test), CORS e configuração do provider.

## Ferramentas e técnicas

- Use `Execute Node` com payloads mínimos para reproduzir.
- Adicione nodes `Set` para inserir `debug_id` e rastrear execução.
- Use storage temporário (ex.: Google Sheets, DB de staging) para comparar inputs/outputs.

## Checklist rápido para problemas com Authy

1. Confirmar `API Key` em `Credentials` do n8n.
2. Reproduzir chamada manualmente com `curl` ou Postman para validar resposta da API Authy.
3. Conferir códigos de erro e cabeçalhos (ex.: `X-RateLimit-Remaining`).
4. Se OTP falha: validar formato do número, país code e se o usuário está registrado.

## Documentar solução

- Para cada incidente, registre: steps para reproduzir, apontamento do root cause, correção aplicada e recomendações preventivas.

``` 
