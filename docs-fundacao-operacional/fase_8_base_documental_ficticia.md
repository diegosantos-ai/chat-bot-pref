# Fase 8 - Base Documental Ficticia e Ingest Limpa

## Objetivo

Criar uma base documental ficticia, pequena e bem estruturada, e executar a ingest limpa para o tenant demonstrativo `prefeitura-vila-serena`.

## Estrutura criada

A base documental versionada do tenant agora possui 14 documentos organizados em quatro grupos:

- institucional
- atendimento
- servicos
- faq

Documentos adicionados nesta fase:

- `atendimento-canais-oficiais.json`
- `protocolo-geral-documentos-basicos.json`
- `servico-alvara-funcionamento.json`
- `servico-iptu-certidoes.json`
- `servico-ubs-vacinacao.json`
- `servico-matricula-escolar.json`
- `servico-coleta-entulho.json`
- `servico-cadunico-cras.json`
- `faq-servicos-digitais.json`
- `servico-iluminacao-publica.json`
- `servico-nota-fiscal-avulsa.json`

O manifesto da base fica em `tenants/prefeitura-vila-serena/knowledge_base/manifest.json` e as perguntas controladas de retrieval ficam em `tenants/prefeitura-vila-serena/knowledge_base/retrieval_checks.json`.

## Cobertura tematica

A base cobre os principais temas definidos para a prefeitura ficticia:

- atendimento presencial e canais oficiais
- protocolo geral e documentos basicos
- alvara de funcionamento
- IPTU e certidoes imobiliarias
- UBS e vacinacao
- matricula e transferencia escolar
- coleta seletiva e entulho
- FAQ de servicos digitais
- identidade, escopo e limites do assistente

## Criterios de aceite

- documentos ficticios criados e organizados: 14 documentos versionados e listados no manifesto
- base cobre os principais temas da prefeitura ficticia: 4 grupos documentais e 11 perguntas controladas
- ingest executada sem acoplamento legado: bundle materializado por script explicito e ingest executada no tenant correto
- retrieval retorna contexto util para perguntas controladas: 11/11 checks aprovados no smoke e nos testes
- ausencia de base e tratada de forma controlada antes da ingest: `RAG vazio` validado no inicio do smoke

## Validacao executada

- `python -m pytest tests -q`
- `python scripts/bootstrap_demo_tenant.py --manifest tenants/prefeitura-vila-serena/tenant.json --purge-documents --ingest --phase-report fase8`
- `python scripts/smoke_tests.py --env prod --tenant-id prefeitura-vila-serena --tenant-manifest tenants/prefeitura-vila-serena/tenant.json --phase-report fase8 --json-out artifacts/fase8-smoke-prod.json`
- `python scripts/smoke_tests.py --env dev --tenant-id prefeitura-vila-serena --tenant-manifest tenants/prefeitura-vila-serena/tenant.json --phase-report fase8 --json-out artifacts/fase8-smoke-dev.json`

## Evidencia operacional

Os artefatos `artifacts/fase8-smoke-prod.json` e `artifacts/fase8-smoke-dev.json` incluem `managerial_report` com validacao objetiva dos criterios de aceite da fase, usando a combinacao de:

- validacao estrutural do bundle
- validacao de base vazia antes da ingest
- ingest limpa por tenant
- retrieval controlado com perguntas predefinidas
