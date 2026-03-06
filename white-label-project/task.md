# Implementation Plan: Nexo Basis White-Label SaaS

## Overview

Este plano direciona a execução das tarefas para reestruturar completamente a arquitetura monolítica engessada do Chatbot TerezIA para um produto SaaS governamental. A arquitetura de implantação foi adaptada para plugar-se perfeitamente na *Nexo Shared Infraestrutura* (`infra_nexo-network`), abdicando de contêineres e volumes estatais locais no favor de delegar o tráfego ao Traefik (`80/443`) e os bancos às instâncias unificadas (`nexo-postgres` e `nexo-chromadb`), consumindo a porta host `8101`.

**Stack Tecnológico:** Python, FastAPI, PostgreSQL unificado (RLS ativo), ChromaDB unificado, Traefik, Docker
**Estratégia:** Subir base de fundação de dados -> Refatorar Rede/Docker -> Limpar códigos sujos na camada lógica -> Implementar Middleware FastAPI de Roteamento -> Abastecer e ligar a Ingestão de conhecimento automatizada.

## Tasks

### Fase 1: Adequação da Infraestrutura & Networking Compartilhado (Tempo Estimado: 1 Dia)

- [x] 1. Adequação de Contêineres (Docker Compose)
  - [x] 1.1 Remover a declaração de construção dos serviços `db`, `chromadb`, e quaisquer bases auxiliares do `docker-compose.yml` da raiz do chatbot.
  - [x] 1.2 Atualizar o serviço principal da API para usar a porta `8101:8000` em conformidade com o `PORTS.md`.
  - [x] 1.3 Renomear a API no compose para um nome aderente ao padrão (ex: `nexo-gov-api`).
  - [x] 1.4 Adicionar rede externa compartilhadora: `networks: infra-network: external: true, name: infra_nexo-network`.
  
- [x] 2. Adequação de Variáveis de Conexões (.env)
  - [x] 2.1 Refatorar TODAS as URIs de configuração e inicialização (SQLAlchemy, Langchain Chroma Client, Redis Cache) para referenciar os contêineres hostnames (ex: `nexo-postgres`, `nexo-chromadb`, `nexo-redis`).

### Fase 2: Fundação Multi-Tenant de Dados (Tempo Estimado: 2-3 Dias)

- [x] 3. Configurar Isolamento Lógico de Transações no PostgreSQL (Row-Level Security)
  - [x] 3.1 Criar migration para adicionar campo `tenant_id` VARCHAR(50) em tabelas-chave.
  - [x] 3.2 Criar tabelas core multi-tenant: `tenants`, `tenant_credentials`, e `tenant_configs`.
  - [x] 3.3 Habilitar funcionalidade `ENABLE ROW LEVEL SECURITY` criando *Policy* em TODAS tabelas sensíveis buscando `current_setting('app.tenant_id', true)`.
  - [x] 3.4 Escrever queries/scripts administrativos de mock bootstrapping.

- [x] 4. Configurar Separação de Vetores e Coleções via ChromaDB
  - [x] 4.1 Refatorar a inicialização da Collections no Retriever alterando para o formato dinâmico `{tenant_id}_knowledge_base`.
  - [x] 4.2 Blindar operações de RAG gerando Collections *lazily* na primeira requisição, se necessário.

### Fase 3: Escudo de Camada Lógica via Middleware Web (Tempo Estimado: 2 Dias)

- [x] 5. Injetar Gestor de Contexto (`contextvars`) Python
  - [x] 5.1 Instanciar a variável contextvar de sessão atrelada globalmente. (`app/tenant_context.py` — concluído na Fase 2)
  - [x] 5.2 Alterar dependência db (yield generator) para forçar o comando Postgres `SET LOCAL app.tenant_id = :tenant_id` na transição do request. (`audit/repository.py` — concluído na Fase 2)

- [x] 6. Criar Interceptor de Roteamento de Tenant no Webhook
  - [x] 6.1 Codar Interceptor na entrada do endpoint RAIZ do Webhook do Meta. (`app/api/webhook.py`)
  - [x] 6.2 Processar Payload -> Procurar Tenant da Página (LRU Cache/DB) -> Seta no Contextvar. (`app/tenant_resolver.py` + `tenant_context.set_tenant()`)
  - [x] 6.3 Desviar com blocagem silenciosa pacotes de Páginas sem Tenant logado. (páginas sem tenant são ignoradas; evento não é despachado)

- [x] 7. Refatoração de Templates Puxados do Banco
  - [x] 7.1 Mudar System Prompts literais para compor via placeholders (ex: `{client_name}`). (`get_tenant_prompt()` em `app/prompts/__init__.py` injeta vars do tenant automaticamente)
  - [x] 7.2 Migrar chaves hard-coded da Meta (PAGE_ACCESS_TOKEN) de forma para consumo do banco injetados na Sessão atual dinamicamente. (`MetaSender._get_access_token()` agora é async e usa `TenantConfig`. Credenciais armazenadas em `tenant_credentials` via migration `002_*.sql`)

### Fase 4: Operação, Limpeza, e Pipeline (Tempo Reservado: 2 Dias)

- [x] 8. Consolidar Automação Assíncrona RAG ETL
  - [x] 8.1 Ajustar Crawler local fazendo iteração de Tenants via job agendado. (`scripts/rag_etl_job.py` — itera tenants ativos do DB, ingere collection `{tenant_id}_knowledge_base`, suporta `--force` e `--tenant`)
  - [x] 8.2 Criar o Script mock rápido `setup_demo_tenant.py` providenciando bot Dummy "Prefeitura de Nova Espeçana" para GTM Vendas. (`scripts/setup_demo_tenant.py` — cria base de conhecimento, faz upsert no DB e ingere no ChromaDB. Suporta `--reset` e `--dry-run`)

- [x] 9. Finalizar e Auditar Componentes Residuais
  - [x] 9.1 Verificar Grafana Dashboards/Logs certificando-se de que os metadados de logs carregam atrelamento com o `tenant_id`. (`app/logging_config.py` — `JsonFormatter` injeta `tenant_id` automaticamente via `tenant_context.get_tenant()` em todo log JSON)
  - [x] 9.2 Realizar Handoff Final do Kiro de volta ao usuário. (Documentação e progresso.md atualizados. Projeto SaaS multi-tenant completo e commitado na branch `limpeza-pipeline`.)
