# Fase 9 - Operacionalizacao do Chat via Telegram

## Objetivo

Disponibilizar um canal demonstrativo do Telegram para o tenant `prefeitura-vila-serena`, reutilizando o mesmo fluxo do `POST /api/chat` e registrando auditoria correlacionada.

## O que foi entregue

- endpoint `POST /api/telegram/webhook`
- validacao opcional de secret via `X-Telegram-Bot-Api-Secret-Token`
- resolucao de tenant por `TELEGRAM_DEFAULT_TENANT_ID` ou `TELEGRAM_CHAT_TENANT_MAP`
- reutilizacao do `ChatService` com `channel="telegram"`
- cliente de entrega com modos `api`, `dry_run` e `disabled`
- auditoria correlacionada com `request_id`, `tenant_id`, `chat_id`, `message_id` e `update_id`
- utilitario `scripts/telegram_webhook.py` para `getMe`, `setWebhook`, `getWebhookInfo` e `deleteWebhook`
- smoke da fase validando o canal em `prod` e `dev`

## Critérios de aceite validados

- bot Telegram preparado para configuracao do tenant demonstrativo
- integracao backend ↔ Telegram implementada
- tenant demonstrativo acessivel no canal via `TELEGRAM_DEFAULT_TENANT_ID`
- mensagens simples respondidas corretamente no webhook
- logs e auditoria registrando as interacoes com correlacao minima

## Validacao executada

- `.venv/bin/python -m pytest tests -q`
- `.venv/bin/python scripts/smoke_tests.py --env prod --tenant-id prefeitura-vila-serena --tenant-manifest tenants/prefeitura-vila-serena/tenant.json --phase-report fase9 --json-out artifacts/fase9-smoke-prod.json`
- `.venv/bin/python scripts/smoke_tests.py --env dev --tenant-id prefeitura-vila-serena --tenant-manifest tenants/prefeitura-vila-serena/tenant.json --phase-report fase9 --json-out artifacts/fase9-smoke-dev.json`

## Artefatos

- `artifacts/fase9-smoke-prod.json`
- `artifacts/fase9-smoke-dev.json`

## Observacao operacional

No ambiente local validado, o Telegram opera em `dry_run` para permitir smoke reproduzivel sem token real.

Para entrega real em um bot configurado no BotFather, e necessario:

- definir `TELEGRAM_BOT_TOKEN`
- usar `TELEGRAM_DELIVERY_MODE=api`
- expor uma URL publica HTTPS para `POST /api/telegram/webhook`
- configurar o webhook com `scripts/telegram_webhook.py`
