# ADR-003 — Airflow como Orquestrador Offline

## Status
Aceito

## Contexto

A Fase 1 do Chat Pref introduz uma camada de LLMOps que exige execução recorrente e desacoplada de tarefas que não pertencem ao fluxo síncrono de atendimento.

Entre essas tarefas estão:
- ingestão de documentos;
- reindexação da base vetorial;
- execução recorrente de benchmark;
- avaliação offline do pipeline RAG;
- rotinas de monitoramento de deriva semântica;
- processamento periódico por tenant.

Na fundação operacional do projeto, o foco esteve no runtime transacional e na validação do pipeline principal. Com a nova fase, torna-se necessário formalizar uma camada de execução offline, separada do request path, para sustentar governança, avaliação e manutenção contínua do ecossistema RAG.

## Decisão

O projeto adota **Airflow** como orquestrador offline da Fase 1.

Airflow será utilizado para coordenar jobs recorrentes e desacoplados do runtime principal, especialmente aqueles relacionados a:
- ingestão;
- reindexação;
- benchmark;
- avaliação recorrente;
- monitoramento de saúde semântica da base por tenant.

## Justificativa

A escolha por Airflow foi feita pelos seguintes motivos:

1. **separação clara entre online e offline**
   O projeto precisa distinguir de forma explícita o que pertence ao fluxo síncrono de atendimento e o que deve ser executado como job assíncrono e orquestrado.

2. **aderência ao tipo de tarefa**
   As atividades previstas têm natureza de pipeline operacional recorrente, com dependências, parâmetros e possibilidade de evolução incremental, o que se encaixa bem no modelo de DAGs.

3. **governança operacional**
   A orquestração formal reduz dependência de execução manual, scripts soltos e rotinas informais.

4. **alinhamento com maturidade de plataforma**
   A Fase 1 busca elevar o Chat Pref para uma camada de engenharia mais demonstrável, reprodutível e operável.

5. **aderência ao objetivo de processo seletivo**
   A adoção de Airflow fortalece a narrativa de pipeline de IA operável, especialmente em conjunto com benchmark, reindexação e avaliação offline.

## Papel do Airflow na arquitetura

Airflow passa a ocupar a camada de **Orquestração Offline** da arquitetura da Fase 1.

Seu papel será:
- disparar jobs recorrentes;
- encadear tarefas offline;
- permitir execução controlada por tenant;
- separar rotinas de manutenção e avaliação do pipeline transacional;
- sustentar evolução organizada da camada de dados e RAG.

Airflow **não substitui**:
- o backend FastAPI;
- a auditoria operacional;
- o experiment tracking;
- a observabilidade operacional do request path.

## Escopo de uso

Na Fase 1, Airflow será considerado principalmente para:

- DAG de ingestão documental por tenant;
- DAG de reindexação controlada;
- DAG de benchmark recorrente;
- DAG de avaliação offline;
- DAG de monitoramento de deriva semântica;
- rotinas de manutenção do ecossistema vetorial.

## Regras de adoção

A adoção de Airflow no projeto deve seguir estas regras:

### 1. Ambiente separado
Airflow deve operar em ambiente distinto do backend principal.

### 2. Sem acoplamento ao request path
Nenhum job orquestrado deve ser inserido no caminho crítico síncrono da requisição por conveniência.

### 3. Tenant-awareness
Toda DAG ou rotina relevante deve preservar isolamento lógico por tenant.

### 4. Introdução incremental
Airflow só deve ser introduzido a partir da fase prevista no planejamento, após fundação de tracking, benchmark e avaliação mínima.

### 5. Uso para jobs reais
Airflow não deve ser adotado apenas por valor cosmético arquitetural. Seu uso deve estar ligado a rotinas concretas e recorrentes.

## Alternativas consideradas

### 1. Executar tudo manualmente por script
Rejeitada.

Motivo:
- baixa governança;
- alta dependência de execução humana;
- pouca rastreabilidade;
- risco de deriva operacional.

### 2. Acoplar rotinas offline ao backend principal
Rejeitada.

Motivo:
- polui o runtime transacional;
- aumenta risco operacional;
- mistura responsabilidades que devem permanecer separadas.

### 3. Adiar indefinidamente a orquestração
Rejeitada.

Motivo:
- compromete a evolução para benchmark recorrente, reindexação e monitoramento estruturado;
- enfraquece a maturidade da fase.

### 4. Adotar Airflow em ambiente separado
Aceita.

Motivo:
- melhor equilíbrio entre formalização operacional, desacoplamento e clareza arquitetural.

## Consequências

### Positivas
- melhor separação entre online e offline;
- base mais sólida para benchmark recorrente e reindexação;
- menor dependência de execução manual;
- maior clareza operacional da camada RAG;
- documentação mais madura da arquitetura da fase.

### Negativas / trade-offs
- aumento de complexidade operacional;
- necessidade de ambiente separado;
- custo adicional de manutenção;
- risco de adoção precoce se entrar antes da fase correta.

## Impacto na implementação

A adoção de Airflow implica:

- criação de ambiente dedicado de orquestração;
- definição de `requirements-airflow.txt`;
- modelagem de DAGs por responsabilidade;
- definição de parâmetros mínimos por tenant;
- documentação do limite entre jobs offline e runtime transacional.

## Impacto na documentação

A partir desta decisão:
- a arquitetura deve tratar Airflow como componente da camada offline;
- o planejamento deve localizar sua introdução apenas na fase prevista;
- os runbooks devem documentar setup e operação mínima;
- a distinção entre execução síncrona e orquestração recorrente deve permanecer explícita.

## Relação com outras decisões

Esta ADR depende conceitualmente de:
- separação entre operação e experimentação;
- formalização da arquitetura-alvo da Fase 1;
- existência de benchmark e avaliação que justifiquem rotinas recorrentes.

## Referências internas
- `docs-LLMOps/CONTEXTO-LLMOps.md`
- `docs-LLMOps/ARQUITETURA-LLMOps.md`
- `docs-LLMOps/PLANEJAMENTO-LLMOps.md`
- `docs-LLMOps/adrs/ADR-001-separacao-auditoria-vs-tracking.md`
- `docs-LLMOps/adrs/ADR-002-mlflow-como-stack-de-experimentacao.md`
