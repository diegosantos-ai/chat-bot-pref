# Fase 12 - Automacao de Qualidade com GitHub Actions

## Objetivo

Automatizar as validacoes essenciais do projeto para bloquear regressao relevante e tornar o case mais defensavel como engenharia de entrega.

## Entregas realizadas

- workflow de CI versionado em `.github/workflows/ci.yml`
- lint minimo do runtime em `scripts/lint_runtime.py`
- varredura anti-residuos historicos em `scripts/check_runtime_residues.py`
- regressao de `audit.v1`, `request_id`, `tenant_id` e `reason_codes` em `tests/test_phase12.py`
- validacao automatica de `docker compose config` e `docker build`
- smoke `prod` reduzido reaproveitando o runtime da Fase 11
- upload do artefato `fase11-smoke-prod.json` ao final do workflow

## Escopo do workflow

### Job `quality`

Executa:

- checkout
- setup do Python 3.11
- instalacao das dependencias
- lint minimo do runtime
- varredura anti-residuos historicos
- `compileall`
- `pytest`

### Job `docker-build-and-smoke`

Executa:

- validacao do `docker compose config`
- `docker build`
- subida do `chat-pref-api`
- espera por `healthy`
- smoke `prod` em `runtime-mode=reuse`
- upload do artefato JSON
- teardown do ambiente Docker

## Criterios de aceite cobertos

- workflow de CI criado e versionado
- lint, testes e validacoes minimas executados automaticamente
- build Docker validado no pipeline
- varredura anti-residuos historicos automatizada
- schema de auditoria e campos obrigatorios validados automaticamente
- regressao de comportamento e rastreabilidade bloqueando o pipeline
- matriz de cenarios criticos coberta por `pytest` e smoke reduzido

## Secrets e variaveis

### Nenhum secret novo obrigatorio para este corte

O workflow `.github/workflows/ci.yml` foi desenhado para rodar sem credenciais externas:

- `LLM_PROVIDER=mock` continua sendo o caminho reproduzivel padrao
- Telegram permanece fora da CI externa real
- o smoke de CI usa o proprio backend local do runner

### Secrets ja existentes, mas fora da CI da Fase 12

- `DEPLOY_WEBHOOK_URL`
- `DEPLOY_WEBHOOK_TOKEN`

Eles continuam restritos ao workflow manual de deploy.

### Secrets opcionais para evolucoes futuras

- `LLM_API_KEY`: apenas se a branch futura validar `LLM_PROVIDER=gemini` como parte do pipeline
- `TELEGRAM_BOT_TOKEN`: apenas para validacao externa real do canal Telegram

## Validacao local equivalente

```bash
.venv/bin/python scripts/lint_runtime.py
.venv/bin/python scripts/check_runtime_residues.py
.venv/bin/python -m compileall app scripts tests
.venv/bin/python -m pytest tests -q
docker compose -f docker-compose.yml config
docker compose -f docker-compose.yml -f docker-compose.local.yml config
docker build -t chat-pref-ci -f Dockerfile .
docker compose -f docker-compose.yml up -d --build
until [ "$(docker inspect -f '{{.State.Health.Status}}' chat-pref-api 2>/dev/null)" = "healthy" ]; do sleep 1; done
.venv/bin/python scripts/smoke_tests.py \
  --env prod \
  --runtime-mode reuse \
  --tenant-id prefeitura-vila-serena \
  --tenant-manifest tenants/prefeitura-vila-serena/tenant.json \
  --phase-report fase11 \
  --json-out artifacts/fase11-smoke-prod.json
docker compose -f docker-compose.yml down -v
```

## Evidencias validadas na branch

- `scripts/lint_runtime.py`: aprovado
- `scripts/check_runtime_residues.py`: aprovado
- `python -m pytest tests -q`: `32 passed`
- `docker compose -f docker-compose.yml config`: aprovado
- `docker compose -f docker-compose.yml -f docker-compose.local.yml config`: aprovado
- `docker build -t chat-pref-ci -f Dockerfile .`: aprovado
- smoke `prod` em `runtime-mode=reuse`: `15/15`

## Limites do corte atual

- a CI ainda nao valida um provedor LLM externo real
- a CI ainda nao conversa com Telegram externo real
- a execucao remota do workflow depende do push/PR no GitHub

Este recorte foi intencional para manter a pipeline simples, rapida e reproduzivel no estado atual do case.
