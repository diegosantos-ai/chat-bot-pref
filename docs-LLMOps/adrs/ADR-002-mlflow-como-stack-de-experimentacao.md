# ADR-002 — MLflow como Stack de Experimentação

## Status
Aceito

## Contexto

A Fase 1 do Chat Pref introduz uma camada formal de LLMOps, com foco em rastreabilidade experimental, benchmark reproduzível, avaliação formal de RAG e comparação entre versões de artefatos de IA.

Para sustentar essa evolução, o projeto precisa de uma stack de experimentação capaz de:

- registrar execuções técnicas comparáveis;
- armazenar parâmetros, métricas e artifacts;
- correlacionar resultados a versões de prompt, retrieval, embeddings e datasets;
- permitir leitura por tenant;
- suportar comparação entre estratégias de retrieval, modelos e políticas;
- servir como base para avaliação formal e regressão.

A adoção dessa stack precisa respeitar a natureza do projeto:
- arquitetura tenant-aware;
- separação entre auditoria operacional e experiment tracking;
- necessidade de documentação clara e demonstrável;
- prioridade por soluções com boa aderência a engenharia aplicada e governança.

## Decisão

O projeto adota **MLflow** como stack principal de experimentação da Fase 1.

MLflow será utilizado como camada responsável por registrar e organizar:

- `experiments`
- `runs`
- `params`
- `metrics`
- `artifacts`
- metadados de versão relevantes para o ciclo de IA

## Justificativa

A escolha por MLflow foi feita pelos seguintes motivos:

1. **aderência ao problema**
   O projeto precisa de uma trilha formal de experimentação, e não apenas de logging enriquecido. MLflow cobre exatamente esse espaço de comparação estruturada.

2. **modelo mental compatível com engenharia experimental**
   A noção de experimento, run, parâmetro, métrica e artifact é adequada para o tipo de evolução que a Fase 1 pretende sustentar.

3. **boa integração com avaliação formal**
   O uso de benchmark, avaliação de RAG e comparação entre versões se beneficia diretamente da organização de runs e artifacts.

4. **neutralidade em relação ao pipeline**
   MLflow pode ser integrado sem exigir reescrita do runtime transacional principal.

5. **boa capacidade de demonstração**
   Para fins de documentação, explicação técnica e processo seletivo, MLflow oferece uma trilha mais clara e defensável do que soluções improvisadas em logs ou tabelas ad hoc.

## Papel do MLflow na arquitetura

MLflow passa a ocupar a camada de **Experiment Tracking** da arquitetura da Fase 1.

Seu papel será:
- registrar execuções experimentais;
- consolidar métricas comparáveis;
- armazenar artifacts de benchmark e avaliação;
- servir como base para análise de regressão;
- suportar comparação entre versões de prompts, retrieval e modelos.

MLflow **não substitui**:
- a auditoria operacional;
- a observabilidade da aplicação;
- a persistência funcional do atendimento.

## Escopo de uso

Na Fase 1, MLflow será usado para registrar, quando aplicável:

- `tenant_id`
- `experiment_name`
- `run_id`
- `prompt_version`
- `policy_version`
- `retriever_version`
- `embedding_version`
- `dataset_version`
- `vectorstore_version`
- `model_provider`
- `model_name`
- parâmetros de retrieval
- métricas de benchmark
- métricas de qualidade
- latência
- custo estimado
- artifacts comparativos

## Regras de adoção

A adoção de MLflow no projeto deve seguir estas regras:

### 1. Segregação por tenant
Toda execução experimental precisa ser filtrável e interpretável por tenant.

### 2. Correlação com o operacional
Sempre que aplicável, runs experimentais devem ser correlacionáveis com `request_id` e contexto operacional, sem fundir tracking com auditoria.

### 3. Versionamento explícito
Nenhuma métrica experimental relevante deve existir sem vínculo a versão de prompt, retrieval, dataset ou configuração associada.

### 4. Uso controlado
MLflow não deve ser transformado em repositório genérico de qualquer telemetria. Seu uso deve permanecer focado em experimentação técnica e comparação estruturada.

## Alternativas consideradas

### 1. Usar apenas logs estruturados
Rejeitada.

Motivo:
- não oferece organização natural para benchmark, comparação entre runs e artifacts;
- aumenta esforço de leitura e governança;
- enfraquece a camada formal de experimentação.

### 2. Usar apenas tabelas em PostgreSQL
Rejeitada.

Motivo:
- exigiria modelagem adicional para reproduzir funcionalidades típicas de tracking experimental;
- tende a gerar solução mais manual e menos expressiva para comparação entre execuções.

### 3. Adotar W&B ou ferramenta equivalente
Não adotada nesta fase.

Motivo:
- embora tecnicamente viável, MLflow apresenta melhor encaixe inicial com o objetivo de manter uma stack mais direta, controlável e aderente ao estilo de engenharia do projeto.

### 4. Adotar MLflow
Aceita.

Motivo:
- melhor equilíbrio entre rastreabilidade experimental, clareza arquitetural e custo de adoção.

## Consequências

### Positivas
- trilha formal de experimentação;
- comparação clara entre versões e estratégias;
- suporte sólido para benchmark e avaliação de RAG;
- melhor base para regressão e explicação técnica;
- documentação mais forte da camada LLMOps.

### Negativas / trade-offs
- aumento da disciplina exigida para registrar parâmetros e versões corretamente;
- necessidade de definir convenções de naming e metadados;
- necessidade de evitar uso excessivamente genérico da ferramenta.

## Impacto na implementação

A adoção de MLflow implica:

- introdução de uma camada própria de tracking experimental;
- definição de contratos mínimos de `runs`, `params`, `metrics` e `artifacts`;
- integração com benchmark e avaliação formal;
- integração futura com CI de GenAI para dry-runs e regressão;
- padronização de metadados por tenant e por versão.

## Impacto na documentação

A partir desta decisão:
- a arquitetura deve tratar MLflow como componente da camada experimental;
- o planejamento deve explicitar onde a instrumentação de MLflow entra;
- os runbooks devem documentar instalação, uso e validação mínima da stack;
- novas ADRs podem complementar esta decisão com convenções operacionais mais específicas.

## Relação com outras decisões

Esta ADR depende diretamente da separação entre auditoria operacional e experiment tracking definida em:

- `ADR-001 — Separação entre Auditoria Operacional e Experiment Tracking`

## Referências internas
- `docs-LLMOps/CONTEXTO-LLMOps.md`
- `docs-LLMOps/ARQUITETURA-LLMOps.md`
- `docs-LLMOps/PLANEJAMENTO-LLMOps.md`
- `docs-LLMOps/adrs/ADR-001-separacao-auditoria-vs-tracking.md`
