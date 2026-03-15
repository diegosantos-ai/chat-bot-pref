# Fase 3 — Estrutura Inicial do Dataset de Benchmark

## Objetivo deste documento

Registrar o resultado do Bloco 1 da Fase 3, dedicado a criar a estrutura minima do dataset de benchmark reproduzivel do Chat Pref.

Este documento descreve apenas o que foi efetivamente implementado nesta etapa:

- estrutura local do dataset no repositorio;
- contrato minimo de casos de avaliacao;
- organizacao por tenant e por cenario;
- placeholders controlados para o tenant demonstrativo;
- validacoes locais simples da estrutura.

Ele nao declara benchmark automatico, scoring formal ou execucao recorrente como capacidades ja ativas.

## Enquadramento da fase

- ciclo: LLMOps, avaliacao e governanca
- fase ativa: Fase 3 — Dataset de Avaliacao e Benchmark Reproduzivel
- branch de execucao: `feat/dataset-avaliacao`
- task principal deste bloco: `CPPX-F3-T1`
- apoio parcial neste bloco: `CPPX-F3-T2` e `CPPX-F3-T6`

## Estrutura adotada

O dataset inicial foi separado do runtime transacional e do tracking experimental em uma pasta propria:

```text
benchmark_datasets/
├── README.md
└── tenants/
    └── prefeitura-vila-serena/
        └── benchmark_v1/
            ├── dataset_manifest.json
            └── scenarios/
                ├── atendimento_normal.jsonl
                ├── pergunta_ambigua.jsonl
                ├── fora_de_escopo.jsonl
                ├── baixa_confianca.jsonl
                └── risco_policy.jsonl
```

Regra estrutural desta etapa:

- `benchmark_datasets/` guarda apenas artefatos offline de benchmark;
- `tenant_id` aparece no caminho e no contrato de cada caso;
- `dataset_version` aparece no caminho do dataset e no manifest;
- cada arquivo JSONL agrupa apenas um tipo de cenario.

## Contrato minimo do manifest

Cada dataset local desta fase possui um `dataset_manifest.json` com os campos:

- `dataset_version`
- `tenant_id`
- `description`
- `scenario_files`
- `notes`

Cada item de `scenario_files` declara:

- `scenario_type`
- `relative_path`
- `cases_count`

Esse manifest permite que as proximas tasks da Fase 3 executem o benchmark de forma repetivel sem depender de banco ou servico externo.

## Contrato minimo de cada caso

Cada linha JSONL representa um caso de avaliacao com o seguinte contrato minimo:

- `case_id`
- `tenant_id`
- `scenario_type`
- `input_query`
- `expected_behavior`
- `expected_answer_reference`
- `expected_context_reference`
- `notes`

### Estrutura de `expected_answer_reference`

- `reference_type`
- `summary`
- `must_include`
- `must_not_include`

### Estrutura de `expected_context_reference`

- `reference_type`
- `document_hints`
- `required_terms`
- `notes`

## Cenarios cobertos neste bloco

O dataset inicial cobre um caso minimo para cada cenario exigido no planejamento:

- `atendimento_normal`
- `pergunta_ambigua`
- `fora_de_escopo`
- `baixa_confianca`
- `risco_policy`

Nesta etapa, a cobertura e propositalmente pequena. O objetivo foi estruturar o metodo, nao preencher o benchmark com volume artificial.

## Tenant demonstrativo usado

O primeiro dataset foi criado para:

- `tenant_id`: `prefeitura-vila-serena`

Justificativa:

- o tenant demonstrativo ja possui bundle institucional documentado;
- existem retrieval checks controladas no repositorio;
- o conjunto permite exemplos plausiveis sem usar dado sensivel ou caso real.

Mesmo assim, alguns casos desta etapa foram mantidos como placeholders honestos, especialmente em `baixa_confianca` e `pergunta_ambigua`, porque a intencao do bloco e validar a estrutura metodologica do benchmark, nao fingir cobertura que o tenant ainda nao tem.

## Relacao com o runtime e com o tracking

Esta entrega:

- nao altera comportamento funcional do chat;
- nao muda o runtime RAG transacional;
- nao mistura benchmark com auditoria operacional;
- nao executa avaliacao automatica sofisticada;
- nao integra ainda o dataset a um runner formal da Fase 3.

O contrato foi colocado em `app/llmops/benchmark_dataset.py` apenas para carga e validacao local do dataset offline.

## O que fica preparado para os proximos blocos

Com esta estrutura, os proximos blocos podem:

- ampliar casos por tenant e por cenario;
- refinar `expected_answer_reference` e `expected_context_reference`;
- conectar `dataset_version` ao tracking experimental local;
- criar o runner repetivel do benchmark;
- consolidar baseline inicial da Fase 3.

## O que ainda nao foi implementado

Neste bloco ainda nao existe:

- benchmark runner recorrente;
- scoring automatico de qualidade;
- comparacao formal entre runs de benchmark;
- integracao do dataset com MLflow;
- cobertura ampla de casos por tenant.

## Validacoes locais recomendadas

```bash
source .venv/bin/activate
pytest tests/test_phase3_benchmark_dataset.py -q
pytest tests -q
```

## Referencias internas

- `docs-LLMOps/PLANEJAMENTO-LLMOps.md`
- `docs-LLMOps/runbooks/avaliacao-rag.md`
- `docs-LLMOps/adrs/ADR-004-versionamento-de-prompts-policies-e-configuracoes.md`
- `docs-LLMOps/adrs/ADR-005-benchmark-por-tenant-como-contrato-de-avaliacao.md`
