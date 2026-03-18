# Fase 8 — Orquestração Offline com Airflow

## Objetivo
Preparar a base operacional para orquestração de tarefas offline (ingestão, reindexação, avaliação formal) via Airflow.

## Decisões Arquiteturais e Restrições
1. **Ambiente Separado:** O ambiente de orquestração do Airflow deve rodar completamente isolado do ambiente principal do backend da API. Suas dependências e ciclo de vida não devem se misturar.
2. **Nenhum Acoplamento com Runtime Online:** Esta fase e o Airflow em si não impactam o caminho crítico transacional do backend (FastAPI). Nenhum processo offline deve bloquear ou ditar a performance da API.
3. **Escopo deste Bloco:** A documentação oficializou o baseline do Airflow no ambiente existente e as fundações de orquestração mínimas.
4. **Camada de DAGs Delgada (Thin-DAG):** A orquestração (via `airflow/dags/`) aciona serviços via entrypoints finos. Regras de negócio não devem ser escritas na matriz da DAG, preservando a coerência entre testes de modelo e execução orquestrada.
5. **Parametrização:** A multiplicidade de origens no bot é espelhada via Airflow Models/Param, fazendo os jobs tornarem-se "tenant-aware" durante a inicialização/acionamento da trigger.

## Diagnóstico Inicial
- **Versão do Python:** O ambiente validado confirmou o uso do `Python 3.13` com `Apache Airflow 2.11.2`. A documentação e os requisitos assumem esse estado como oficial para a orquestração offline local.
- **Dependências:** O arquivo `requirements-airflow.txt` relaxou as *minor versions* de `apache-airflow`, mantendo `pandas` e `psycopg` base, sem sobrecarregar a esteira online.
- **Isolamento e Estrutura:** As DAGs assumiram um formato `stub` na pasta base recém criada `airflow/dags/`, aguardando a consolidação das interações com a CLI/Python subjacentes para testagem isolada, mantendo integridade com as definições de tracking experimental e sem contaminar o path da API.

## Próximos Passos
- Inicializar a base de metadados local com `AIRFLOW_HOME` e `airflow db migrate`.
- Realizar teste de execução ("run" local) dos stubs usando inputs dos tenants.
- Integrar os stubs com os reais scripts Python/Bash da codebase raiz (ex: scripts/rag_ingest.py).
