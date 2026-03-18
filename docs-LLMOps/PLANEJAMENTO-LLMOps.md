# Fase 1 — GenAI com Método: LLMOps, Avaliação e Governança

## Contexto

Após a consolidação da **Fase 0 — Fundação Operacional do Chat Pref**, o projeto passa a entrar em uma nova etapa de desenvolvimento orientada à maturidade técnica da plataforma de IA.

A fase anterior estabeleceu a base funcional do sistema: arquitetura backend, pipeline principal de atendimento, integração com RAG, guardrails, auditoria, observabilidade inicial, segregação multi-tenant e estrutura mínima de deploy. Essa fundação permitiu validar o funcionamento do produto, a coerência da arquitetura e a viabilidade do projeto como solução aplicada ao contexto público.

A partir deste ponto, o objetivo deixa de ser apenas manter uma aplicação funcional e passa a ser elevar o projeto ao nível de uma **plataforma de IA rastreável, avaliável, governável e demonstrável sob critérios de engenharia**.

## Objetivo da nova fase

Esta fase tem como objetivo estruturar a camada de **LLMOps, avaliação formal, governança e observabilidade avançada** do Chat Pref, transformando a base já existente em uma solução capaz de sustentar:

- rastreabilidade experimental por tenant;
- versionamento formal de prompts, policies e configuração de RAG;
- avaliação reproduzível da qualidade do pipeline;
- comparação controlada entre estratégias de retrieval e provedores LLM;
- observabilidade de qualidade, latência e custo;
- detecção de degradação semântica da base vetorial;
- orquestração offline para ingestão, avaliação e reindexação;
- documentação técnica consistente para demonstração e defesa arquitetural.

## Diretriz central

A diretriz desta fase é consolidar o princípio de **GenAI com método**, substituindo evolução baseada em percepção isolada por evolução baseada em:

- experimento rastreável;
- benchmark reproduzível;
- comparação entre versões;
- evidência técnica;
- segregação segura por tenant;
- governança explícita de artefatos e decisões.

## Escopo

O escopo desta fase não se limita à implementação de novas funcionalidades. Ele inclui também a preparação formal do ambiente, a estruturação de dependências, a definição de contratos técnicos, a criação de critérios de aceite por etapa e a consolidação de trilhas de evidência que permitam avaliar, explicar e demonstrar o sistema com rigor.

## Resultado esperado ao final da fase

Ao final desta etapa, o Chat Pref deverá estar posicionado não apenas como um sistema funcional de atendimento com IA, mas como uma **plataforma de IA com maturidade técnica mensurável**, apta a ser apresentada, defendida e evoluída com base em princípios de reprodutibilidade, governança e observabilidade.


## Card Macro — Fase 1 — Fundação de LLMOps e Rastreabilidade Experimental

### Objetivo da fase

Estabelecer a base de Lastreabilidade Experimental e LLMOps do projeto, com segregação por tenant, contrato explícito entre auditoria operacional e tracking experimental, além da preparação formal do ambiente base e do ambiente de desenvolvimento necessários para as fases subsequentes de avaliação, observabilidade e testes.

### Resultado esperado

Projeto com ambiente técnico preparado para evolução da camada de LLMOps, contendo as dependências essenciais do backend e do ecossistema de experimentação devidamente versionadas, instaladas e validadas, com diretrizes claras de rastreabilidade por tenant.

### Critério de aceite

* arquivos `requirements.txt` e `requirements-dev.txt` definidos, versionados e revisados
* instalação do ambiente base executada com sucesso
* instalação do ambiente de desenvolvimento executada com sucesso
* estratégia de uso do MLflow definida e documentada
* segregação por `tenant_id` prevista no tracking experimental
* distinção explícita entre auditoria operacional e experimento técnico formalizada
* estrutura mínima de `runs`, `params`, `metrics` e `artifacts` definida
* contratos de versionamento para prompt, retriever e embeddings estabelecidos

### Riscos

* sobreposição indevida entre auditoria de atendimento e rastreamento experimental
* registro de execuções sem contexto suficiente para comparação
* ausência de isolamento por tenant no tracking
* instalação de dependências fora da fase planejada
* evolução de avaliação e tracking sobre ambiente não padronizado

### Dependências

* arquitetura atual estabilizada
* fluxo principal do pipeline compreendido

### Observações

Esta fase deixa de ser apenas conceitual e passa a incorporar a preparação formal do ambiente, reduzindo risco de acoplamento indevido, improviso de setup e divergência entre execução local, testes e experimentação.

#### Tasks — Fase 1 - (CONCLUIDA)

* `CPPX-F1-T1 — Definir estratégia de adoção do MLflow no projeto`
* `CPPX-F1-T2 — Definir modelo de segregação experimental por tenant_id`
* `CPPX-F1-T3 — Formalizar a separação entre auditoria operacional e tracking experimental`
* `CPPX-F1-T4 — Definir contrato mínimo de run, params, metrics e artifacts`
* `CPPX-F1-T5 — Definir versionamento inicial de prompt, retriever e embeddings`
* `CPPX-F1-T6 — Mapear pontos de instrumentação em app/audit e app/rag`
* `CPPX-F1-T7 — Consolidar arquitetura alvo de LLMOps tenant-aware`
* `CPPX-F1-T8 — Criar e versionar o novo requirements.txt`
* `CPPX-F1-T9 — Criar e versionar o requirements-dev.txt`
* `CPPX-F1-T10 — Instalar o ambiente base com requirements.txt`
* `CPPX-F1-T11 — Instalar o ambiente de desenvolvimento com requirements-dev.txt`
* `CPPX-F1-T12 — Validar importação, compatibilidade mínima e consistência das dependências instaladas`

---

## Card Macro — Fase 2 — Versionamento de Prompts, Policies e Configuração de RAG (CONCLUIDO)

### Objetivo da fase

Transformar prompts, guardrails e configurações de retrieval em artefatos versionados, comparáveis e promovíveis com controle explícito, operando sobre o ambiente de desenvolvimento previamente preparado na Fase 1.

### Resultado esperado

Mudanças em prompt, policy e parâmetros de RAG registradas de forma rastreável, com histórico claro, metadados mínimos e base consistente para regressão e comparação entre versões.

### Critério de aceite

* prompts base, fallback e guardrails versionados
* policies textuais com versionamento explícito
* configuração de chunking, `top_k` e retrieval versionada
* alteração de artefatos gera identificador único comparável
* convenção de promoção entre versões definida
* execução da fase realizada sobre ambiente previamente instalado e validado na Fase 1

### Riscos

* versionamento informal ou implícito de prompts
* alteração de retrieval sem evidência comparativa
* acoplamento excessivo entre policy e lógica de aplicação
* impossibilidade de reconstruir qual versão produziu determinada resposta

### Dependências

* fase 1 concluída
* estrutura de tracking definida

### Observações

Nenhuma instalação nova deve ocorrer nesta fase. O foco é governança de artefatos, não expansão do ambiente.

#### Tasks — Fase 2

* `CPPX-F2-T1 — Definir estrutura de versionamento de prompts`
* `CPPX-F2-T2 — Definir estrutura de versionamento de guardrails e policies`
* `CPPX-F2-T3 — Versionar configuração de retrieval e chunking`
* `CPPX-F2-T4 — Criar identificadores consistentes de versão experimental`
* `CPPX-F2-T5 — Definir metadados obrigatórios por versão`
* `CPPX-F2-T6 — Integrar versões ao tracking experimental`
* `CPPX-F2-T7 — Documentar política de promoção e rollback de versões`

---

## Card Macro — Fase 3 — Dataset de Avaliação e Benchmark Reproduzível (CONSOLIDADA NESTE ESCOPO)

### Objetivo da fase

Construir um conjunto de avaliação controlado para medir a qualidade do sistema de forma reproduzível, comparável e orientada por tenant, utilizando o ambiente de desenvolvimento preparado na Fase 1.

### Resultado esperado

Benchmark inicial estruturado com perguntas, respostas de referência, contexto esperado e classificação por cenário de uso, suportando execução recorrente e comparação entre versões.

### Critério de aceite

* dataset inicial definido e estruturado
* casos organizados por tenant e tipo de pergunta
* cenários normais, ambíguos, fora de escopo e baixa confiança cobertos
* referência mínima de resposta e contexto documentada
* benchmark utilizável em execução repetida
* ambiente de desenvolvimento da Fase 1 confirmado como base da fase

### Riscos

* benchmark insuficiente para detectar regressões
* viés por excesso de casos simples
* mistura indevida de tenants em um mesmo conjunto
* ausência de referência mínima para comparação confiável

### Dependências

* fase 2 concluída
* escopo institucional do tenant demonstrativo conhecido

### Observações

Nenhuma instalação nova deve ocorrer nesta fase. O foco é a qualidade metodológica do dataset.

#### Tasks — Fase 3

* `CPPX-F3-T1 — Definir estrutura do dataset de benchmark`
* `CPPX-F3-T2 — Selecionar cenários prioritários por tenant`
* `CPPX-F3-T3 — Criar casos normais de atendimento institucional`
* `CPPX-F3-T4 — Criar casos fora de escopo e baixa confiança`
* `CPPX-F3-T5 — Criar casos de risco e bloqueio por policy`
* `CPPX-F3-T6 — Definir referência mínima de resposta e contexto esperado`
* `CPPX-F3-T7 — Consolidar benchmark reproduzível inicial`

---

## Card Macro — Fase 4 — Avaliação Formal de RAG com Métricas de Qualidade

### Objetivo da fase

Implementar avaliação formal do pipeline RAG com métricas técnicas e comparações entre versões de base vetorial, prompts e estratégias de retrieval, utilizando as dependências de avaliação já instaladas no ambiente de desenvolvimento desde a Fase 1.

### Resultado esperado

Sistema capaz de medir a qualidade do RAG de forma estruturada, com relatórios comparáveis entre execuções, sem dependência de setup paralelo fora do planejamento.

### Critério de aceite

* avaliação com Ragas ou equivalente integrada
* métricas de `faithfulness` e `answer_relevance` registradas
* métricas complementares de contexto e recuperação definidas
* execuções comparáveis entre versões de configuração
* resultados persistidos como `artifacts` de experimento
* dependências de avaliação disponíveis e funcionais no ambiente preparado na Fase 1

### Riscos

* avaliação sem benchmark minimamente confiável
* interpretação excessiva de nota agregada sem análise de casos críticos
* comparação entre runs com configuração mal registrada
* uso de métrica sem entendimento do seu alcance e limitação

### Dependências

* fases 1, 2 e 3 concluídas

### Observações

Nenhuma instalação nova deve ocorrer nesta fase. Bibliotecas de avaliação devem já ter sido incorporadas ao ambiente dev.

#### Tasks — Fase 4

* `CPPX-F4-T1 — Definir stack de avaliação formal do RAG`
* `CPPX-F4-T2 — Integrar execução de avaliação ao pipeline experimental`
* `CPPX-F4-T3 — Registrar faithfulness e answer_relevance por run`
* `CPPX-F4-T4 — Definir métricas complementares de contexto e recuperação`
* `CPPX-F4-T5 — Gerar artifacts comparativos por experimento`
* `CPPX-F4-T6 — Revisar casos com pior desempenho e causas prováveis`
* `CPPX-F4-T7 — Consolidar baseline inicial de qualidade do RAG`

---

## Card Macro — Fase 5 — Retrieval Híbrido, Query Rewriting e Reranking

### Objetivo da fase

Evoluir a camada de recuperação para técnicas avançadas de RAG, reduzindo ruído, melhorando relevância e aproximando o projeto do estado da arte requerido, apoiando-se na base de experimentação e avaliação já preparada nas fases anteriores.

### Resultado esperado

Pipeline de retrieval operando com estratégias comparáveis de busca semântica, busca lexical, query rewriting e reranking, com resultados mensuráveis e rastreáveis.

### Critério de aceite

* estratégia híbrida semântica + lexical definida
* query rewriting ou query expansion controlado e mensurável
* reranking integrado ao pipeline de recuperação
* comparação entre estratégias executada com benchmark
* melhoria ou trade-off documentado com evidência
* execução da fase realizada sobre ambiente previamente preparado nas fases anteriores

### Riscos

* aumento de complexidade sem ganho comprovado
* degradação de latência por reranking sem benefício proporcional
* distorção de intenção por rewriting mal calibrado
* multiplicidade de estratégias sem controle experimental adequado

### Dependências

* fase 4 concluída
* benchmark funcional

### Observações

Nenhuma instalação nova deve ocorrer nesta fase. Toda evolução deve ser guiada por benchmark e tracking.

#### Tasks — Fase 5

* `CPPX-F5-T1 — Definir arquitetura alvo de retrieval híbrido`
* `CPPX-F5-T2 — Implementar camada lexical complementar`
* `CPPX-F5-T3 — Implementar query rewriting ou expansion controlado`
* `CPPX-F5-T4 — Integrar reranker ao pipeline de recuperação`
* `CPPX-F5-T5 — Expor parâmetros experimentais de retrieval avançado`
* `CPPX-F5-T6 — Executar comparação entre estratégias`
* `CPPX-F5-T7 — Consolidar baseline vencedora ou matriz de trade-offs`

### Fechamento estrutural atual do bloco

Na branch `feat/fase5-retrieval-query-reranking`, este planejamento passa a ter o seguinte recorte fechado:

- `CPPX-F5-T1` documentado em `docs-LLMOps/fases/FASE5-RETRIEVAL-HIBRIDO.md`;
- `CPPX-F5-T2` implementado com camada lexical complementar real por full scan da collection do tenant;
- `CPPX-F5-T3` implementado com query expansion heurística opt-in baseada em metadados `keywords` do tenant;
- `CPPX-F5-T4` implementado com reranking heurístico pós-recuperação, opt-in e rastreável;
- `CPPX-F5-T5` implementado com consolidação da superfície experimental da fase em contrato único por eixo, compartilhado entre runtime, benchmark offline, tracking e CLI;
- `CPPX-F5-T6` implementado com execução comparativa reproduzível entre cinco combinações da Fase 5, registradas em tracking experimental e consolidadas em sumário objetivo;
- baseline anterior do retrieval explicitado e mantido como variante comparável;
- tracking e benchmark passam a distinguir a execução por `retrieval_strategy_name`, `query_transform_strategy_name`, `rerank_strategy_name` e pela matriz `phase5_experiment_axes`;
- `CPPX-F5-T7` consolidado com promoção de `semantic_plus_full_collection_lexical_candidates_v1` sem query transformation e sem reranking como baseline recomendada do recorte atual;
- query expansion heurística e reranking heurístico permanecem experimentais, sem promoção para default;
- a decisão continua restrita ao recorte atual do benchmark offline do tenant demonstrativo e não deve ser lida como vencedor absoluto fora desse contexto.

---

## Card Macro — Fase 6 — Observabilidade de Qualidade, Latência e Custo por Tenant

### Objetivo da fase

Expandir a observabilidade atual para incluir métricas de qualidade, custo e desempenho do pipeline de IA com recorte por tenant e por etapa, utilizando a base de instrumentação instalada desde a preparação inicial do ambiente.

### Resultado esperado

Painel técnico mínimo e trilha operacional capazes de responder custo, latência e qualidade por configuração e por tenant, sobre ambiente já preparado com OpenTelemetry e instrumentação de serviços.

### Critério de aceite

* métricas por tenant definidas
* latência por estágio do pipeline observável
* custo estimado por requisição registrado
* indicadores de fallback, bloqueio e retrieval vazio expostos
* correlação entre tracing operacional e tracking experimental estabelecida
* instrumentação necessária presente e funcional no ambiente preparado na Fase 1

### Riscos

* excesso de métricas sem utilidade decisória
* custo estimado sem metodologia consistente
* latência agregada mascarando gargalos por etapa
* dashboards com baixo valor operacional

### Dependências

* fases 1 e 4 concluídas
* observabilidade básica existente estabilizada

### Observações

Nenhuma instalação nova deve ocorrer nesta fase. O foco é enriquecer a observabilidade sobre base já provisionada.

#### Tasks — Fase 6

* `CPPX-F6-T1 — Definir métricas de qualidade, custo e latência por tenant`
* `CPPX-F6-T2 — Instrumentar latência por estágio do pipeline`
* `CPPX-F6-T3 — Registrar custo estimado de chamadas LLM e retrieval`
* `CPPX-F6-T4 — Expor métricas de fallback, bloqueio e retrieval vazio`
* `CPPX-F6-T5 — Correlacionar traces operacionais com runs experimentais`
* `CPPX-F6-T6 — Consolidar visão mínima em dashboard técnico`
* `CPPX-F6-T7 — Documentar leitura operacional das métricas`

Detalhamento do bloco inicial desta fase:

- `docs-LLMOps/fases/FASE6-OBSERVABILIDADE-QUALIDADE-LATENCIA-CUSTO.md` (contrato minimo de metricas, dimensoes e pontos candidatos de instrumentacao para `CPPX-F6-T1`).

---

## Card Macro — Fase 7 — CI de GenAI com Regressão de Prompt e Dry-Run Experimental (CONCLUÍDA)

### Objetivo da fase

Expandir o CI atual para validar mudanças de prompt, retrieval e policy com regressão automatizada e registro experimental controlado, utilizando o ambiente de desenvolvimento já preparado e validado nas fases iniciais.

### Resultado esperado

Pipeline de CI apta a bloquear regressões de comportamento, rastreabilidade e qualidade em mudanças de IA, sem depender de instalações manuais fora do fluxo formal de projeto.

### Critério de aceite

* workflow de GenAI CI criado
* regressão de prompt ou policy automatizada
* benchmark reduzido executado no pipeline
* dry-run experimental registrado
* falhas relevantes bloqueiam merge ou promoção
* dependências de teste, tracking e avaliação previamente instaladas e reconhecidas como base da fase

### Riscos

* pipeline excessivamente lenta para uso recorrente
* benchmark reduzido insuficiente para proteger regressões
* registro experimental sem contexto mínimo
* gates frágeis que não capturam quebra real

### Dependências

* fases 2, 3 e 4 concluídas
* CI básica existente funcional

### Observações

Nenhuma instalação nova deve ocorrer aqui no backend Python. Tooling externo de CI deve ser tratado como dependência específica da fase, com documentação própria.

#### Tasks — Fase 7

* `CPPX-F7-T1 — Definir escopo mínimo do CI específico de GenAI`
* `CPPX-F7-T2 — Integrar regressão de prompt e policy ao pipeline`
* `CPPX-F7-T3 — Executar benchmark reduzido em pull request`
* `CPPX-F7-T4 — Registrar dry-run experimental no tracking`
* `CPPX-F7-T5 — Definir critérios de bloqueio por qualidade e rastreabilidade`
* `CPPX-F7-T6 — Validar execução com provider mock e cenário controlado`
* `CPPX-F7-T7 — Documentar política de aprovação de mudanças em IA`

### Fechamento estrutural atual do bloco

Na branch `feat/ci-genai-regressao`, este planejamento passa a ter o seguinte recorte fechado:

- `CPPX-F7-T1` a `CPPX-F7-T7` foram implementadas configurando um job dedicado (`genai-dry-run`) no repositório;
- a execução aproveitou a camada offline mockada em conjunto com limite explícito de execuções (`--max-cases 3`) para validar comportamentos estáticos e estruturais de MLflow/Ragas operando em CI;
- o rastreamento foi isolado no artefato `mlflow.db` acoplado ao Github Actions (`genai-ci-mlflow-tracking`), consolidando a política de separação formal entre auditoria operacional e fluxo experimental;
- a documentação metodológica foi gerada em `docs-LLMOps/fases/FASE7-CI-GENAI-REGRESSAO.md` delimitando de forma transparente que métricas semânticas acuradas e provedores LLM online continuam fora de escopo deste CI rápido (mantendo-se o mock para avaliação de integridade).

---

## Card Macro — Fase 8 — Orquestração Offline com Airflow

### Objetivo da fase

Introduzir orquestração formal para ingest, reindexação, avaliação e tarefas recorrentes do ecossistema RAG, incluindo a preparação do ambiente isolado de Airflow e a instalação controlada das dependências de orquestração.

### Resultado esperado (Entregue)

Processos offline e mapeamento de DAGs prioritárias entregues de forma organizada, com ambiente dedicado de Airflow (Python 3.13 e Airflow 2.11.2) isolado do runtime transacional.

### Fora do escopo entregue nesta etapa

* execução de processos recorrentes e agendamento robusto sistêmico operando ativamente em produção; as execuções de prova permaneceram em testes controlados guiados.

### Critério de aceite

* arquivo `requirements-airflow.txt` definido e versionado
* ambiente dedicado de Airflow instalado com sucesso
* escopo de DAGs prioritárias definido
* ingest, reindexação e avaliação com jobs identificáveis
* execução desacoplada do runtime transacional
* parâmetros por tenant previstos
* evidência mínima de execução orquestrada registrada

### Riscos

* introdução prematura de Airflow com baixo retorno
* instalação de Airflow no ambiente principal do backend
* DAGs replicando scripts mal estruturados
* mistura entre processo offline e fluxo transacional online
* sobrecarga operacional desnecessária

### Dependências

* fases 3, 4 e 5 concluídas

### Observações

Airflow deve ser tratado como ambiente separado e como ativo operacional da fase, não como extensão informal do runtime principal.

#### Tasks — Fase 8

* `CPPX-F8-T1 — Definir escopo mínimo de orquestração offline`
* `CPPX-F8-T2 — Criar e versionar o requirements-airflow.txt`
* `CPPX-F8-T3 — Preparar ambiente dedicado para Airflow`
* `CPPX-F8-T4 — Instalar dependências de orquestração com requirements-airflow.txt`
* `CPPX-F8-T5 — Validar importação e compatibilidade mínima do ambiente Airflow`
* `CPPX-F8-T6 — Modelar DAG de ingest por tenant`
* `CPPX-F8-T7 — Modelar DAG de avaliação offline`
* `CPPX-F8-T8 — Modelar DAG de reindexação controlada`
* `CPPX-F8-T9 — Definir parâmetros e contratos por tenant`
* `CPPX-F8-T10 — Validar execução mínima das DAGs prioritárias`
* `CPPX-F8-T11 — Documentar fronteira entre runtime online e jobs offline`

---

## Card Macro — Fase 9 — Deriva Semântica e Saúde da Base Vetorial

### Objetivo da fase

Criar mecanismos para detectar degradação da qualidade semântica da base documental e distinguir problemas de base, retrieval ou modelo, operando sobre os ambientes já preparados para avaliação e, quando aplicável, para orquestração offline.

### Resultado esperado (Entregue)

Fundação diagnóstica do ecossistema formalizado. Criada matriz de diagnóstico, limites matemáticos configurados e estabelecido o protocolo de comparação vetorial para isolar a natureza do erro. Não implementou-se reavaliação 100% autônoma ou on-the-fly request.

### Fora do escopo entregue nesta etapa

* persistência sistêmica unificada do repositório de snapshots e a execução acoplada end-to-end com automação absoluta permanecem no roadmap.

### Critério de aceite

* indicadores de saúde da base vetorial definidos
* comparação entre versões de base registrada
* queda de relevância detectável por benchmark
* sinais operacionais de degradação mapeados
* hipótese de causa provável documentável por tenant
* quando houver rotina agendada, uso do ambiente Airflow preparado na Fase 8 documentado

### Riscos

* confusão entre degradação de base e problema de prompt
* dependência excessiva de percepção subjetiva para detectar queda
* comparação entre bases sem versionamento adequado
* excesso de alerta com baixo poder diagnóstico

### Dependências

* fases 4, 5 e 6 concluídas

### Observações

Nenhuma nova instalação deve ser introduzida nesta fase. Qualquer lacuna de ambiente aqui aponta falha de preparação em fase anterior.

#### Tasks — Fase 9

* `CPPX-F9-T1 — Definir indicadores de saúde semântica da base`
* `CPPX-F9-T2 — Versionar bases vetoriais e configurações de ingest`
* `CPPX-F9-T3 — Comparar desempenho entre versões de base`
* `CPPX-F9-T4 — Mapear sinais operacionais de degradação semântica`
* `CPPX-F9-T5 — Relacionar sintomas a causas prováveis por tenant`
* `CPPX-F9-T6 — Definir rotina mínima de reavaliação da base`
* `CPPX-F9-T7 — Consolidar narrativa técnica de deriva semântica`

---

## Card Macro — Fase 10 — Multi-LLM, Fallback e Avaliação Comparativa de Provedores

### Objetivo da fase

Expandir a camada de provedor LLM para comparação entre modelos, fallback controlado e decisão orientada por custo, latência e qualidade, sobre a base de experimentação já instalada e validada anteriormente.

### Resultado esperado

Projeto apto a comparar modelos e justificar escolha de provedor com evidência técnica, sem dependência de setup adicional fora do plano.

### Critério de aceite

* contrato multi-LLM definido
* fallback controlado entre modelos previsto
* comparação por custo, latência e qualidade executável
* resultados comparativos registrados no tracking
* critério de escolha de modelo documentado
* uso do ambiente dev preparado na Fase 1 confirmado como base da fase

### Riscos

* abstração excessivamente genérica e pouco aplicável
* comparação entre modelos sem benchmark consistente
* fallback mascarando problema estrutural do pipeline
* escolha de modelo baseada apenas em efeito de demonstração

### Dependências

* fases 4 e 6 concluídas

### Observações

Nenhuma instalação nova obrigatória deve ocorrer nesta fase.

#### Tasks — Fase 10 - (CONCLUÍDA)

* `[x] CPPX-F10-T1 — Definir contrato de multi-LLM e fallback`
* `[x] CPPX-F10-T2 — Integrar segundo provedor ou modo comparável`
* `[x] CPPX-F10-T3 — Expor parâmetros experimentais por modelo`
* `[x] CPPX-F10-T4 — Executar comparação de qualidade, custo e latência`
* `[x] CPPX-F10-T5 — Registrar fallback e motivo de acionamento`
* `[x] CPPX-F10-T6 — Consolidar recomendação técnica de escolha de modelo`

---

## Card Macro — Fase 11 — Governança, Explicabilidade e Evidência de Decisão

### Objetivo da fase

Consolidar a camada de governança do sistema, ampliando explicabilidade, rastreabilidade de decisão e transparência entre resposta, contexto e policy, sobre a base técnica já preparada e validada nas fases anteriores.

### Resultado esperado

Sistema demonstrável com trilha clara de como uma resposta foi gerada, bloqueada, limitada ou desviada, sem depender de instalação adicional fora do planejamento.

### Critério de aceite

* motivo de bloqueio ou fallback documentável
* versão de prompt e policy visível na trilha técnica
* contexto recuperado rastreável por resposta
* evidência de decisão disponível por request e por tenant
* separação entre trilha operacional e experimental preservada
* execução da fase realizada sobre ambientes já preparados e validados anteriormente

### Riscos

* explicabilidade apenas cosmética, sem lastro técnico
* excesso de detalhe comprometendo legibilidade
* divergência entre resposta e evidência registrada
* promessa de governança acima da capacidade real do sistema

### Dependências

* fases 1, 2, 4 e 6 concluídas

### Observações

Nenhuma instalação nova deve ocorrer nesta fase. Explicabilidade deve permanecer como trilha de engenharia verificável.

#### Tasks — Fase 11

* `[x] CPPX-F11-T1 — Definir estrutura de evidência de decisão por request`
* `[x] CPPX-F11-T2 — Expor versão de prompt, policy e retrieval por resposta`
* `[x] CPPX-F11-T3 — Consolidar reason_codes e trilha de bloqueio ou fallback`
* `[x] CPPX-F11-T4 — Correlacionar contexto recuperado e resposta produzida`
* `[x] CPPX-F11-T5 — Revisar clareza da explicabilidade para demonstração`
* `[x] CPPX-F11-T6 — Documentar fronteira entre evidência operacional e experimental`

---

## Card Macro — Fase 12 — Alinhamento Final com a Vaga e Material de Demonstração

### Objetivo da fase

Consolidar tudo o que foi implementado em narrativa técnica, evidência objetiva e roteiro de demonstração alinhados aos requisitos da vaga, operando sobre ambientes já preparados e estabilizados ao longo do plano.

### Resultado esperado

Projeto pronto para entrevista, demonstração técnica e defesa de arquitetura, com aderência integral aos itens anteriormente classificados como parcial ou gap e sem dependência de setup improvisado na etapa final.

### Critério de aceite

* matriz `requisito -> implementação -> evidência` consolidada
* roteiro de demonstração pronto
* arquitetura atualizada refletindo o estado real da solução
* README e documentação principal atualizados
* narrativa de trade-offs e decisões técnicas preparada
* checklist final de aderência integral concluído
* confirmação de que todas as fases foram executadas sobre os ambientes previstos no planejamento

### Riscos

* documentação prometendo mais do que o sistema entrega
* evidência técnica dispersa
* demonstração dependente de improviso
* discurso forte com baixa sustentação prática

### Dependências

* fases 1 a 11 concluídas ou estabilizadas

### Observações

Esta fase consolida o material de defesa técnica. Sem ela, a solução pode estar forte do ponto de vista de implementação, mas fraca em comunicação técnica e apresentação executiva.

#### Tasks — Fase 12

* `CPPX-F12-T1 — Consolidar matriz requisito da vaga versus evidência do projeto`
* `CPPX-F12-T2 — Atualizar arquitetura final com camada de LLMOps`
* `CPPX-F12-T3 — Atualizar README e documentação principal`
* `CPPX-F12-T4 — Preparar roteiro de demonstração técnica`
* `CPPX-F12-T5 — Consolidar resultados comparativos de experimentos`
* `CPPX-F12-T6 — Organizar artefatos de portfólio e entrevista`
* `CPPX-F12-T7 — Revisar aderência final aos gaps da vaga`

---

## Regra estrutural — Preparação de ambiente por fase

### Instalações permitidas por fase

* **Fase 1:** `requirements.txt` e `requirements-dev.txt`
* **Fase 8:** `requirements-airflow.txt`

### Instalações não previstas fora dessas fases

Qualquer nova dependência identificada fora dessas fases deve ser tratada como:

* ajuste formal do planejamento, ou
* exceção técnica registrada em card próprio, com justificativa e impacto documentados.

---

## Modelo de Descrição — Card de Task

```markdown
## Objetivo
[descrever a ação concreta da task]

## Arquivos / áreas afetadas
- [arquivo 1]
- [arquivo 2]

## Passo operacional
1. [passo 1]
2. [passo 2]
3. [passo 3]

## Validação
- [comando / evidência 1]
- [comando / evidência 2]

## Critério de conclusão
- [critério 1]
- [critério 2]

## Riscos
- [risco 1]
- [risco 2]

## Fechamento
- [ ] alteração realizada
- [ ] validação executada
- [ ] evidência registrada
- [ ] card movido corretamente
```

---

## Modelo de Comentário — Encerramento de Sessão

```markdown
Sessão encerrada.

Foi executado: [resumo curto].
Validação realizada: [resumo].
Status atual: [estado].
Próximo passo: [ação objetiva].
Branch atual: [nome da branch].
```
