# operacao-airflow

## Objetivo

Este runbook descreve os princípios e o procedimento mínimo para preparação, validação e operação da camada de orquestração offline da Fase 1 do Chat Pref.

Seu objetivo é formalizar o uso do Airflow como componente responsável por jobs recorrentes e desacoplados do runtime transacional, preservando a separação entre atendimento online, experimentação técnica e processamento offline.

## Escopo

Este documento cobre:

- finalidade operacional do Airflow na fase LLMOps;
- preparação do ambiente dedicado;
- regras mínimas de uso;
- tipos de job previstos;
- validação mínima da camada offline;
- limites arquiteturais da orquestração.

Este runbook não substitui:
- a arquitetura da fase;
- o planejamento macro;
- decisões arquiteturais registradas em ADRs;
- documentação específica de DAGs futuras.

## Papel do Airflow na arquitetura

Na Fase 1, o Airflow ocupa a camada de **orquestração offline** do Chat Pref.

Seu papel é coordenar tarefas que:
- não pertencem ao fluxo síncrono da requisição;
- exigem execução recorrente, controlada ou desacoplada;
- precisam preservar contexto por tenant;
- contribuem para ingestão, benchmark, avaliação ou manutenção do ecossistema RAG.

Airflow não deve ser utilizado como extensão informal do backend principal.

## Tipos de uso previstos

O uso do Airflow na fase inclui, prioritariamente:

- ingestão documental por tenant;
- reindexação controlada da base vetorial;
- benchmark recorrente;
- avaliação offline do pipeline RAG;
- rotinas de monitoramento de deriva semântica;
- tarefas recorrentes de manutenção da camada de recuperação.

## Pré-requisitos

Antes de iniciar a operação com Airflow, os seguintes pontos devem estar atendidos:

- Fase 1 e fases anteriores de base experimental concluídas ou suficientemente estabilizadas;
- `requirements-airflow.txt` definido e versionado;
- ambiente dedicado previsto;
- fronteira entre runtime online e processamento offline explicitada;
- parâmetros mínimos por tenant definidos para os jobs prioritários;
- benchmark e tracking experimental minimamente operacionais.

## Dependências

A camada de orquestração offline depende de:

- `requirements-airflow.txt`

A instalação deste ambiente deve ocorrer apenas na fase prevista no planejamento, evitando introdução prematura de complexidade operacional.

## Regras de operação

### 1. Ambiente separado
O Airflow deve operar em ambiente distinto do backend principal.

### 2. Sem acoplamento ao request path
Nenhuma DAG deve ser usada para deslocar para o Airflow responsabilidade que pertença ao caminho síncrono do atendimento.

### 3. Tenant-awareness obrigatório
Toda rotina relevante deve preservar identificação clara do tenant associado.

### 4. Jobs com propósito explícito
Nenhuma DAG deve existir apenas por formalismo. Cada job precisa responder a uma necessidade concreta de operação, avaliação ou manutenção.

### 5. Introdução incremental
A camada offline deve crescer gradualmente, começando pelas rotinas de maior valor estrutural para a fase.

## Sequência recomendada de preparação

### Etapa 1 — Preparar o ambiente dedicado
Instalar o ambiente de Airflow a partir do arquivo específico da fase.

### Etapa 2 — Validar o ambiente
Confirmar:
- import principal do Airflow funcionando;
- ambiente isolado do backend principal;
- dependências auxiliares disponíveis;
- estrutura inicial pronta para introdução de DAGs.

### Etapa 3 — Definir o primeiro conjunto de DAGs
Priorizar DAGs com maior valor para a fase:
- ingestão;
- benchmark recorrente;
- avaliação offline.

### Etapa 4 — Validar o recorte por tenant
Confirmar que parâmetros e execução preservam a separação lógica entre tenants.

### Etapa 5 — Registrar evidência mínima
Toda ativação relevante da camada offline deve gerar evidência mínima de setup, validação e uso inicial.

## Validação mínima do ambiente

O ambiente Airflow deve ser considerado minimamente válido quando:

- a instalação ocorrer sem conflito relevante;
- o ambiente estiver isolado do backend principal;
- os imports principais funcionarem;
- existir capacidade técnica de registrar ao menos uma DAG inicial;
- a separação entre operação online e orquestração offline estiver documentada.

## Primeiras DAGs recomendadas

A ordem sugerida de introdução é:

### 1. DAG de ingestão por tenant
Para formalizar carga e atualização documental.

### 2. DAG de benchmark recorrente
Para sustentar avaliação periódica da qualidade do pipeline.

### 3. DAG de avaliação offline
Para consolidar execução desacoplada de comparação entre versões.

### 4. DAG de reindexação controlada
Para suportar evolução da base vetorial com governança.

### 5. DAG de monitoração de deriva semântica
Para suportar leitura operacional da saúde semântica por tenant.

## Evidência mínima esperada

A introdução e operação mínima do Airflow devem gerar evidência de:

- ambiente preparado;
- validação básica executada;
- primeira DAG definida;
- tenant-awareness preservado;
- separação entre offline e online documentada.

## Falhas comuns a evitar

- instalar Airflow no mesmo ambiente principal do backend;
- introduzir DAGs antes de existir benchmark minimamente estável;
- usar Airflow para compensar falta de modelagem operacional;
- misturar lógica transacional com rotina offline;
- criar DAGs sem parâmetro explícito de tenant quando o contexto exigir segregação.

## Relação com outros documentos

Este runbook deve ser lido em conjunto com:

- `README.md`
- `CONTEXTO-LLMOps.md`
- `ARQUITETURA-LLMOps.md`
- `PLANEJAMENTO_LLMOps.md`
- `adrs/ADR-003-airflow-como-orquestrador-offline.md`

## Status

Runbook inicial de operação da camada offline definido.

Próximo passo:
- consolidar `requirements-airflow.txt`;
- preparar ambiente isolado;
- validar primeira DAG prioritária da fase.