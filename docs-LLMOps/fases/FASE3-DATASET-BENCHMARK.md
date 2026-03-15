# Fase 3 — Estrutura Inicial do Dataset de Benchmark

## Objetivo deste documento

Registrar o estado atual do dataset de benchmark da Fase 3 apos os Blocos 1 e 2.

Este documento descreve apenas o que foi efetivamente implementado ate aqui:

- estrutura local do dataset no repositorio;
- contrato minimo de casos de avaliacao;
- organizacao por tenant e por cenario;
- priorizacao metodologica inicial dos cenarios do tenant demonstrativo;
- diferenciacao entre cenario aderente ao tenant, cenario generico municipal e placeholder controlado;
- validacoes locais simples da estrutura.

Ele nao declara benchmark automatico, scoring formal ou execucao recorrente como capacidades ja ativas.

## Enquadramento da fase

- ciclo: LLMOps, avaliacao e governanca
- fase ativa: Fase 3 — Dataset de Avaliacao e Benchmark Reproduzivel
- branch de execucao: `feat/dataset-avaliacao`
- task principal desta entrega: `CPPX-F3-T2`
- tasks ja cobertas na base atual: `CPPX-F3-T1`
- apoio parcial nesta entrega: `CPPX-F3-T3`, `CPPX-F3-T4`, `CPPX-F3-T5` e `CPPX-F3-T6`

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
- `selection_hypotheses`
- `scenario_files`
- `notes`

Cada item de `scenario_files` declara:

- `scenario_type`
- `relative_path`
- `cases_count`
- `priority_tier`
- `coverage_type`
- `selection_rationale`

Esse manifest permite que as proximas tasks da Fase 3 executem o benchmark de forma repetivel sem depender de banco ou servico externo.

## Contrato minimo de cada caso

Cada linha JSONL representa um caso de avaliacao com o seguinte contrato minimo:

- `case_id`
- `tenant_id`
- `scenario_type`
- `priority_tier`
- `coverage_type`
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

## Priorizacao inicial adotada

Os cenarios foram priorizados com tres faixas simples:

- `p1`: cenarios centrais para o tenant demonstrativo, frequentes ou sensiveis a regressao funcional;
- `p2`: cenarios importantes para ambiguidade, limites de escopo ou comparacao complementar;
- `p3`: placeholders honestos para lacunas ainda nao cobertas pelo tenant demonstrativo.

Tambem foi adotada uma diferenciacao explicita de aderencia:

- `tenant_demonstrativo`: caso sustentado diretamente por bundle, retrieval checks ou limite institucional ja documentado do tenant demonstrativo;
- `generico_municipal`: caso plausivel no dominio municipal, util para benchmark, mas nao validado por um servico especifico do tenant;
- `placeholder`: caso mantido para explicitar lacuna real e guiar refinamento posterior.

### Matriz inicial de priorizacao

| Cenário | Prioridade | Aderência | Racional curto |
|---|---|---|---|
| `atendimento_normal` | `p1` | `tenant_demonstrativo` | cobre perguntas centrais e frequentes do bundle atual, sensiveis a regressao de retrieval |
| `risco_policy` | `p1` | `tenant_demonstrativo` | protege um comportamento critico de guardrail e privacidade |
| `pergunta_ambigua` | `p2` | `tenant_demonstrativo` | testa desambiguacao dentro do dominio ja coberto pelo tenant |
| `fora_de_escopo` | `p2` | `generico_municipal` | mede limite de escopo com exemplo plausivel no contexto municipal |
| `baixa_confianca` | `p3` | `placeholder` | explicita uma lacuna atual do tenant sem inventar cobertura documental |

### Casos P1 atualmente materializados

Os casos P1 escolhidos para o tenant demonstrativo foram:

- horario da Central de Atendimento;
- documentos basicos para protocolo geral presencial;
- segunda via do IPTU;
- solicitacao de alvara para comercio de baixo risco;
- horario da sala de vacinacao da UBS;
- solicitacao de coleta de entulho;
- bloqueio de pedido de CPF de servidor.

Eles foram priorizados porque combinam:

- alta aderencia ao escopo institucional conhecido do tenant;
- frequencia plausivel no atendimento municipal;
- dependencia clara de contexto recuperado ou de guardrail;
- utilidade alta para detectar regressao funcional.

### Cobertura atual de `atendimento_normal`

Depois desta ampliacao, `atendimento_normal` passou a cobrir, de forma mais representativa:

- informacao institucional de horario e canal principal;
- documentos necessarios para atendimento presencial;
- emissao ou segunda via de servico recorrente;
- etapa inicial de procedimento administrativo;
- horario e local de servico municipal especifico;
- solicitacao de servico com regra operacional objetiva.

Casos propositalmente evitados neste bloco:

- `Cadastro Unico`, `nota fiscal avulsa` e `iluminacao publica`, porque ampliariam o volume com padroes ja parcialmente cobertos por documentos, procedimento ou solicitacao de servico;
- variacoes muito proximas das perguntas ja escolhidas, para nao transformar diversidade aparente em redundancia de benchmark.

## Tenant demonstrativo usado

O primeiro dataset foi criado para:

- `tenant_id`: `prefeitura-vila-serena`

Justificativa:

- o tenant demonstrativo ja possui bundle institucional documentado;
- existem retrieval checks controladas no repositorio;
- o conjunto permite exemplos plausiveis sem usar dado sensivel ou caso real.

Mesmo assim, o dataset ainda preserva um caso explicitamente `placeholder` em `baixa_confianca` e um caso `generico_municipal` em `fora_de_escopo`, justamente para nao transformar suposicao em verdade institucional.

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
- substituir placeholders por casos aderentes ao tenant quando a base documental for aprofundada;
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

## Leitura metodologica do estado atual

No estado atual:

- `tenant_demonstrativo` significa aderencia suficiente ao bundle e aos retrieval checks ja versionados;
- `generico_municipal` significa utilidade metodologica sem declaracao de servico especifico do tenant;
- `placeholder` significa falta de cobertura assumida explicitamente, nao defeito escondido.

Isso permite usar o benchmark repetidamente desde agora, sem perder a distinção entre evidencia real do tenant e extrapolacao ainda nao consolidada.

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
