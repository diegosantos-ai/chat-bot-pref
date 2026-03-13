# Fase 7 - Tenant Demonstrativo Ficticio

## Objetivo

Criar um tenant institucional ficticio, coerente e reutilizavel, para servir como base oficial de demonstracao da plataforma.

## Tenant definido

- `tenant_id`: `prefeitura-vila-serena`
- `client_name`: `Prefeitura Municipal de Vila Serena`
- `bot_name`: `Atende Vila Serena`
- natureza: prefeitura ficticia, sem uso de dados reais

## Artefatos criados

- bundle versionado em `tenants/prefeitura-vila-serena/`
- configuracao principal em `tenants/prefeitura-vila-serena/tenant.json`
- identidade e escopo documentados em `tenants/prefeitura-vila-serena/README.md`
- base documental inicial em `tenants/prefeitura-vila-serena/knowledge_base/`
- script de materializacao em `scripts/bootstrap_demo_tenant.py`

## Estrutura documental inicial

O bundle inclui tres documentos iniciais:

1. `tenant-identidade-institucional.json`
2. `tenant-escopo-assistente.json`
3. `tenant-limites-disclaimer.json`

Esses documentos formam a base minima para ingest do tenant demonstrativo sem depender de defaults globais.

## Coerencia arquitetural validada

- `tenant_id` explicito no bundle e repetido em todos os documentos
- paths do bundle sao relativos ao proprio tenant
- materializacao no runtime ocorre por acao explicita, sem fallback silencioso
- a base versionada fica fora de `data/knowledge_base/`, preservando a separacao entre fonte versionada e runtime materializado

## Criterios de aceite

- nome do tenant definido e padronizado: `prefeitura-vila-serena`
- identidade textual institucional criada: `README.md` e documento institucional inicial
- configuracao do tenant criada sem hardcodes de runtime: `tenant.json` com caminhos relativos
- escopo do assistente documentado: `scope` no manifest e documento dedicado
- estrutura inicial preparada para ingest: tres documentos versionados, bootstrap validado e ingest executavel

## Validacao executada

- `pytest` com teste dedicado do bundle e do bootstrap
- `python scripts/bootstrap_demo_tenant.py --manifest tenants/prefeitura-vila-serena/tenant.json --purge-documents --ingest`
- `python scripts/smoke_tests.py --env prod --tenant-id prefeitura-vila-serena --tenant-manifest tenants/prefeitura-vila-serena/tenant.json`
- `python scripts/smoke_tests.py --env dev --tenant-id prefeitura-vila-serena --tenant-manifest tenants/prefeitura-vila-serena/tenant.json`

## Evidencia operacional

O smoke test agora produz um `managerial_report` no JSON final, validando automaticamente os criterios de aceite desta fase e anexando evidencia objetiva por criterio.
