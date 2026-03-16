# Fase 5 — Retrieval Hibrido, Query Rewriting e Reranking

## Objetivo deste documento

Registrar o fechamento estrutural do bloco:

- `CPPX-F5-T1 — Definir arquitetura alvo de retrieval híbrido`

Este documento descreve:

- o estado atual resumido da camada de retrieval;
- os pontos corretos de extensão no código;
- a arquitetura-alvo incremental da Fase 5;
- como as variantes devem ser comparadas experimentalmente;
- os limites deste bloco e o que permanece para os próximos cortes.

Este documento nao declara como implementado:

- retrieval híbrido completo em runtime;
- query rewriting ativo no request path;
- reranking ativo no runtime ou no benchmark;
- promoção de nova estratégia como default.

## Enquadramento do bloco

- ciclo atual: Fase 1 — LLMOps, avaliação e governança
- fase ativa: Fase 5 — Retrieval híbrido, query rewriting e reranking
- branch de trabalho: `feat/fase5-retrieval-query-reranking`
- task coberta agora: `CPPX-F5-T1`
- critério de aceite do bloco: arquitetura-alvo pequena, incremental, tenant-aware e comparável por benchmark/tracking
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

Ponto relevante para a Fase 5:

- antes deste bloco, o executor offline repetia parte da lógica de candidate pool e do score lexical+semântico;
- isso aumentava o risco de divergência entre baseline do runtime e baseline do benchmark.

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
- depois adicionar candidatos lexicais;
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
- este bloco nao cria artefatos novos de rewriting ou reranking.

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
- o resultado técnico do retrieval passa a expor `params_used.strategy_name` para tornar o baseline visível no payload.

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
- contrato mínimo preparatório no artefato de retrieval para nome da estratégia, pesos e candidate pool;
- remoção da duplicação principal entre runtime e executor offline no cálculo baseline do retrieval.

## O que fica explicitamente para os próximos blocos

- `CPPX-F5-T2`: camada lexical complementar real;
- `CPPX-F5-T3`: query rewriting ou expansion controlado;
- `CPPX-F5-T4`: reranking pós-recuperação;
- `CPPX-F5-T5`: exposição ampliada dos parâmetros experimentais novos;
- `CPPX-F5-T6`: comparação formal entre variantes;
- `CPPX-F5-T7`: consolidação da baseline vencedora ou matriz de trade-offs.

## Riscos e limites identificados

- o baseline atual nao e puramente semântico; ele já tem rescoring lexical simples, o que exige cuidado na nomenclatura das variantes futuras;
- o benchmark offline ainda depende de espelho manual do retrieval, mesmo após a redução de duplicação;
- query rewriting mal calibrado pode distorcer intenção e mascarar ganho artificial em cobertura;
- reranking pode melhorar relevância e ainda assim piorar custo/latência sem benefício suficiente;
- promover estratégia nova sem trocar o `retriever_version` ou sem registrar seus parâmetros quebraria comparabilidade.
