# avaliacao-rag

## Objetivo

Este runbook descreve como preparar, executar, registrar e revisar a avaliação formal do pipeline RAG na Fase 1 do Chat Pref.

Seu objetivo é padronizar a avaliação de qualidade do sistema, garantindo que mudanças em prompts, policies, retrieval, embeddings ou base vetorial sejam analisadas com benchmark reproduzível, métricas comparáveis e rastreabilidade por tenant.

## Escopo

Este runbook cobre:

- preparação do ambiente de avaliação;
- pré-condições para execução do benchmark;
- execução de avaliações formais do pipeline RAG;
- registro de métricas e artifacts;
- leitura inicial dos resultados;
- critérios mínimos de revisão técnica.

Este documento não substitui:
- a arquitetura da fase;
- o planejamento macro;
- a definição do dataset de benchmark;
- a documentação de tracking experimental.

## Pré-requisitos

Antes de executar qualquer avaliação formal, os seguintes itens devem estar disponíveis:

- ambiente base instalado;
- ambiente de desenvolvimento instalado;
- benchmark mínimo definido;
- convenção de versionamento de prompts, policies e retrieval definida;
- mecanismo de tracking experimental disponível;
- tenant de referência claramente identificado;
- configuração da base vetorial sob avaliação conhecida.

## Dependências

A execução da avaliação formal depende, no mínimo, de:

- `requirements.txt`
- `requirements-dev.txt`

A instalação dessas dependências deve ocorrer na **Fase 1**, conforme definido em `PLANEJAMENTO-LLMOps.md`.

Estado atual implementado no repositório:

- `Ragas` é a stack primária de métricas da Fase 4;
- `MLflow` é o tracking experimental da run;
- a execução atual ocorre em pipeline offline, sem acoplamento ao runtime transacional;
- o modo inicial do avaliador é `offline_heuristic_ragas`, com adapters locais para manter a execução reproduzível no ambiente dev.

## Objetos mínimos de avaliação

Toda avaliação formal deve buscar registrar, quando aplicável:

- `tenant_id`
- `dataset_version`
- `prompt_version`
- `policy_version`
- `retriever_version`
- `embedding_version`
- `vectorstore_version`
- `model_provider`
- `model_name`
- parâmetros relevantes de retrieval
- timestamp da execução
- identificador do experimento
- identificador do run

## Tipos de avaliação previstos

### 1. Avaliação de baseline
Usada para estabelecer a linha de referência inicial da qualidade do pipeline.

### 2. Avaliação comparativa
Usada para comparar duas ou mais variações de:
- prompt;
- retrieval;
- política;
- embeddings;
- base vetorial;
- modelo.

### 3. Avaliação de regressão
Usada para verificar se uma mudança degradou comportamento previamente aceito.

### 4. Avaliação por tenant
Usada para validar impacto local de mudança sobre um tenant específico.

## Fluxo recomendado de execução

### Etapa 1 — Confirmar contexto da avaliação
Antes da execução, registrar explicitamente:

- qual tenant será avaliado;
- qual versão de dataset será utilizada;
- qual hipótese está sendo testada;
- qual baseline será usada como referência;
- qual componente está sendo alterado.

### Etapa 2 — Validar o ambiente
Confirmar que:

- as dependências do ambiente dev estão instaladas;
- imports de tracking e avaliação funcionam;
- a base vetorial alvo está acessível;
- o benchmark está disponível;
- o contexto experimental está corretamente identificado.

### Etapa 3 — Executar a avaliação
Executar o benchmark no contexto planejado, preservando:

- isolamento por tenant;
- identificação da versão dos artefatos;
- registro das métricas;
- persistência dos resultados experimentais.

Comando mínimo atual:

```bash
./.venv/bin/python scripts/run_phase4_rag_evaluation.py \
  --manifest benchmark_datasets/tenants/prefeitura-vila-serena/benchmark_v1/dataset_manifest.json \
  --case-id vs-normal-001 \
  --case-id vs-risco-policy-001
```

Comando comparativo atual da Fase 5:

```bash
./.venv/bin/python scripts/run_phase5_strategy_comparison.py \
  --manifest benchmark_datasets/tenants/prefeitura-vila-serena/benchmark_v1/dataset_manifest.json
```

Saída esperada:

- resumo JSON curto no terminal;
- criação do backend local do `MLflow` em `artifacts/llmops/fase4_rag_evaluation/`;
- geração de artifacts por run em `artifacts/llmops/fase4_rag_evaluation/run_reports/`.
- quando a comparação da Fase 5 for usada, o sumário consolidado da matriz é escrito em `artifacts/llmops/fase5_retrieval_comparison/run_reports/phase5_strategy_comparison_summary.json`.

### Etapa 4 — Registrar métricas e artifacts
Persistir os resultados no sistema de tracking adotado, incluindo métricas e artifacts comparativos.

No estado atual da Fase 4, a run já registra no `MLflow`:

- `tenant_id`, `dataset_version`, `prompt_version`, `policy_version`, `retriever_version`, `embedding_version`;
- `prompt_version_id`, `policy_version_id`, `retriever_version_id`, `chunking_version`, `chunking_version_id`;
- `vectorstore_collection`, `vectorstore_fingerprint`, `evaluator_library`, `evaluator_library_version`, `evaluator_mode`;
- `faithfulness_mean`, `answer_relevance_mean`, `expected_context_coverage_mean`, `retrieval_empty_rate`;
- `cases_total`, `cases_evaluated`, `cases_partial`, `cases_skipped`, `cases_with_methodology_limitations`;
- contadores de skip por métrica e um relatório JSON consolidado da run.

Artifacts gerados neste estado:

- `*_rag_evaluation_run.json`
- `*_rag_evaluation_comparison.json`
- `*_rag_evaluation_comparison.csv`
- `*_rag_evaluation_case_ranking.json`
- `*_rag_evaluation_baseline_summary.json`

Uso esperado de cada artifact:

- `run.json`: leitura completa da run atual;
- `comparison.json`: comparação rastreável entre runs anteriores do mesmo experimento e tenant;
- `comparison.csv`: tabela plana para inspeção manual e comparação automatizável;
- `case_ranking.json`: lista de melhores, piores e não avaliados da run atual, sem análise causal automática.
- `baseline_summary.json`: resumo pequeno da baseline observada na run, com métricas oficiais, métricas bloqueadas e notas metodológicas.

### Etapa 5 — Revisar os resultados
Analisar:

- melhoria ou degradação da qualidade;
- impacto em latência;
- impacto em custo;
- aumento de fallback;
- aumento de retrieval vazio;
- comportamento inconsistente por cenário.

Leitura mínima para fechamento da Fase 4:

- usar `case_ranking.json` para localizar piores casos avaliados e casos apenas parciais;
- usar `baseline_summary.json` para registrar quais métricas entram oficialmente na baseline e quais continuam bloqueadas;
- manter a distinção entre problema observado, hipótese provável, evidência disponível e limitação da conclusão.

## Métricas mínimas esperadas

Conforme a maturidade da fase evoluir, a avaliação deve buscar registrar pelo menos:

- `faithfulness`
- `answer_relevance`
- métricas de contexto e recuperação
- latência
- custo estimado
- taxa de fallback
- taxa de retrieval vazio

Estado efetivamente registrado agora:

- `faithfulness_mean`
- `answer_relevance_mean`
- `expected_context_coverage_mean`
- `retrieval_empty_rate`
- contagens de casos avaliados, parciais e pulados

## Critérios mínimos de leitura

Nenhuma avaliação deve ser considerada suficiente apenas com nota agregada.

A leitura técnica deve considerar:

- comportamento médio;
- casos com pior desempenho;
- cenários sensíveis por tenant;
- impacto da mudança sobre respostas anteriormente estáveis;
- trade-off entre qualidade, latência e custo.

## Regras de execução

### 1. Sempre comparar com referência
Nenhuma mudança relevante deve ser avaliada sem baseline.

### 2. Sempre preservar o tenant
A avaliação deve manter recorte explícito por tenant.

### 3. Sempre versionar o contexto
Nenhum resultado deve ser aceito sem associação clara a versões de artefatos.

### 4. Sempre registrar hipótese
Toda avaliação relevante deve responder a uma hipótese concreta, ainda que simples.

### 5. Não promover por percepção
Mudanças não devem ser promovidas com base apenas em amostragem informal ou percepção subjetiva.

## Evidência mínima esperada

Cada avaliação relevante deve gerar evidência mínima, preferencialmente composta por:

- identificação do tenant;
- identificação do benchmark;
- versão dos artefatos avaliados;
- métricas principais;
- artifacts comparativos;
- comentário técnico de leitura inicial;
- decisão resultante: manter, revisar ou promover.

## Falhas comuns a evitar

- avaliar sem benchmark definido;
- comparar execuções com versionamento incompleto;
- misturar tenants em um mesmo resultado;
- usar métrica agregada como único critério;
- ignorar custo e latência ao melhorar qualidade;
- alterar múltiplas variáveis ao mesmo tempo sem controle.

Limitação metodológica relevante do estado atual:

- `context_precision` e `context_recall` continuam parciais porque o benchmark atual ainda não fornece `reference_answer` textual canônica para toda a baseline;
- o judge inicial da stack `Ragas` é offline e heurístico, então a leitura deve priorizar comparabilidade entre runs e inspeção dos piores casos, não interpretação absoluta da nota.
- o artifact comparativo atual explicita contexto e diferenças entre runs, mas ainda não interpreta automaticamente a causa dos piores casos.
- a baseline inicial da fase é válida para encerramento estrutural da avaliação offline, mas não deve ser apresentada como baseline semântica definitiva do produto.

## Saídas possíveis após avaliação

Ao final de uma avaliação, a decisão técnica deve cair em uma das seguintes categorias:

- **promover**  
  quando houver ganho ou trade-off aceitável sustentado por evidência;

- **manter em observação**  
  quando houver sinal promissor, mas com evidência ainda insuficiente;

- **revisar**  
  quando houver resultado inconclusivo ou degradado;

- **reverter**  
  quando a mudança piorar baseline validada.

## Relação com outros documentos

Este runbook deve ser lido em conjunto com:

- `README.md`
- `CONTEXTO-LLMOps.md`
- `ARQUITETURA-LLMOps.md`
- `PLANEJAMENTO-LLMOps.md`

## Status

Runbook atualizado com a execução offline mínima da Fase 4.

Próximo passo:
- ampliar a baseline executada;
- destravar `context_precision` e `context_recall` com `reference_answer`;
- evoluir da comparação estrutural para leitura técnica dos casos críticos.
