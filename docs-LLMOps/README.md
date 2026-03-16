# Chat Pref — LLMOps, Avaliação e Governança

## Visão geral

Esta pasta concentra a documentação da nova etapa de evolução do Chat Pref: a fase de **LLMOps, avaliação formal, governança e observabilidade avançada**.

Após a consolidação da **Fundação Operacional** do projeto, o foco desta nova frente deixa de ser apenas a manutenção de uma aplicação funcional e passa a ser a construção de uma plataforma de IA com maior maturidade técnica, reprodutibilidade experimental e capacidade de demonstração sob critérios de engenharia.

O objetivo desta documentação é organizar, registrar e sustentar tecnicamente essa transição.

## Objetivo da fase

A nova fase do projeto tem como objetivo transformar o Chat Pref em uma solução capaz de sustentar, de forma explícita e auditável:

- rastreabilidade experimental por tenant;
- versionamento formal de prompts, policies e configuração de RAG;
- avaliação reproduzível da qualidade do pipeline;
- comparação entre estratégias de retrieval e provedores LLM;
- observabilidade de qualidade, latência e custo;
- detecção de degradação semântica da base vetorial;
- orquestração offline para ingestão, avaliação e reindexação;
- documentação técnica consistente para demonstração, defesa arquitetural e evolução controlada.

## Escopo documental

Esta pasta documenta o novo ciclo de desenvolvimento do projeto, com foco em:

- contexto e motivação da nova fase;
- arquitetura-alvo da camada de LLMOps;
- planejamento macro e execução por fases;
- decisões arquiteturais relevantes;
- runbooks operacionais;
- detalhamento de fases específicas, quando necessário.

A documentação anterior, relativa à fundação operacional do projeto, permanece preservada em sua pasta própria, como registro histórico do ciclo já consolidado.

## Estrutura da pasta

```text
docs-LLMOps/
├── README.md
├── CONTEXTO-LLMOps.md
├── ARQUITETURA-LLMOps.md
├── PLANEJAMENTO-LLMOps.md
├── fases/
├── adrs/
└── runbooks/
```

## Papel de cada documento

### `README.md`

Documento de entrada da pasta. Apresenta a finalidade da fase, o escopo documental e a navegação entre os arquivos.

### `CONTEXTO-LLMOps.md`

Formaliza a abertura da nova fase, explicando motivação, objetivos, limites, critérios de sucesso e relação com a etapa anterior.

### `ARQUITETURA-LLMOps.md`

Descreve a arquitetura-alvo da nova fase, deixando explícito o que já está validado, o que permanece como contrato ativo e o que será introduzido ao longo do novo ciclo.

### `PLANEJAMENTO-LLMOps.md`

Concentra o planejamento macro da fase, com frentes, critérios de aceite, tasks e ordem de execução.

### `adrs/`

Armazena os registros de decisões arquiteturais relevantes da nova fase.

### `runbooks/`

Armazena procedimentos operacionais, setup de ambiente, rotinas de avaliação e guias de execução técnica.

### `fases/`

Pode ser usado para detalhamento adicional de fases ou frentes específicas quando o nível de complexidade ultrapassar o escopo do planejamento macro.

Documentos de fase atualmente presentes nesta pasta:

- `fases/FASE1-LLMOPS.md`
- `fases/FASE2-LLMOPS.md`
- `fases/FASE3-DATASET-BENCHMARK.md`
- `fases/FASE4-AVALIACAO-FORMAL-RAG.md`
- `fases/FASE5-RETRIEVAL-HIBRIDO.md`

## Diretriz de manutenção

Esta documentação deve seguir as seguintes regras:

* não declarar como implementado o que ainda é apenas arquitetura-alvo;
* preservar separação clara entre estado atual e estado planejado;
* registrar decisões relevantes com justificativa técnica;
* manter rastreabilidade entre planejamento, arquitetura e execução;
* tratar segregação por tenant como requisito estrutural, não opcional.

## Relação com a documentação anterior

A pasta `docs-fundacao-operacional/` permanece como registro da fase já consolidada do projeto.

A pasta `docs-LLMOps/` passa a concentrar a documentação viva do novo ciclo, orientado à maturidade de IA, avaliação formal, governança e observabilidade.

## Próxima leitura recomendada

A sequência recomendada de leitura desta pasta é:

1. `CONTEXTO-LLMOps.md`
2. `ARQUITETURA-LLMOps.md`
3. `PLANEJAMENTO-LLMOps.md`
4. `fases/FASE1-LLMOPS.md`
5. `fases/FASE2-LLMOPS.md`
6. `fases/FASE3-DATASET-BENCHMARK.md`
7. `fases/FASE4-AVALIACAO-FORMAL-RAG.md`
8. `fases/FASE5-RETRIEVAL-HIBRIDO.md`

## Status

Fase 1 concluída com evidência local.
Fase 2 consolidada neste escopo na branch `feat/fase2-rag-prompts`.
Fase 3 consolidada neste escopo na branch `feat/dataset-avaliacao`, com baseline inicial de benchmark reproduzível para o tenant demonstrativo.
Fase 4 consolidada neste escopo na branch `feat/avaliacao-rag-metricas-de-qualidade`, com avaliação formal offline, artifacts comparativos e baseline inicial rastreável do RAG.
Na branch `feat/fase5-retrieval-query-reranking`, a Fase 5 foi aberta estruturalmente com `CPPX-F5-T1` documentado e um diff preparatório mínimo no contrato do retrieval atual, sem promover nova estratégia como default.
