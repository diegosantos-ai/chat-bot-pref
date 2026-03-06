

# Tecnologias e Ferramentas — Projeto TerezIA

## Tecnologias Principais

---
**Python 3.11+**
	- Linguagem principal do backend, scripts e automações.
	- Gera: API, scripts, processamento de dados.

**FastAPI**
	- Framework web para APIs modernas em Python.
	- Função: Servidor HTTP, rotas REST, integração frontend.
	- Gera: API REST, docs interativa (/docs).

**PostgreSQL**
	- Banco de dados relacional open source.
	- Função: Persistência, auditoria, analytics.
	- Gera: Tabelas, views, relatórios SQL.

**ChromaDB**
	- Banco vetorial para IA/RAG.
	- Função: Busca de embeddings/textos.
	- Gera: Contexto para respostas da IA.

**OpenAI GPT-4.1**
	- Modelo de linguagem natural (LLM).
	- Função: Geração de respostas, compreensão de linguagem.
	- Gera: Respostas do chatbot, análise de intenção.

**Grafana**
	- Dashboards e monitoramento operacional.
	- Função: Visualização de KPIs, métricas.
	- Gera: Dashboards de latência, erros, fallback.

**Metabase**
	- BI e análise de dados.
	- Função: Relatórios e exploração de dados.
	- Gera: Dashboards, relatórios customizados.

**Facebook/Instagram API**
	- APIs oficiais das redes sociais Meta.
	- Função: Recebimento/envio de mensagens, webhooks.
	- Gera: Atendimento ao cidadão via redes sociais.

---

## Bibliotecas e Ferramentas Utilizadas

---
**Uvicorn**
	- Servidor ASGI rápido para Python.
	- Função: Executar o backend FastAPI.
	- Gera: Servidor HTTP local/produção.

**pytest**
	- Framework de testes automatizados.
	- Função: Testes unitários e integração.
	- Gera: Relatórios de testes.

**python-dotenv**
	- Carrega variáveis de ambiente do .env.
	- Função: Gerenciamento seguro de configs.
	- Gera: Variáveis de ambiente no runtime.

**httpx**
	- Cliente HTTP assíncrono.
	- Função: Integração com APIs externas (Meta IG/FB).
	- Gera: Requisições/respostas HTTP.

**psycopg2**
	- Driver PostgreSQL para Python.
	- Função: Scripts e automações SQL.
	- Gera: Execução de comandos SQL, migrações.

**asyncpg**
	- Driver PostgreSQL assíncrono.
	- Função: Operações assíncronas no banco.
	- Gera: Queries rápidas e não bloqueantes.

**pydantic / pydantic-settings**
	- Validação e gerenciamento de configs.
	- Função: Tipagem e validação de dados.
	- Gera: Classes de configuração, validação automática.

**Prometheus FastAPI Instrumentator**
	- Middleware para métricas Prometheus.
	- Função: Expor métricas HTTP para observabilidade.
	- Gera: Métricas de latência, requisições, erros.
