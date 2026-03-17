# Fase 6 - Observabilidade de Qualidade, Latencia e Custo por Tenant

## Objetivo deste documento

Registrar o bloco `CPPX-F6-T1 - Definir metricas de qualidade, custo e latencia por tenant` com foco em contrato minimo observavel, sem declarar implementacao ampla antes dos proximos blocos da fase.

Este documento cobre:

- matriz minima de metricas uteis para a Fase 6;
- dimensoes obrigatorias, opcionais e proibidas;
- separacao entre metricas operacionais, sinais de auditoria e sinais de tracking experimental;
- pontos naturais de instrumentacao no codigo atual;
- metodologia inicial para latencia por etapa, custo estimado e indicadores de qualidade/saude;
- lacunas explicitas do estado atual.

Este documento nao cobre:

- implementacao de dashboard;
- instalacao de novas dependencias;
- refatoracao estrutural ampla do runtime;
- mudancas de benchmark offline fora do necessario para contrato da fase.

## Enquadramento do bloco

- projeto: Chat Pref
- fase: Fase 6 - Observabilidade de Qualidade, Latencia e Custo por Tenant
- task: `CPPX-F6-T1`
- branch oficial da fase: `feat/observabilidade-latencia-custo`
- principio de execucao: menor diff coerente, preservando arquitetura tenant-aware

## Estado atual real (antes da instrumentacao da Fase 6)

### Runtime operacional

Sinais ativos hoje:

- endpoint `/metrics` com contadores/histograma basicos em `app/observability/metrics.py`;
- tracing por request e spans principais em `app/observability/middleware.py` e `app/services/chat_service.py`;
- correlacao por `request_id` e `tenant_id` nas trilhas de trace e log estruturado;
- auditoria operacional `audit.v1` por tenant em `app/storage/audit_repository.py`.

### Tracking experimental (fora do runtime transacional)

Sinais ativos hoje:

- `latency_ms` e `estimated_cost` no contrato de run experimental (`app/audit/contracts.py`);
- parametros experimentais por estrategia (retrieval/query transformation/rerank) em `app/llmops/tracking_integration.py`;
- metricas de avaliacao formal de RAG e artifacts no runner offline (`app/llmops/rag_evaluation_runner.py`).

### Lacuna declarada

- nao ha etapa de classificacao ativa no caminho transacional atual (diretorio `app/classifier/` sem modulo de runtime).

## Mapa do pipeline e pontos naturais de instrumentacao

| Etapa logica | Ponto candidato no codigo | Estado atual |
|---|---|---|
| Entrada de requisicao | `app/observability/middleware.py` (`RequestObservabilityMiddleware.dispatch`) | Ativo para trace/log e latencia HTTP agregada |
| Classificacao | `app/classifier/` | Nao aplicavel no runtime atual |
| Policy pre | `app/services/chat_service.py` (`policy_pre`) | Ativo em span e contador de policy |
| Query expansion | `app/services/rag_service.py` (`query_transformation_service.transform_query`) | Ativo como payload tecnico, sem metrica dedicada |
| Retrieval | `app/services/rag_service.py` e `app/services/chat_service.py` (`retrieval`) | Ativo com status e span; sem latencia por etapa em metrica dedicada |
| Composer / LLM | `app/services/chat_service.py` (`compose`, `compose.rewrite`) e `app/services/llm_service.py` | Ativo com latencia de composicao/fallback e metadados do provider |
| Policy post | `app/services/chat_service.py` (`policy_post`) | Ativo em span e contador de policy |
| Resposta final | `app/services/chat_service.py` (`response`) e `app/storage/chat_repository.py` | Ativo com persistencia e trace |
| Fallback / bloqueio / vazio | `app/services/chat_service.py` + `app/services/rag_service.py` | Ativo em eventos/contadores parcialmente agregados |

## Matriz minima de metricas da Fase 6

### 1) Metricas operacionais (runtime transacional)

| Nome tecnico | Tipo | Leitura principal | Status no bloco T1 |
|---|---|---|---|
| `chatpref_pipeline_requests_total` | Counter | Volume de requests por tenant e canal | Definida em contrato |
| `chatpref_pipeline_stage_latency_seconds` | Histogram | Latencia por etapa (`stage_name`) | Definida em contrato |
| `chatpref_pipeline_estimated_cost_usd_total` | Counter | Custo estimado acumulado por tenant | Definida em contrato |
| `chatpref_pipeline_fallback_total` | Counter | Taxa de fallback por tenant e motivo | Ativo (T4) |
| `chatpref_pipeline_policy_block_total` | Counter | Bloqueios de policy por etapa | Ativo (T4) |
| `chatpref_pipeline_retrieval_empty_total` | Counter | Retrieval vazio por tenant | Ativo (T4) |

### 2) Sinais de auditoria operacional (nao misturar com tracking)

| Sinal | Origem | Papel |
|---|---|---|
| `audit_v1_pipeline_events_total` (derivavel) | `app/services/chat_service.py` + `app/storage/audit_repository.py` | Contagem por `event_type` e tenant para leitura operacional |
| eventos de policy (`policy_pre_evaluated`, `policy_post_evaluated`) | `audit.v1` | Explicar decisao no atendimento, nao comparar experimento |
| eventos de retrieval/fallback | `audit.v1` | Evidenciar comportamento real do request |

### 3) Sinais de tracking experimental (fora do runtime)

| Sinal | Origem | Papel |
|---|---|---|
| `tracking_run_latency_ms` | `app/llmops/tracking_integration.py` | Latencia de run comparavel por tenant e estrategia |
| `estimated_cost` (run) | `app/audit/contracts.py` | Custo estimado de execucao experimental |
| metricas de qualidade do benchmark (`faithfulness_mean`, `answer_relevance_mean`, `retrieval_empty_rate`) | `app/llmops/rag_evaluation_runner.py` | Qualidade experimental do RAG por dataset e configuracao |

### 4) Sinais apenas de contrato/documentacao neste bloco

| Sinal | Motivo |
|---|---|
| `chatpref_pipeline_classification_latency_seconds` | Etapa de classificacao nao existe no runtime transacional atual |
| Correlacao trace-run automatica ponta a ponta | Fica como preparacao contratual para `CPPX-F6-T5` |

## Dimensoes (tags) da Fase 6

### Obrigatorias

- `tenant_id`
- `stage_name`

### Opcionais (permitidas conforme a metrica)

- `channel`
- `status`
- `result`
- `reason_code`
- `retrieval_strategy_name`
- `query_transform_strategy_name`
- `rerank_strategy_name`
- `llm_provider`
- `llm_model`

### Proibidas

- `message`
- `user_message`
- `assistant_message`
- `document_text`
- `full_name`
- `email`
- `phone`
- `cpf`
- `token_raw`

Justificativa:

- evitar vazamento de conteudo sensivel na telemetria;
- controlar cardinalidade para manter utilidade operacional;
- preservar separacao entre metricas e dados de negocio/sessao.

## Metodologia inicial

### Latencia por etapa

Regra do bloco T1:

- medicao por estagio logico com `stage_name` canonicamente definido;
- inicio/fim no ponto natural da etapa (span ou fronteira de funcao);
- unidade padrao em segundos para metricas (`*_seconds`), mantendo conversao para ms apenas em payload textual quando necessario.

Estagios alvo iniciais:

- `request_entry`
- `policy_pre`
- `query_expansion`
- `retrieval`
- `composer`
- `policy_post`
- `response_final`
- `fallback`
- `blocked`

### Custo estimado

Regra do bloco T1:

- custo e estimado, nao faturamento real;
- `LLM_PROVIDER=mock` deve permanecer explicitamente com custo `0.0`;
- para provedores reais, usar metodologia deterministica e documentada por versao.

Formula inicial proposta (contrato, ainda sem rollout amplo no runtime):

- `estimated_input_tokens ~= input_chars / 4`
- `estimated_output_tokens ~= output_chars / 4`
- `estimated_cost_usd = ((estimated_input_tokens / 1000) * input_unit_price_usd) + ((estimated_output_tokens / 1000) * output_unit_price_usd)`

Observacao:

- sem dependencia nova de tokenizador nesta task;
- os coeficientes e precos devem ser versionados como configuracao em bloco posterior.

### Indicadores de qualidade e saude operacional

Conjunto minimo para leitura operacional da Fase 6:

- `fallback_rate` (derivado de `chatpref_pipeline_fallback_total / chatpref_pipeline_requests_total`)
- `policy_block_rate` (derivado de bloqueios por policy)
- `retrieval_empty_rate` (derivado de retrieval vazio)
- latencia p95 por etapa critica (`retrieval`, `composer`, `policy_post`)

Regra de leitura:

- usar indicadores operacionais para operacao do runtime;
- usar metricas experimentais (benchmark/tracking) para comparacao tecnica;
- nao fundir auditoria operacional com tracking experimental.

## Correlacao entre tracing operacional e tracking experimental

Estado no bloco T1:

- correlacao definida como contrato de preparacao;
- implementacao ponta a ponta fica para blocos posteriores da Fase 6.

Contrato minimo de correlacao:

- chave primaria: `request_id`
- chave de segregacao: `tenant_id`
- chave contextual de experimento: `dataset_version` + estrategias (`retrieval_strategy_name`, `query_transform_strategy_name`, `rerank_strategy_name`) quando aplicavel.

## Artefato de contrato em codigo

Para sustentar os proximos blocos sem inflar escopo, este bloco introduz contrato pequeno em:

- `app/observability/phase6_contracts.py`

Conteudo do contrato:

- matriz minima de metricas da Fase 6;
- dimensoes obrigatorias/opcionais/proibidas;
- pontos candidatos de instrumentacao;
- status por sinal (`active`, `planned`, `not_applicable_current_runtime`).

## Decisoes do bloco (T1)

1. A fase passa a ter naming tecnico canonico de metricas para qualidade, latencia e custo por tenant.
2. A separacao entre metrica operacional, auditoria e tracking experimental fica explicita no contrato.
3. A etapa de classificacao permanece somente como contrato futuro, sem simulacao no runtime atual.
4. A correlacao trace-tracking permanece como preparacao contratual, sem declarar implementacao total.

## O que ficou para os proximos blocos da Fase 6

- `CPPX-F6-T2`: instrumentacao de latencia por estagio no runtime
- `CPPX-F6-T3`: registro operacional de custo estimado por request
- `CPPX-F6-T4`: exposicao operacional de fallback/bloqueio/retrieval vazio
- `CPPX-F6-T5`: correlacao operacional-tracking em trilha tecnicamente verificavel
- `CPPX-F6-T6`: painel tecnico minimo
- `CPPX-F6-T7`: guia de leitura operacional final

## Atualizacao do bloco CPPX-F6-T2

Estado implementado no runtime apos este bloco:

- serie Prometheus `chatpref_pipeline_stage_latency_seconds` ativa em `/metrics`;
- labels usadas na serie: `tenant_id`, `stage_name`, `channel`, `status`;
- instrumentacao com ponto reutilizavel central em `app/observability/metrics.py` (`track_pipeline_stage_latency`);
- estagios hoje observaveis no fluxo transacional:
	- `policy_pre`
	- `query_expansion`
	- `retrieval`
	- `composer`
	- `policy_post`
	- `response_final`

Lacunas mantidas de forma explicita:

- `classification` continua nao aplicavel ao runtime atual por ausencia de etapa ativa no caminho transacional;
- fallback/bloqueio/retrieval vazio como metricas dedicadas e correlacao trace-run continuam para blocos seguintes da Fase 6.

## Atualizacao do bloco CPPX-F6-T3

Estado implementado no runtime apos este bloco:

- serie Prometheus `chatpref_pipeline_estimated_cost_usd_total` ativa em `/metrics`;
- labels usadas na serie: `tenant_id`, `stage_name`, `channel`, `status`, `llm_provider`, `llm_model`;
- metodologia centralizada em `app/observability/cost_estimation.py`, sem valores magicos espalhados;
- configuracao central minima em `app/settings.py` para heuristica de token e preco por 1k tokens.

Metodologia aplicada por etapa:

- `composer` (LLM):
	- `provider=mock` -> custo operacional `0.0` com status `non_billed`;
	- provedores nao-mock -> custo estimado por heuristica `chars_per_token_heuristic_v1`.
- `retrieval`:
	- runtime atual com Chroma local -> custo operacional `0.0` com status `non_billed`;
	- nao ha estimativa monetaria externa de retrieval neste bloco.

Leitura honesta dos limites:

- o valor de `composer` fora de `mock` e estimado por heuristica de caracteres, nao e custo contabil exato;
- o custo de retrieval em infraestrutura externa (quando existir) permanece nao mensuravel no runtime atual e fica para evolucao posterior.

## Atualizacao do bloco CPPX-F6-T5

Estado implementado no runtime apos este bloco:

- o `CorrelationContext` de observabilidade em `app/observability/context.py` foi estendido para incluir `run_id`, `parent_run_id` e `strategy_name`;
- o `ChatService` agora propaga esses identificadores para o contexto de correlacao e para os spans do OpenTelemetry a partir do `audit_context` do request;
- o endpoint `/api/chat` agora aceita headers `X-Parent-Run-ID` e `X-Strategy-Name` para injetar contexto experimental;
- o `X-Request-ID` passa a ser usado como `run_id` quando presente;
- a chamada ao `RagService` a partir do `ChatService` agora propaga o `run_id`, permitindo que o `ActiveArtifactResolver` resolva configuracoes experimentais a partir de uma run do MLflow, caso o `mlflow` esteja disponivel no ambiente.

Leitura honesta dos limites:

- a correlacao e minima e depende da injecao externa dos headers;
- a resolucao de parametros a partir da run de MLflow e opcional e tratada com um import seguro para nao quebrar o runtime se `mlflow` nao estiver instalado;
- nao ha garantia de que *toda* execucao tera um `run_id` associado, apenas aquelas iniciadas com o devido contexto (ex: smoke tests da Fase 10).
