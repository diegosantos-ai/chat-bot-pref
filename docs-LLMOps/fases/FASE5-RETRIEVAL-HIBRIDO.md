# Fase 5 — Retrieval Hibrido, Query Rewriting e Reranking

## Objetivo deste documento

Registrar o fechamento estrutural dos blocos:

- `CPPX-F5-T1 — Definir arquitetura alvo de retrieval híbrido`
- `CPPX-F5-T2 — Implementar camada lexical complementar`
- `CPPX-F5-T3 — Implementar query rewriting ou expansion controlado`
- `CPPX-F5-T4 — Integrar reranker ao pipeline de recuperação`
- `CPPX-F5-T5 — Expor parâmetros experimentais de retrieval avançado`
- `CPPX-F5-T6 — Executar comparação entre estratégias`
- `CPPX-F5-T7 — Consolidar baseline vencedora ou matriz de trade-offs`

Este documento descreve:

- o estado atual resumido da camada de retrieval;
- os pontos corretos de extensão no código;
- a arquitetura-alvo incremental da Fase 5;
- como as variantes devem ser comparadas experimentalmente;
- a decisão de fechamento da Fase 5 para o recorte atual;
- os limites deste bloco e o que permanece experimental.

Este documento nao declara:

- vencedor absoluto fora do recorte atual do benchmark offline;
- superioridade generalizada de query expansion heurística ou reranking heurístico.

## Enquadramento do bloco

- ciclo atual: Fase 1 — LLMOps, avaliação e governança
- fase ativa: Fase 5 — Retrieval híbrido, query rewriting e reranking
- branch de trabalho: `feat/fase5-retrieval-query-reranking`
- tasks cobertas agora:
  - `CPPX-F5-T1`
  - `CPPX-F5-T2`
  - `CPPX-F5-T3`
  - `CPPX-F5-T4`
  - `CPPX-F5-T5`
  - `CPPX-F5-T6`
  - `CPPX-F5-T7`
- critério de aceite do bloco: arquitetura-alvo pequena, incremental, tenant-aware, com variante lexical real, query expansion opt-in, reranking pós-recuperação e comparabilidade por benchmark/tracking
- validação mínima deste bloco:
  - leitura cruzada entre `ARQUITETURA-LLMOps.md`, `PLANEJAMENTO-LLMOps.md` e o código do retrieval;
  - checagem de contratos do runtime e do executor offline;
  - testes locais focados no contrato de artefatos e no endpoint RAG.

## Estado atual resumido

### Runtime transacional

Hoje o caminho síncrono de retrieval continua pequeno e explícito:

1. `app/services/chat_service.py` chama `RagService.query(...)` quando `policy_pre` permite a consulta.
2. `app/services/rag_service.py` resolve `tenant_id`, `top_k`, `min_score` e monta `RagQueryResponse`.
3. `app/storage/chroma_repository.py` consulta a collection do tenant no Chroma e faz o corte final dos chunks.

Estado importante:

- o tenant permanece explícito no request e na collection;
- o runtime ainda usa uma única fonte de candidatos: Chroma por tenant;
- o score atual já mistura sinal semântico do vetor com sobreposição lexical simples do texto recuperado;
- nao existe hoje camada separada de lexical retrieval;
- nao existe hoje query rewriting de retrieval;
- nao existe hoje reranking posterior ao conjunto final de chunks.

### Benchmark offline e tracking experimental

O executor offline de Fase 4 em `app/llmops/rag_evaluation_runner.py`:

- nao toca auditoria operacional;
- reproduz o retrieval por tenant fora do endpoint HTTP;
- usa `build_phase2_tracking_run(...)` para registrar `tenant_id`, `dataset_version`, `retriever_version`, `retriever_version_id`, `top_k` e demais versões ativas no `MLflow`.

Pontos relevantes para a Fase 5:

- antes deste bloco, o executor offline repetia parte da lógica de candidate pool e do score lexical+semântico;
- isso aumentava o risco de divergência entre baseline do runtime e baseline do benchmark.
- antes deste bloco, nao existia geração lexical de candidatos fora do pool devolvido pelo Chroma.

## Pontos de extensão corretos no código

### 1. Resolução de configuração ativa

Arquivo principal:

- `app/llmops/active_artifacts.py`

Papel:

- resolver a configuração ativa de retrieval em `ai_artifacts/rag/retrieval/`;
- concentrar nome técnico da estratégia, pesos do score e tamanho do pool de candidatos;
- manter um local previsível para parâmetros futuros sem espalhar hardcodes pelo runtime.

### 2. Geração de candidatos semânticos do baseline

Arquivo principal:

- `app/storage/chroma_repository.py`

Papel:

- executar a busca vetorial tenant-aware atual;
- continuar sendo o adaptador do baseline baseado em Chroma;
- servir como ponto natural para manter o backend semântico isolado de futuras combinações híbridas.

Limite:

- a introdução de um retriever lexical complementar nao deve virar `if` disperso em `ChatService` ou no endpoint;
- a combinação de candidatos deve acontecer abaixo do serviço HTTP e acima do armazenamento bruto.

### 3. Score e corte do baseline atual

Arquivo novo preparado neste bloco:

- `app/rag/retrieval_scoring.py`

Papel:

- centralizar tokenização, score lexical simples, score ponderado do baseline e cálculo do candidate pool;
- reduzir divergência entre runtime e benchmark offline;
- oferecer um ponto pequeno e explícito para a futura substituição do score baseline por fusão híbrida ou reranking.

### 4. Orquestração do retrieval no runtime

Arquivos:

- `app/services/chat_service.py`
- `app/services/rag_service.py`

Papel:

- continuar coordenando somente contrato de entrada/saída do retrieval;
- nao absorver lógica de rewriting, fusão híbrida ou reranking diretamente.

Diretriz:

- query rewriting deve entrar antes da recuperação;
- reranking deve entrar depois da montagem do pool de candidatos;
- o serviço HTTP deve continuar enxergando um contrato simples de query e resposta.

### 5. Espelho offline do retrieval para benchmark

Arquivo:

- `app/llmops/rag_evaluation_runner.py`

Papel:

- continuar executando retrieval fora do runtime transacional;
- espelhar a lógica baseline sem duplicar regras sensíveis;
- expor a variante comparada via `retriever_version` e `retriever_version_id` no tracking experimental.

## Arquitetura-alvo incremental

### Decisão estrutural 1

O baseline atual passa a ser tratado explicitamente como:

- candidatos semânticos do Chroma por tenant;
- rescoring lexical simples sobre os candidatos;
- corte final por `top_k`.

Isto nao e o retrieval híbrido final da Fase 5. E apenas o baseline herdado que precisa permanecer comparável.

### Decisão estrutural 2

Retrieval híbrido futuro deve ser introduzido em camadas pequenas:

1. baseline semântico atual explicitado
2. fonte lexical complementar de candidatos
3. fusão controlada de candidatos
4. query rewriting opcional antes da recuperação
5. reranking opcional após a recuperação inicial

Ordem escolhida:

- primeiro tornar o baseline observável e configurável;
- depois adicionar candidatos lexicais reais por varredura da collection do tenant;
- só então avaliar rewriting e reranking sobre um pool já comparável.

### Decisão estrutural 3

Query rewriting nao deve nascer dentro de `policy_post`, nem como efeito colateral do fallback atual.

Ele deve ser tratado como etapa própria de preparação da consulta, com estes limites:

- entrada: pergunta original do usuário e contexto institucional mínimo;
- saída: query original + variantes controladas ou decisão de nao reescrever;
- uso inicial preferencial: benchmark offline ou ativação experimental explícita;
- sem promoção silenciosa para o runtime default.

### Decisão estrutural 4

Reranking nao deve substituir o retriever base nem se misturar ao armazenamento.

Ele deve operar sobre um pool já recuperado, com:

- lista de candidatos;
- metadados do tenant;
- parâmetros explícitos da variante;
- corte final claro para comparação com baseline.

## Parametros experimentais previstos

Parametros que passam a ter local previsível de resolução:

- `strategy_name`
- `supported_strategies`
- `top_k_default`
- `min_score_default`
- `candidate_pool_multiplier`
- `score_weights`

Local ativo agora:

- `ai_artifacts/rag/retrieval/tenant_chroma_hash_v1.json`
- `app/llmops/active_artifacts.py`

Parametros previstos para próximos blocos, ainda nao criados como contrato ativo:

- identificador da fonte lexical complementar;
- política de query rewriting;
- tamanho do pool antes de reranking;
- estratégia de fusão híbrida;
- identificador do reranker;
- pesos de fusão entre variantes.

Regra:

- novos parâmetros só devem virar artefato ativo quando houver implementação mínima comparável;
- este bloco ainda nao cria artefatos novos de rewriting ou reranking.

## O que foi implementado em `CPPX-F5-T2`, `CPPX-F5-T3` e `CPPX-F5-T4`

- uma variante opcional de retrieval chamada `semantic_plus_full_collection_lexical_candidates_v1`;
- geração lexical real de candidatos por varredura de todos os chunks da collection já persistida do tenant;
- união entre:
  - candidatos do baseline semântico do Chroma;
  - candidatos lexicais recuperados pelo full scan da collection;
- reaproveitamento da mesma lógica da variante no runtime e no executor offline.

Implementação factual:

- o baseline continua usando apenas candidatos vindos da consulta semântica do Chroma, com rescoring lexical simples;
- a nova variante faz `collection.get(...)` da collection do tenant, calcula overlap lexical simples chunk a chunk e monta um pool lexical complementar;
- o resultado final da variante híbrida do bloco é a união deduplicada entre candidatos semânticos e candidatos lexicais, preservando o maior score por chunk.
- a etapa de query transformation ficou separada do retrieval e foi resolvida como eixo próprio de configuração, sem renomear artificialmente as variantes de retrieval;
- a estratégia `tenant_keyword_query_expansion_v1` usa apenas metadados `keywords` dos documentos do tenant para adicionar poucos termos novos quando houver overlap com a query original;
- a query original continua íntegra no contrato de resposta e a query efetivamente usada no retrieval passa a ser registrada em `params_used.query_transformation.retrieval_query`.
- a etapa de reranking ficou separada do retrieval base e da query transformation, com strategy própria chamada `heuristic_post_retrieval_rerank_v1`;
- o reranker atual opera apenas sobre os candidatos já recuperados, sem ampliar o universo de busca;
- o reranking usa a query original do usuário, e nao a query expandida, para recentrar a ordenação na intenção original após a recuperação.

## Limitações atuais do reranking

- o reranker atual é heurístico, nao é cross-encoder nem reranker semântico robusto;
- ele usa apenas sinais já disponíveis localmente: `retrieval_score`, overlap com `title`, overlap com `tags` e densidade lexical no texto do chunk;
- ele atua sobre até `max_candidates` chunks já recuperados, o que preserva custo e comparabilidade, mas limita ganho potencial quando o candidato ideal ficou fora do pool do retrieval;
- o reranking atual pode reordenar os chunks e recalcular o `score` final, mas preserva rastreabilidade do `retrieval_score` original no payload técnico;
- a latência adicional tende a ser pequena, mas ainda cresce linearmente com a quantidade de candidatos reranqueados.

## Limitações atuais da query expansion

- a expansão atual é heurística e local; ela nao usa LLM, embeddings extras nem biblioteca externa;
- ela só consulta metadados de documentos já persistidos localmente por tenant;
- por padrão, a fonte ativa de expansão fica restrita a `keywords`, justamente para reduzir ruído e distorção de intenção;
- se nao houver overlap suficiente entre query e metadados do tenant, a estratégia continua registrada, mas nao transforma a query;
- a expansão atual melhora recall potencial, mas nao implica melhoria automática de grounding, precisão ou latência.

## Limitações atuais da camada lexical

- a recuperação lexical atual nao usa BM25, inverted index nem biblioteca externa;
- ela faz varredura completa da collection já persistida no Chroma do tenant;
- o score lexical continua simples e baseado em tokenizer local + overlap de termos;
- chunks lexicais sem evidência semântica recebem score apenas lexical ponderado pelos pesos atuais do baseline;
- essa camada melhora cobertura de candidatos, mas ainda nao implementa fusão sofisticada nem reranker semântico avançado.

## Como comparar estratégias experimentalmente

### Tracking

A comparação experimental deve continuar separada da auditoria operacional e usar:

- `tenant_id`
- `dataset_version`
- `retriever_version`
- `retriever_version_id`
- `top_k`
- demais parâmetros de retrieval que vierem a ser ativados nos próximos blocos

No estado atual:

- a variante continua identificada no tracking por `retriever_version` e `retriever_version_id`;
- o resultado técnico do retrieval expõe `params_used.strategy_name`;
- o resultado técnico do retrieval expõe `params_used.experimental_axes` com:
  - `retrieval`, `query_transformation` e `reranking`;
  - `strategy_name`;
  - `supported_strategies`;
  - `params` ativos de cada eixo;
- o resultado técnico do retrieval expõe `params_used.query_transformation` com:
  - query original;
  - query usada no retrieval;
  - termos adicionados;
  - strategy_name aplicada;
- o resultado técnico do retrieval expõe `params_used.reranking` com:
  - strategy_name;
  - se houve aplicação;
  - sobre quantos candidatos o reranker rodou;
  - pesos ativos da heurística;
- o tracking experimental da run passa a registrar `retrieval_strategy_name`, `query_transform_strategy_name`, `rerank_strategy_name` e `phase5_experiment_axes_json` para distinguir os três eixos da execução dentro do mesmo `retriever_version`.

## Matriz experimental atualmente suportada

O contrato experimental consolidado da Fase 5 agora fica resolvido em `app/llmops/active_artifacts.py` por meio de um único objeto lógico com três eixos:

- `retrieval`
- `query_transformation`
- `reranking`

Cada eixo expõe:

- `strategy_name`
- `supported_strategies`
- `params`

No estado atual, a matriz suportada e comparável é:

- retrieval:
  - `semantic_candidates_with_lexical_rescoring_v1`
  - `semantic_plus_full_collection_lexical_candidates_v1`
- query transformation:
  - `no_query_transformation_v1`
  - `tenant_keyword_query_expansion_v1`
- reranking:
  - `no_rerank_v1`
  - `heuristic_post_retrieval_rerank_v1`

Parâmetros ativos por eixo hoje:

- retrieval:
  - `top_k_default`
  - `min_score_default`
  - `boost_enabled_default`
  - `candidate_pool_multiplier`
  - `score_weights`
- query transformation:
  - `max_added_terms`
  - `source_fields`
- reranking:
  - `max_candidates`
  - `score_weights`

### Benchmark

Toda comparação da Fase 5 deve preservar:

- mesmo tenant;
- mesmo recorte de benchmark;
- mesma baseline de prompt/policy quando a hipótese for só retrieval;
- leitura conjunta de qualidade, retrieval vazio, fallback e latência.

Critérios mínimos de leitura:

- melhoria ou piora de `faithfulness`;
- melhoria ou piora de `answer_relevance`;
- impacto em `expected_context_coverage_mean`;
- impacto em `retrieval_empty_rate`;
- impacto em latência total por run;
- casos em que a estratégia melhora grounding, mas piora custo ou latência.

## O que este bloco entrega agora

- arquitetura-alvo incremental da Fase 5 documentada;
- pontos corretos de extensão no código identificados;
- baseline atual descrito sem vender como retrieval híbrido completo;
- contrato mínimo do artefato de retrieval ampliado para listar estratégias suportadas;
- camada lexical complementar real por full scan da collection do tenant;
- integração opcional da nova estratégia no runtime RAG e no benchmark offline;
- query expansion heurística opt-in baseada em `keywords` do tenant;
- separação explícita entre query original e query efetivamente usada no retrieval;
- reranking heurístico opt-in aplicado após a recuperação inicial e antes da resposta técnica final;
- preservação do `retrieval_score` original quando o reranking está ativo;
- consolidação da superfície experimental da Fase 5 em um contrato único por eixo, resolvido a partir do artefato ativo e reaproveitado por runtime, benchmark offline, tracking e CLI;
- exposição explícita da matriz ativa em `params_used.experimental_axes` e em `phase5_experiment_axes_json` no tracking experimental;
- redução adicional de duplicação entre runtime e executor offline ao reaproveitar o repositório de retrieval.

## Comparativo preliminar executado em 2026-03-16

Execução realizada com:

- tenant: `prefeitura-vila-serena`
- dataset: `benchmark_v1`
- benchmark completo: `17` casos
- experimento MLflow: `chat-pref-fase5-retrieval-comparison`
- script de orquestração: `scripts/run_phase5_strategy_comparison.py`

Combinações executadas:

| Label | Retrieval | Query transformation | Reranking |
|---|---|---|---|
| `baseline_semantic_only` | `semantic_candidates_with_lexical_rescoring_v1` | `no_query_transformation_v1` | `no_rerank_v1` |
| `hybrid_lexical_only` | `semantic_plus_full_collection_lexical_candidates_v1` | `no_query_transformation_v1` | `no_rerank_v1` |
| `hybrid_plus_query_transform` | `semantic_plus_full_collection_lexical_candidates_v1` | `tenant_keyword_query_expansion_v1` | `no_rerank_v1` |
| `hybrid_plus_rerank` | `semantic_plus_full_collection_lexical_candidates_v1` | `no_query_transformation_v1` | `heuristic_post_retrieval_rerank_v1` |
| `hybrid_plus_query_transform_plus_rerank` | `semantic_plus_full_collection_lexical_candidates_v1` | `tenant_keyword_query_expansion_v1` | `heuristic_post_retrieval_rerank_v1` |

Métricas observadas:

| Label | Faithfulness | Answer relevance | Expected context coverage | Retrieval empty rate | Latência total da run (ms) |
|---|---:|---:|---:|---:|---:|
| `baseline_semantic_only` | `0.7500` | `0.0000` | `0.5385` | `0.1765` | `168.421` |
| `hybrid_lexical_only` | `0.8214` | `0.0000` | `0.7308` | `0.1765` | `182.013` |
| `hybrid_plus_query_transform` | `0.8214` | `0.0000` | `0.6538` | `0.1765` | `204.387` |
| `hybrid_plus_rerank` | `0.7857` | `0.0000` | `0.7308` | `0.1765` | `194.760` |
| `hybrid_plus_query_transform_plus_rerank` | `0.7500` | `0.0000` | `0.6538` | `0.1765` | `190.309` |

Contagens estruturais observadas em todas as combinações:

- `cases_total = 17`
- `cases_evaluated = 14`
- `cases_partial = 3`
- `cases_skipped = 0`

Leitura preliminar:

- `hybrid_lexical_only` foi a combinação com melhor sinal conjunto do recorte atual:
  - `faithfulness_mean` subiu de `0.7500` para `0.8214`;
  - `expected_context_coverage_mean` subiu de `0.5385` para `0.7308`;
  - a latência total da run aumentou `13.592 ms` frente à baseline.
- `hybrid_plus_query_transform` não trouxe ganho adicional sobre `hybrid_lexical_only`:
  - manteve `faithfulness_mean` em `0.8214`;
  - reduziu `expected_context_coverage_mean` para `0.6538`;
  - aumentou mais a latência total.
- `hybrid_plus_rerank` preservou o ganho de cobertura de `0.7308`, mas com `faithfulness_mean` inferior ao `hybrid_lexical_only` e custo de latência maior.
- `hybrid_plus_query_transform_plus_rerank` voltou ao mesmo `faithfulness_mean` da baseline e não superou a variante híbrida simples em cobertura.
- `answer_relevance_mean` ficou em `0.0000` em toda a matriz e não discriminou variantes neste recorte; por isso, ele não sustenta decisão isolada neste bloco.
- `retrieval_empty_rate` permaneceu em `0.1765` em todas as combinações; neste benchmark atual, a Fase 5 não alterou o vazio de retrieval medido.

Conclusão metodológica consolidada da Fase 5:

- `semantic_plus_full_collection_lexical_candidates_v1` sem query transformation e sem reranking foi promovida como baseline recomendada do recorte atual;
- a evidência atual não sustenta promoção de query expansion heurística ou reranking heurístico como complemento default da variante híbrida;
- a decisão continua honesta quanto aos limites: trata-se da melhor combinação no benchmark offline atual do tenant demonstrativo, e não de um vencedor absoluto fora desse recorte.

## Decisão final da Fase 5

Baseline recomendada do recorte atual:

- retrieval: `semantic_plus_full_collection_lexical_candidates_v1`
- query transformation: `no_query_transformation_v1`
- reranking: `no_rerank_v1`

Justificativa técnica:

- melhorou `faithfulness_mean` de `0.7500` para `0.8214`;
- melhorou `expected_context_coverage_mean` de `0.5385` para `0.7308`;
- manteve `retrieval_empty_rate` em `0.1765`;
- não exigiu query expansion nem reranking adicionais para sustentar esse ganho.

Decisão contratual:

- o artefato ativo de retrieval passa a resolver `semantic_plus_full_collection_lexical_candidates_v1` como `strategy_name` default;
- `query_transform_strategy_name` permanece em `no_query_transformation_v1`;
- `rerank_strategy_name` permanece em `no_rerank_v1`.

## O que foi promovido e o que permaneceu experimental

Promovido:

- `semantic_plus_full_collection_lexical_candidates_v1` como retrieval default do recorte atual da Fase 5.

Permanece experimental:

- `semantic_candidates_with_lexical_rescoring_v1` como baseline anterior, preservada para comparação e possível rollback controlado;
- `tenant_keyword_query_expansion_v1`, porque não sustentou ganho adicional suficiente sobre `hybrid_lexical_only`;
- `heuristic_post_retrieval_rerank_v1`, porque não sustentou ganho adicional suficiente para promoção;
- a combinação completa com query transformation e reranking, porque não superou a baseline recomendada.

## Checklist honesto de aceite da Fase 5

Entregue:

- arquitetura-alvo incremental da Fase 5 documentada;
- baseline anterior formalizada e mantida como variante comparável;
- camada lexical complementar real, tenant-aware e rastreável;
- query expansion controlada, opt-in e rastreável;
- reranking heurístico pós-recuperação, opt-in e rastreável;
- superfície experimental consolidada em três eixos explícitos;
- comparação reproduzível entre cinco combinações relevantes;
- fechamento formal com baseline recomendada do recorte atual.

Não entregue:

- query rewriting por LLM;
- índice lexical dedicado;
- reranker semântico robusto ou cross-encoder;
- demonstração de ganho generalizado fora do benchmark atual;
- decisão universal de baseline para qualquer tenant, corpus ou cenário futuro.

## Riscos e limites identificados

- o baseline atual nao e puramente semântico; ele já tem rescoring lexical simples, o que exige cuidado na nomenclatura das variantes futuras;
- a camada lexical atual depende de full scan da collection, o que é honesto para este bloco, mas ainda nao escala como um índice lexical dedicado;
- a query expansion atual depende da qualidade e da cobertura dos `keywords` cadastrados no tenant;
- query rewriting mal calibrado pode distorcer intenção e mascarar ganho artificial em cobertura, por isso a etapa continua opt-in e rastreável;
- o reranker atual pode favorecer títulos e tags bem curados, mas nao resolve ausência de candidatos bons no pool inicial;
- reranking pode melhorar relevância e ainda assim piorar custo/latência sem benefício suficiente;
- a promoção atual se apoia em um único recorte de benchmark tenant-aware; novos tenants ou corpus mais amplos podem exigir reabertura da decisão;
- `answer_relevance_mean` continuou não discriminativo no recorte atual, então a decisão não deve ser lida como consenso de todas as métricas;
- promover estratégia nova sem trocar o `retriever_version` ou sem registrar seus parâmetros quebraria comparabilidade.
