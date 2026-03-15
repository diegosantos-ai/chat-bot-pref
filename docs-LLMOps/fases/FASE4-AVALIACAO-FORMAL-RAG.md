# Fase 4 — Avaliacao Formal de RAG com Metricas de Qualidade

## Objetivo deste documento

Registrar o fechamento do bloco atual da Fase 4 no escopo de:

- `CPPX-F4-T1 — Definir stack de avaliacao formal do RAG`
- `CPPX-F4-T2 — Conectar benchmark ao contrato de avaliacao formal`
- `CPPX-F4-T3 — Executar avaliacao formal offline com tracking experimental`
- parte operacional do `CPPX-F4-T4 — Registrar metricas complementares viaveis`
- `CPPX-F4-T5 — Gerar artifacts comparativos por experimento`

Este documento descreve apenas o que foi efetivamente implementado ou fechado neste bloco:

- stack de avaliacao formal disponivel no ambiente dev;
- contrato tecnico minimo da avaliacao offline por caso e por run;
- executor offline que conecta benchmark, retrieval, composicao, policy e avaliacao;
- registro minimo da run no `MLflow` local;
- artifacts comparativos por run e experimento;
- metricas obrigatorias da fase;
- metricas complementares iniciais ja enquadradas no contrato e registradas quando viaveis;
- limites metodologicos do benchmark atual da Fase 3.

Ele nao declara:

- baseline comparativa entre multiplas variacoes ja consolidada;
- artifacts comparativos avancados ja persistidos;
- uso da avaliacao formal no runtime transacional.

## Enquadramento do bloco

- ciclo: Fase 1 — LLMOps, avaliacao e governanca
- fase ativa: Fase 4 — Avaliacao Formal de RAG com Metricas de Qualidade
- branch de execucao: `feat/avaliacao-rag-metricas-de-qualidade`
- tasks cobertas agora:
  - `CPPX-F4-T1`
  - `CPPX-F4-T2`
  - `CPPX-F4-T3`
  - `CPPX-F4-T5`
- task preparada parcialmente agora: `CPPX-F4-T4`
- base reutilizada:
  - benchmark versionado da Fase 3 em `benchmark_datasets/`
  - contrato local do dataset em `app/llmops/benchmark_dataset.py`
  - contrato de tracking experimental em `app/audit/contracts.py`
  - integracao de versoes da Fase 2 em `app/llmops/tracking_integration.py`

## Estado encontrado no repositorio

Antes desta entrega, o repositorio ja possuia:

- `requirements-dev.txt` com `mlflow`, `ragas` e `deepeval`;
- smoke da Fase 1 exigindo import de `ragas`;
- benchmark tenant-aware e versionado da Fase 3;
- contrato minimo de runs experimentais separado da auditoria operacional.

Validacao local deste bloco na `.venv` do repositorio:

- `mlflow 3.10.1`
- `ragas 0.2.15`
- `deepeval 3.8.9`

Conclusao estrutural:

- `MLflow` continua sendo a camada de tracking experimental;
- `Ragas` passa a ser a biblioteca primaria de metricas da avaliacao formal do RAG nesta fase;
- `DeepEval` permanece apenas como biblioteca alternativa disponivel no ambiente, sem virar stack ativa deste bloco.

## Stack escolhida

### Biblioteca primaria de metricas

- `Ragas 0.2.15`

Motivos da escolha:

- ja esta versionada em `requirements-dev.txt`;
- ja esta disponivel na `.venv` ativa do projeto;
- atende diretamente as metricas obrigatorias da fase:
  - `faithfulness`
  - `answer_relevancy` na API da biblioteca, normalizada neste projeto como `answer_relevance`
- expoe tambem metricas complementares de contexto:
  - `context_precision`
  - `context_recall`

Implementacao efetiva neste bloco:

- o executor offline usa `Ragas` como biblioteca primaria;
- o modo atual do avaliador e `offline_heuristic_ragas`;
- esse modo injeta adapters locais deterministas de `LLM` e embeddings para permitir execucao offline sem chave externa nem dependencia nova.

Leitura correta:

- a stack continua sendo `Ragas`;
- o judge semantico atual e controlado localmente para manter reprodutibilidade no ambiente dev;
- os scores desta etapa servem para comparacao tecnica entre runs offline do projeto, nao como substituto de uma baseline futura com juiz semantico externo.

### Camada de tracking

- `MLflow 3.10.1`

Papel:

- registrar metricas agregadas por run;
- manter segregacao experimental por `tenant_id`;
- permanecer separado da auditoria operacional.

### Biblioteca nao ativada neste bloco

- `DeepEval 3.8.9`

Status:

- disponivel no ambiente;
- nao selecionada como stack principal deste bloco;
- pode ser reconsiderada apenas se houver restricao concreta para uso do `Ragas` em bloco futuro.

## Contrato tecnico da avaliacao

O contrato Python minimo deste bloco foi formalizado em:

- `app/llmops/rag_evaluation.py`
- `app/llmops/rag_evaluation_runner.py`

### Entrada minima por caso

Cada caso avaliado passa a reutilizar o `BenchmarkCase` da Fase 3 e acrescentar apenas a saida do pipeline sob teste:

- `benchmark_case`
- `response`
- `retrieved_contexts`
- `reference_answer` opcional

Interpretacao:

- `benchmark_case` preserva `case_id`, `tenant_id`, pergunta, comportamento esperado e termos de grounding;
- `response` e a resposta gerada pela variacao do pipeline avaliada;
- `retrieved_contexts` e o conjunto efetivamente recuperado para o caso;
- `reference_answer` so entra quando houver referencia textual suficiente para metricas de contexto do `Ragas`.

### Saida minima por caso

Cada caso avaliado pode registrar:

- `faithfulness`
- `answer_relevance`
- `context_precision`
- `context_recall`
- `expected_context_coverage`
- `retrieval_empty`

Regras importantes:

- `retrieval_empty` e flag booleana por caso;
- `context_precision` e `context_recall` so devem existir quando houver `reference_answer`;
- `expected_context_coverage` e derivada localmente do benchmark atual, sem depender do `Ragas`;
- `faithfulness` nao deve ser computada quando o retrieval vier vazio.

### Saida minima agregada por run

Cada run offline da avaliacao formal pode consolidar:

- `tenant_id`
- `dataset_version`
- `metric_library`
- `metric_library_version`
- `tracking_target`
- `total_cases`
- `metric_case_counts`
- `faithfulness_mean`
- `answer_relevance_mean`
- `context_precision_mean`
- `context_recall_mean`
- `expected_context_coverage_mean`
- `retrieval_empty_rate`

Leitura arquitetural:

- o contrato agregado continua offline e experimental;
- o tracking da run deve ser isolavel por `tenant_id`;
- a agregacao nao substitui leitura por caso.

## Como a run experimental funciona agora

O executor offline atual:

1. carrega o manifest do benchmark da Fase 3;
2. seleciona um recorte estavel de `case_id`, quando informado;
3. executa `policy_pre`;
4. executa retrieval offline tenant-aware sem tocar auditoria operacional;
5. compoe resposta ou fallback com o mesmo conjunto de servicos do pipeline;
6. executa `policy_post`;
7. monta `RagEvaluationCaseInput` com resposta final e contexto recuperado;
8. calcula metricas por caso com a stack formal resolvida;
9. agrega resultados por run;
10. registra tags, parametros, metricas e um relatorio JSON no `MLflow`.

Arquivos principais deste fluxo:

- `app/llmops/rag_evaluation_runner.py`
- `scripts/run_phase4_rag_evaluation.py`

## O que a run registra de fato no MLflow

Parametros e metadados minimos registrados:

- `tenant_id`
- `dataset_version`
- `prompt_version`
- `policy_version`
- `retriever_version`
- `embedding_version`
- `prompt_version_id`
- `policy_version_id`
- `retriever_version_id`
- `chunking_version`
- `chunking_version_id`
- `vectorstore_collection`
- `vectorstore_fingerprint`
- `evaluator_library`
- `evaluator_library_version`
- `evaluator_mode`
- `selected_case_ids`

Metricas agregadas minimas registradas:

- `faithfulness_mean`
- `answer_relevance_mean`
- `expected_context_coverage_mean`
- `retrieval_empty_rate`
- `cases_total`
- `cases_evaluated`
- `cases_partial`
- `cases_skipped`
- `cases_with_methodology_limitations`
- contadores de skip por metrica, quando ocorrerem

Artifacts comparativos persistidos agora:

- `*_rag_evaluation_run.json`
- `*_rag_evaluation_comparison.json`
- `*_rag_evaluation_comparison.csv`
- `*_rag_evaluation_case_ranking.json`

Finalidade de cada artifact:

- `run.json`: relatorio completo da run atual com resumo e casos executados;
- `comparison.json`: snapshot comparativo das runs anteriores do mesmo experimento e tenant mais a run atual;
- `comparison.csv`: versao tabular do snapshot comparativo para leitura manual e automacao posterior;
- `case_ranking.json`: melhores casos avaliados, piores casos avaliados e casos nao avaliados da run atual, sem inferencia interpretativa adicional.

## Metricas obrigatorias desta fase

As metricas obrigatorias definidas neste bloco sao:

- `faithfulness`
- `answer_relevance`

Mapeamento para a biblioteca escolhida:

- `faithfulness` -> `ragas.metrics.faithfulness`
- `answer_relevance` -> `ragas.metrics.answer_relevancy`

Padrao adotado no projeto:

- o nome interno do contrato permanece `answer_relevance`;
- o nome nativo da biblioteca fica registrado apenas como detalhe de implementacao.

## Metricas complementares iniciais

As metricas complementares iniciais enquadradas neste bloco sao:

- `context_precision`
- `context_recall`
- `retrieval_empty_rate`
- `expected_context_coverage`

### `context_precision`

Uso previsto:

- medir ruido do contexto recuperado frente a uma referencia explicita.

Condicao minima:

- exige `reference_answer`.

### `context_recall`

Uso previsto:

- medir se o retrieval cobriu o necessario para sustentar a resposta esperada.

Condicao minima:

- exige `reference_answer`.

### `retrieval_empty_rate`

Uso previsto:

- medir a proporcao de casos da run que terminaram sem contexto recuperado.

Fonte:

- agregacao da flag `retrieval_empty` por caso.

### `expected_context_coverage`

Uso previsto:

- medir a cobertura inicial dos `required_terms` do benchmark da Fase 3 no contexto realmente recuperado.

Fonte:

- calculo lexical simples sobre `expected_context_reference.required_terms`.

## O que passa a ser medido agora

Neste bloco, fica explicitamente medido ou preparavel:

- disponibilidade local da stack de avaliacao;
- `faithfulness` agregado por run;
- `answer_relevance` agregado por run;
- `retrieval_empty_rate` agregado por run;
- `expected_context_coverage_mean` agregado por run;
- total de casos, casos avaliados, casos parciais e casos pulados;
- suporte contratual a `context_precision` e `context_recall` quando houver `reference_answer`.

## O que ainda nao sera medido neste bloco

Este bloco ainda nao entrega:

- baseline comparativa entre variacoes de prompt, retrieval e base vetorial;
- correlacao automatica com custo, latencia, fallback e bloqueio;
- julgamento semantico forte de contexto quando o dataset nao tiver `reference_answer` textual.

## Limites metodologicos

### 1. O benchmark atual nao traz gabarito textual pleno

O dataset da Fase 3 foi desenhado com:

- `expected_answer_reference.summary`
- `must_include`
- `must_not_include`
- `expected_context_reference.required_terms`

Isso e suficiente para benchmark controlado e comparacao estrutural, mas ainda nao equivale automaticamente a uma `reference_answer` textual canonica para todas as metricas de contexto do `Ragas`.

Consequencia:

- `context_precision` e `context_recall` ficam formalmente definidas agora, mas dependem de curadoria adicional por caso para uso sem ambiguidade.

### 2. `expected_context_coverage` e um sinal diagnostico, nao um gold score

O calculo atual usa matching lexical simples em cima de `required_terms`.

Consequencia:

- a metrica ajuda a detectar ausencia evidente de grounding;
- ela nao substitui avaliacao semantica mais forte;
- termos sinonimos ou parafrases podem reduzir a nota sem representar regressao real.

### 3. `retrieval_empty_rate` nao explica a causa do vazio sozinha

A taxa de retrieval vazio pode refletir:

- base ausente;
- score minimo alto demais;
- pergunta mal ancorada ao tenant;
- regressao real do retrieval.

Consequencia:

- a taxa deve ser lida junto do contexto operacional do experimento, nao isoladamente.

### 4. Nota agregada nao substitui leitura dos piores casos

Mesmo com metricas formais:

- medias podem esconder regressao local;
- um tenant multi-servico continua exigindo leitura de cenarios criticos;
- casos `risco_policy`, `fora_de_escopo` e `baixa_confianca` merecem leitura qualitativa adicional.

### 5. O judge atual e offline e heuristico

Para manter este bloco executavel sem dependencia nova nem chave externa, o executor usa `Ragas` com adapters locais deterministas.

Consequencia:

- a run permanece reproduzivel no ambiente dev;
- os scores ficam comparaveis entre runs do mesmo repositorio e stack;
- os resultados ainda nao equivalem a uma avaliacao semantica forte com juiz externo dedicado.

### 6. O comparativo atual nao substitui leitura interpretativa dos casos

Os artifacts comparativos deste bloco deixam o contexto da run explicito, mas ainda nao executam interpretacao tecnica automatica dos piores casos.

Consequencia:

- o `comparison.json` mostra diferencas e contexto entre runs;
- o `case_ranking.json` lista casos fortes, fracos e nao avaliados;
- a analise causal detalhada dos casos criticos continua reservada ao bloco seguinte da fase.

## Relacao com a Fase 3

Esta entrega depende diretamente da qualidade metodologica do benchmark consolidado na Fase 3.

Na pratica:

- sem `BenchmarkCase` consistente por tenant, a Fase 4 perde comparabilidade;
- sem `required_terms` e hints de grounding, `expected_context_coverage` nao existe;
- sem melhor curadoria de `reference_answer`, `context_precision` e `context_recall` permanecem parcialmente bloqueadas.

## Status deste bloco

Implementado agora:

- decisao objetiva da stack primaria de avaliacao;
- contrato Python offline da avaliacao formal;
- executor offline do benchmark para avaliacao formal;
- registro minimo da run no `MLflow` local;
- snapshot comparativo JSON/CSV por experimento e tenant;
- ranking JSON de casos da run atual;
- catalogo explicito de metricas obrigatorias e complementares iniciais;
- agregacao minima por run sem acoplamento ao runtime transacional;
- documentacao dos limites metodologicos da medicao.

Preparado, mas nao concluido agora:

- curadoria adicional de `reference_answer` para destravar `context_precision` e `context_recall` em toda a baseline.
