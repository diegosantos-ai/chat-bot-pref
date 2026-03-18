# Fase 8 — Orquestração Offline com Airflow

## Objetivo
Preparar a base operacional para orquestração de tarefas offline (ingestão, reindexação, avaliação formal) via Airflow.

## Decisões Arquiteturais e Restrições
1. **Ambiente Separado:** O ambiente de orquestração do Airflow deve rodar completamente isolado do ambiente principal do backend da API. Suas dependências e ciclo de vida não devem se misturar.
2. **Nenhum Acoplamento com Runtime Online:** Esta fase e o Airflow em si não impactam o caminho crítico transacional do backend (FastAPI). Nenhum processo offline deve bloquear ou ditar a performance da API.
3. **Escopo deste Bloco:** Este bloco trata apenas a preparação da base operacional. Ele foca no diagnóstico, provisionamento limpo de dependências com `requirements-airflow.txt` e delimitação das fronteiras arquiteturais.

## Diagnóstico Inicial
- **Versão do Python:** A documentação do Airflow indica que o suporte principal no ambiente atual é dado na faixa de Apache Airflow `2.10.x` (ou a nova futura `3.x` suportada pelo seu host Python). Dependendo da versão local de testes utilizada (ex: Python 3.13), algumas releases específicas de Airflow são ignoradas por limitação declarada dos packages.
- **Dependências:** O arquivo `requirements-airflow.txt` foi reescrito para relaxar as minor versions de `apache-airflow`, mantendo `pandas` e `psycopg` nas versões mínimas compatíveis do ambiente, sem sobrecarregar a esteira online com dependências cruzadas.
- **Isolamento:** A camada de orquestração não reside nos fluxos de `app/api/...`, será operada localmente numa pasta ou serviço docker focado estritamente na parte do Airflow, com DAGs alocadas corretamente em sua própria pipeline.

## Próximos Passos
- Inicializar a estrutura mínima oficial para pastas como `/dags`, `/plugins` seguindo as boas práticas tenant-aware.
- Instanciar um Dockerfile para o Worker/Webserver do Airflow ou serviço respectivo dentro de um novo compose complementar (ex: `docker-compose.airflow.yml`).
