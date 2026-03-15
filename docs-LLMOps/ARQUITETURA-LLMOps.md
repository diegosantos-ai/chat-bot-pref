# ARQUITETURA-LLMOps

## Objetivo do documento

Este documento descreve a arquitetura-alvo da fase de **LLMOps, avaliação formal, governança e observabilidade avançada** do Chat Pref.

Seu objetivo é registrar como a solução evolui a partir da **Fundação Operacional**, preservando os contratos já validados no runtime atual e introduzindo, de forma controlada, as novas capacidades necessárias para rastreabilidade experimental, avaliação reproduzível, governança de artefatos e observabilidade ampliada.

Este documento não substitui a arquitetura da fundação operacional. Ele a complementa, delimitando:

- a base herdada do ciclo anterior;
- os novos componentes e responsabilidades da fase LLMOps;
- a separação entre estado atual e arquitetura-alvo;
- os contratos técnicos que passam a orientar a nova etapa.

## Princípio de leitura

A leitura deste documento deve observar a seguinte distinção:

- **estado atual**: componentes, contratos e fluxos já validados na base operacional;
- **arquitetura-alvo**: componentes e fluxos planejados para esta nova fase;
- **fora do runtime transacional**: elementos de avaliação, reindexação, benchmark e orquestração offline que não pertencem ao caminho síncrono principal da requisição.

Nenhum componente deve ser tratado como ativo apenas por estar descrito aqui. A documentação deve preservar separação explícita entre o que já existe em produção local/remota e o que está sendo introduzido como parte do novo ciclo.

## Base arquitetural herdada

A nova fase parte de uma fundação já estabelecida.

A base herdada inclui, em termos funcionais e conceituais:

- backend FastAPI como ponto de entrada principal;
- pipeline transacional de atendimento;
- segregação por `tenant_id`;
- correlação mínima por `request_id`;
- integração com camada RAG;
- guardrails e políticas de resposta;
- trilha mínima de auditoria operacional;
- observabilidade inicial;
- contratos de execução já estabilizados;
- documentação da arquitetura operacional consolidada.

Essa fundação permanece válida e continua sendo a base de execução do sistema.

## Diretriz arquitetural da fase

A arquitetura da fase LLMOps segue cinco diretrizes estruturais:

1. **tenant-awareness como requisito transversal**  
   Nenhuma camada nova deve misturar dados, métricas, experimentos ou artefatos de tenants distintos de forma insegura.

2. **separação entre operação e experimento**  
   O fluxo operacional de atendimento e a trilha de experimentação devem coexistir sem se confundir.

3. **benchmark antes de otimização**  
   Evoluções de prompt, retrieval, modelo ou policy devem nascer comparáveis.

4. **instrumentação antes de sofisticação**  
   A arquitetura deve medir antes de sofisticar.

5. **estado atual distinto de arquitetura-alvo**  
   O documento deve continuar distinguindo com rigor o que já está validado do que ainda está em implantação.

## Arquitetura-alvo da fase

A arquitetura-alvo desta fase adiciona à base operacional uma nova camada de capacidades, distribuída em seis blocos principais:

- camada de experiment tracking;
- camada de versionamento de artefatos de IA;
- camada de avaliação formal do pipeline;
- camada de observabilidade ampliada;
- camada de orquestração offline;
- camada de governança e explicabilidade técnica.

Esses blocos se conectam à fundação operacional sem substituir o pipeline principal de atendimento.

## Visão lógica da arquitetura

```text
Usuário / Cliente
        |
        v
   API FastAPI
        |
        v
Pipeline Transacional de Atendimento
(Classificação -> Policy Guard -> Query Expansion -> Retrieval -> Composer -> Policy Post)
        |
        +------------------------------+
        |                              |
        v                              v
Auditoria Operacional            Observabilidade Operacional
(PostgreSQL / logs / traces)     (metrics / traces / correlação)
        |
        |
        +--------------------------------------------------+
        |                                                  |
        v                                                  v
Camada de Experiment Tracking                     Camada de Governança Técnica
(MLflow / runs / params / metrics / artifacts)   (versionamento / evidência / reason codes)
        |
        v
Camada de Avaliação Formal
(benchmark / RAG evaluation / comparação entre versões)
        |
        v
Camada Offline de Orquestração
(ingestão / reindexação / avaliação recorrente / deriva semântica)
````

## Bloco 1 — Pipeline transacional de atendimento

### Papel

Permanece como núcleo síncrono da aplicação.

### Responsabilidades

* receber a requisição;
* validar contexto do tenant;
* aplicar políticas de entrada e saída;
* acionar retrieval e composição;
* produzir resposta final;
* registrar trilha operacional mínima;
* expor sinais observáveis do request.

### Situação

**Estado atual herdado da fundação operacional.**

### Observação

A fase LLMOps não substitui este pipeline. Ela adiciona camadas de medição, comparação, governança e avaliação ao redor dele.

## Bloco 2 — Auditoria operacional

### Papel

Registrar o atendimento enquanto evento operacional e institucional.

### Responsabilidades

* persistir fatos operacionais do atendimento;
* registrar contexto mínimo do request;
* armazenar resultado de policy, fallback, bloqueios e trilha de execução aplicável;
* sustentar histórico funcional do sistema.

### Situação

**Estado atual herdado da fundação operacional.**

### Limite arquitetural

Auditoria operacional **não** é experiment tracking.

Ela responde perguntas como:

* quem foi atendido;
* em qual tenant;
* com qual resultado operacional;
* sob qual decisão de policy;
* em qual janela temporal.

Ela **não** deve ser sobrecarregada com:

* comparações entre versões de prompt;
* tracking de benchmark;
* artifacts de avaliação;
* scoring experimental.

## Bloco 3 — Experiment Tracking

### Papel

Registrar execuções técnicas e comparações controladas do ecossistema de IA.

### Responsabilidades

* registrar `runs` experimentais;
* armazenar `params`, `metrics`, `artifacts` e metadados;
* correlacionar experimento a `tenant_id`, versão de prompt, versão de retrieval e versão de embeddings;
* suportar comparação entre execuções;
* servir como base para análise de regressão e evolução.

### Situação

**Arquitetura-alvo da fase.**

### Tecnologia-alvo

* MLflow como camada principal de tracking experimental.

### Contratos mínimos esperados

Cada execução experimental deverá, quando aplicável, registrar:

* `tenant_id`
* `experiment_name`
* `run_id`
* `prompt_version`
* `policy_version`
* `retriever_version`
* `embedding_version`
* `dataset_version`
* `model_provider`
* `model_name`
* `top_k`
* `latency_ms`
* `estimated_cost`
* métricas de qualidade do experimento
* artifacts comparativos

### Regra de segregação

Toda execução experimental deve ser isolável por tenant e por versão de artefato.

## Bloco 4 — Versionamento de artefatos de IA

### Papel

Controlar a evolução de prompts, policies e parâmetros críticos do pipeline de IA.

### Responsabilidades

* versionar prompts base, fallback e guardrails;
* versionar policies e regras textuais;
* versionar configuração de retrieval;
* versionar chunking, top_k e parâmetros experimentais;
* registrar metadados mínimos para comparação;
* sustentar rollback e promoção controlada.

### Situação

**Arquitetura-alvo da fase.**

### Artefatos versionáveis previstos

* prompt de sistema
* prompt de composição
* prompt de fallback
* policy pre
* policy post
* configuração de retrieval
* configuração de chunking
* estratégia de reranking
* dataset de benchmark
* versão da base vetorial

### Observação

Versionamento não deve existir apenas como convenção oral ou nome de arquivo ad hoc. Deve ser tratável como contrato técnico.

## Bloco 5 — Avaliação formal do pipeline RAG

### Papel

Medir, comparar e qualificar o desempenho do pipeline de recuperação e resposta.

### Responsabilidades

* executar benchmark reproduzível;
* medir qualidade de resposta e fidelidade ao contexto;
* comparar versões de prompts, retrieval e bases vetoriais;
* registrar resultados experimentais;
* produzir artifacts de análise.

### Situação

**Arquitetura-alvo da fase.**

### Capacidades previstas

* dataset estruturado por tenant e cenário;
* benchmark recorrente;
* avaliação por métricas formais;
* comparação entre estratégias de retrieval;
* comparação entre modelos e versões de prompt.

### Métricas-alvo

Conforme a fase evoluir, o sistema deverá permitir registrar, ao menos:

* `faithfulness`
* `answer_relevance`
* métricas de contexto/recuperação
* latência
* custo estimado
* taxa de fallback
* taxa de retrieval vazio

### Observação

A arquitetura deve permitir tanto execução local de benchmark quanto execução automatizada em pipeline ou job offline.

## Bloco 6 — Retrieval avançado

### Papel

Aumentar a qualidade da recuperação de contexto por meio de estratégias comparáveis e controladas.

### Responsabilidades

* combinar busca semântica e lexical;
* suportar query rewriting ou query expansion controlado;
* integrar reranking;
* expor parâmetros experimentais;
* permitir comparação entre estratégias.

### Situação

**Arquitetura-alvo da fase.**

### Estratégias previstas

* retrieval semântico como baseline
* retrieval híbrido semântico + lexical
* query rewriting ou expansion
* reranking posterior à recuperação inicial

### Regra arquitetural

Nenhuma estratégia adicional deve ser consolidada sem benchmark comparativo.

## Bloco 7 — Observabilidade ampliada

### Papel

Expandir a observabilidade do sistema para além da saúde técnica básica, incorporando sinais de qualidade e eficiência da camada de IA.

### Responsabilidades

* medir latência por estágio;
* registrar custo estimado por execução;
* expor indicadores de qualidade operacional;
* correlacionar tracing operacional com tracking experimental;
* permitir leitura por tenant, pipeline e versão.

### Situação

**Parcialmente herdado da fundação operacional; ampliado nesta fase.**

### Capacidades previstas

* latência por etapa do pipeline;
* métricas de fallback e bloqueio;
* métricas de retrieval vazio;
* correlação entre `request_id` e execução experimental;
* dashboards técnicos com leitura operacional.

### Observação

Observabilidade nesta fase deixa de ser apenas telemetria de infraestrutura e passa a incluir telemetria de comportamento do pipeline de IA.

## Bloco 8 — Orquestração offline

### Papel

Executar processos que não pertencem ao fluxo síncrono da requisição.

### Responsabilidades

* ingestão de documentos;
* reindexação da base vetorial;
* execução de benchmark recorrente;
* avaliação offline;
* monitoramento de deriva semântica;
* rotinas recorrentes por tenant.

### Situação

**Arquitetura-alvo da fase.**

### Tecnologia-alvo

* Airflow em ambiente separado do backend principal.

### Regra arquitetural

Nenhum processo offline deve ser acoplado ao caminho crítico de requisição quando puder ser executado como job desacoplado.

## Bloco 9 — Monitoramento de deriva semântica

### Papel

Detectar sinais de deterioração da qualidade semântica da base de conhecimento por tenant.

### Responsabilidades

* comparar desempenho entre versões de base vetorial;
* identificar queda de relevância ou aumento de fallback;
* sinalizar degradações associáveis a base, retrieval ou modelo;
* sustentar reavaliação de ingest, chunking e configuração.

### Situação

**Arquitetura-alvo da fase.**

### Sinais previstos

* queda de métricas de benchmark;
* piora de contexto recuperado;
* aumento de retrieval vazio;
* aumento de fallback;
* perda de consistência em respostas antes estáveis.

### Observação

Deriva semântica deve ser tratada como fenômeno mensurável, não como percepção informal de piora.

## Bloco 10 — Governança e explicabilidade técnica

### Papel

Consolidar trilha técnica de decisão do pipeline de IA.

### Responsabilidades

* explicitar versão de prompt, policy e retrieval por execução;
* registrar reason codes e eventos relevantes;
* correlacionar contexto recuperado, decisão de policy e resposta;
* sustentar explicabilidade técnica da resposta produzida.

### Situação

**Parcialmente herdado da fundação operacional; ampliado nesta fase.**

### Resultado esperado

Capacidade de responder, tecnicamente:

* qual contexto foi utilizado;
* qual policy incidiu;
* qual versão de artefato estava ativa;
* por que houve bloqueio, fallback ou resposta final;
* sob qual configuração a execução ocorreu.

## Separação entre camadas

### Auditoria operacional

Responsável por fatos operacionais do atendimento.

### Tracking experimental

Responsável por fatos comparativos e técnicos do ciclo de IA.

### Benchmark

Responsável por medir qualidade em conjunto controlado.

### Orquestração offline

Responsável por tarefas desacopladas do fluxo síncrono.

### Observabilidade

Responsável por métricas, traces e leitura operacional/técnica da execução.

Essas camadas se relacionam, mas não devem ser fundidas em uma única estrutura de responsabilidade.

## Contratos transversais da fase

Os seguintes contratos passam a ser estruturais na nova fase:

* `tenant_id` como eixo obrigatório de segregação
* `request_id` como eixo de correlação operacional
* `artifact_version` para prompts, policies e retrieval
* `dataset_version` para benchmark
* `run_id` para tracking experimental
* distinção explícita entre estado operacional e estado experimental

## Estado atual vs. arquitetura-alvo

### Estado atual herdado

* pipeline transacional principal
* segregação básica por tenant
* auditoria operacional
* observabilidade inicial
* integração RAG funcional
* políticas e guardrails
* documentação da fundação operacional

### Arquitetura-alvo desta fase

* experiment tracking com MLflow
* versionamento formal de artefatos de IA
* benchmark reproduzível por tenant
* avaliação formal de RAG
* retrieval híbrido com comparação controlada
* orquestração offline com Airflow
* monitoramento de deriva semântica
* observabilidade ampliada de qualidade, custo e latência
* governança e explicabilidade técnica ampliadas

## Relação com o planejamento

A execução desta arquitetura-alvo está organizada em fases no documento:

* `PLANEJAMENTO-LLMOps.md`

A ordem de implantação deve respeitar o princípio de fundação antes de otimização:

1. preparar ambiente e tracking;
2. versionar artefatos;
3. criar benchmark;
4. medir qualidade;
5. evoluir retrieval;
6. ampliar observabilidade;
7. automatizar validação;
8. introduzir orquestração offline;
9. consolidar deriva, governança e demonstração.

## Critério de consistência arquitetural

A arquitetura da fase será considerada consistente quando:

* os novos componentes estiverem posicionados sem violar a separação entre operação e experimento;
* a segregação por tenant estiver preservada em todas as camadas;
* benchmark, tracking e observabilidade puderem ser correlacionados;
* a evolução do pipeline de IA estiver sustentada por versionamento e medição;
* a documentação distinguir claramente o que está ativo do que está planejado.

## Status

Arquitetura-alvo formalizada para início da fase.

Base herdada preservada.
Novas camadas definidas conceitualmente.
Próximo passo: iniciar execução da Fase 1 conforme `PLANEJAMENTO-LLMOps.md`.

````

