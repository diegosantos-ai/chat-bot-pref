# Fase 1 - Inventario Tecnico do Legado

Data: 2026-03-13

## Escopo

Este documento consolida a execucao da `Fase 1 - Diagnostico e Inventario do Legado` definida em `docs/planejamento_fases.md`.

Objetivo aplicado nesta analise:
- identificar o que deve ser preservado como contrato da aplicacao
- identificar o que deve ser reescrito do zero para um repositorio publico, explicavel e reproduzivel
- identificar o que deve ser descartado por legado, acoplamento operacional ou ruído de implementacao

## Metodo

Varreduras executadas sobre:
- `app/`
- `admin-panel/`
- `nexo-admin/`
- `db/`
- `scripts/`
- `.github/workflows/`
- `docker-compose*.yml`
- `Dockerfile`
- `logging/`
- `dashboards/`
- `docs/`

Comandos usados na fase:
- `find . -maxdepth 2 -type d | sort`
- `rg -n -i "pilot-atendimento|santa tereza|terezia|governador|nexo basis|nexo-gov|nexo_prefa|core_saas_gov|infra_nexo-network|nexo-postgres|nexo-chromadb|nexo-redis|verify_token_webhook|service_account.json|RAG_BASE_ID|knowledge_base" .`
- `find scripts .github/workflows db -maxdepth 3 -type f | sort`
- `git ls-files '.env*' '*/.env*' '*credentials*' '*secret*' '*.pem' '*.key'`
- leituras direcionadas de arquivos criticos de runtime, deploy e admin

## Resumo Executivo

O repositório atual nao representa uma base publica limpa de produto. Ele mistura:
- legado `Pilot Atendimento`
- legado `Terezia`
- identidade `Nexo Basis / Nexo Prefa`
- acoplamentos de deploy e infraestrutura de ambiente privado
- contrato multi-tenant parcial com fallbacks mono-tenant ainda ativos

Conclusao da fase:
- existe valor real para preservar no contrato funcional da aplicacao
- a camada operacional e de produto demonstravel precisa ser reescrita quase por completo
- boa parte da estrutura ativa atual enfraquece a tese tecnica que o repositório precisa sustentar

## O Que Deve Ser Preservado Como Contrato

### 1. Arquitetura logica do backend

Arquivos-base:
- `app/orchestrator/service.py`
- `app/policy_guard/service.py`
- `app/rag/retriever.py`
- `app/rag/composer.py`
- `app/tenant_context.py`
- `app/tenant_resolver.py`
- `app/tenant_config.py`
- `app/audit/repository.py`
- `app/contracts/dto.py`
- `app/contracts/enums.py`

Valor preservavel:
- pipeline `classifier -> policy guard -> RAG -> resposta -> auditoria`
- separacao entre retrieval, composition e policy
- uso de `tenant_context` e `tenant_resolver` como base do contrato tenant-aware
- trilha de auditoria e eventos do pipeline
- guardrails de crise, PII, prompt injection e fora de escopo

### 2. Requisitos de plataforma que ja aparecem no codigo

Requisitos explicitados no codigo atual:
- isolamento por tenant no banco e no RAG
- auditoria por request
- restricoes diferentes para inbox e comentario publico
- tratamento de canais Meta
- observabilidade e validacao tecnica como parte do produto

### 3. Dominio minimo aproveitavel

Entidades e conceitos que fazem sentido reaproveitar conceitualmente:
- `tenants`
- `tenant_credentials`
- eventos de auditoria
- jobs de ingest
- logs/analytics por tenant

Observacao:
- isso nao implica reaproveitar schema, scripts ou flows atuais sem redesenho

## O Que Deve Ser Reescrito do Zero

### 1. Infraestrutura e operacao

Arquivos/areas:
- `docker-compose.yml`
- `docker-compose.local.yml`
- `Dockerfile`
- `.github/workflows/deploy.yml`
- `scripts/ops/deploy.sh`
- `scripts/ops/deploy.ps1`
- `app/api/deploy.py`
- `scripts/systemd/`
- `logging/`
- `dashboards/`
- `provisioning/`

Motivo:
- forte acoplamento com infraestrutura privada, nomes legados, services de systemd e deploy via webhook
- modelo operacional nao reproduzivel para um case publico
- mistura de Docker local, rede compartilhada privada, systemd e automacao manual

### 2. Camada de admin e superficie publica

Arquivos/areas:
- `app/api/admin.py`
- `app/api/panel.py`
- `admin-panel/`
- `nexo-admin/`

Motivo:
- rotas hardcoded como `/tereziapi/tereziadmin` e `/tereziadmin`
- JWT com fallback inseguro
- acoplamento entre painel, API e storage atual
- experiencia e naming desalinhados com o produto demonstravel

### 3. Banco de dados e automacao de schema

Arquivos/areas:
- `db/schema.sql`
- `db/migrations/`
- `scripts/db/`
- `nexo-admin/migrations/`

Motivo:
- ha valor de dominio, mas nao ha sinal de base publica minimamente limpa para seguir como fundacao final
- ha mistura de legado, comentarios historicos e evolucao incremental de estrutura
- o schema atual deve servir mais como fonte de regras do que como fundacao pronta

## O Que Deve Ser Descartado ou Isolado Como Legado

### 1. Identidades antigas e narrativas misturadas

Achados principais:
- `Pilot Atendimento MVE`
- `Terezia`
- `Nexo Basis Governador`
- `Nexo Prefa`

Arquivos afetados:
- `app/`
- `db/`
- `scripts/`
- `dashboards/`
- `logging/`
- `panel/`
- `tests/`
- `analytics/v1/queries.jsonl`

### 2. Artefatos de ambiente privado

Achados principais:
- `infra_nexo-network`
- `nexo-postgres`
- `nexo-chromadb`
- `nexo-redis`
- `core_saas_gov`
- `nexobasis.com.br`
- services `terezia-api.service` e `terezia-grafana.service`

Esses itens devem sair da estrutura ativa de produto publico.

### 3. Dados e logs historicos

Arquivos/areas:
- `analytics/v1/queries.jsonl`
- `dashboards/terezia/`
- `dashboards/02-terezia-api.json`
- `dashboards/terezia-logs-dashboard.json`
- `logging/README.md`
- `logging/GRAFANA_JSON_FIELDS.md`

Motivo:
- carregam nomes historicos, traces operacionais e narrativa de ambiente privado
- agregam pouco valor ao case publico no estado atual

## Achados Principais

### A1. Identidade do projeto esta fragmentada

Tipo: funcional e cosmetico

Arquivos relevantes:
- `app/settings.py`
- `app/orchestrator/service.py`
- `app/policy_guard/service.py`
- `app/contracts/dto.py`
- `db/schema.sql`
- `panel/index.html`
- `scripts/systemd/*`
- `dashboards/*`

Descricao:
- runtime, docs internas, painel, observabilidade e scripts usam marcas e contextos diferentes
- isso reduz clareza arquitetural e enfraquece a apresentacao publica do projeto

Impacto:
- alto para produto demonstravel
- medio para runtime

### A2. O contrato multi-tenant esta incompleto no chat direto

Tipo: funcional

Arquivos relevantes:
- `app/contracts/dto.py`
- `app/api/chat.py`
- `app/api/webhook.py`
- `app/tenant_context.py`
- `app/tenant_resolver.py`
- `app/channels/meta_sender.py`
- `app/tenant_config.py`

Descricao:
- o webhook resolve `page_id -> tenant_id`
- `ChatRequest` nao exige `tenant_id`
- `/api/chat` nao explicita estrategia de entrada de tenant
- `meta_sender` e `tenant_config` ainda aceitam fallback global

Impacto:
- alto para arquitetura
- alto para isolamento tenant-aware

### A3. Existem defaults legados de base e collection

Tipo: funcional

Arquivos relevantes:
- `app/settings.py`
- `app/rag/retriever.py`
- `app/rag/ingest.py`
- `scripts/chroma_ingest_base.sh`
- `scripts/chroma_count_collection.sh`
- `tests/test_embedding_ab.py`
- `app/api/admin.py`

Descricao:
- `RAG_BASE_ID = "default"`
- scripts assumem `data/knowledge_base/default`
- contagem usa `default_knowledge_base`
- retriever ainda aceita caminho legado `base/<RAG_BASE_ID>`

Impacto:
- alto para Fase 3 e Fase 4

### A4. Existem fallbacks inseguros ou improprios para ambiente demonstravel

Tipo: funcional

Arquivos relevantes:
- `app/settings.py`
- `app/main.py`
- `app/api/admin.py`
- `app/api/webhook.py`

Descricao:
- `CORS_ORIGINS = ["*"]`
- `ALLOWED_HOSTS = ["*"]`
- `META_WEBHOOK_VERIFY_TOKEN = "verify_token_webhook"`
- JWT do admin cai para `"dev-secret-change-in-production"`
- webhook aceita request sem assinatura valida se `META_APP_SECRET` nao estiver configurado

Impacto:
- alto para seguranca
- alto para confianca arquitetural

### A5. A camada de deploy atual e descarte claro

Tipo: funcional

Arquivos relevantes:
- `.github/workflows/deploy.yml`
- `app/api/deploy.py`
- `scripts/ops/deploy.sh`
- `scripts/ops/deploy.ps1`

Descricao:
- workflow chama URL fixa `https://nexobasis.com.br/tereziapi/updateAPI`
- endpoint de deploy executa `git fetch`, `git pull`, `pip install` e `systemctl restart`
- fluxo e acoplado a host, service name e modelo operacional privado

Impacto:
- alto para operacao
- alto para reprodutibilidade

### A6. O painel e o admin carregam naming e roteamento legados

Tipo: funcional

Arquivos relevantes:
- `app/api/admin.py`
- `admin-panel/vite.config.ts`
- `admin-panel/src/services/api.ts`
- `admin-panel/src/App.tsx`
- `admin-panel/src/pages/Login.tsx`
- `panel/`

Descricao:
- prefixos `/tereziapi/tereziadmin` e `/tereziadmin`
- telas ainda usam `Nexo Prefa` e `Nexo Basis`
- ha duas superfícies admin/painel concorrentes (`panel/`, `admin-panel/`, `nexo-admin/`)

Impacto:
- alto para produto demonstravel
- medio para runtime

### A7. Banco, observabilidade e scripts ainda carregam infraestrutura privada

Tipo: funcional

Arquivos relevantes:
- `app/settings.py`
- `.env.example`
- `.env.prod.example`
- `docker-compose*.yml`
- `scripts/start_local.*`
- `scripts/systemd/*`
- `logging/*`
- `dashboards/*`
- `provisioning/*`

Descricao:
- hostnames, DB names, network names e services sao especificos de ambiente privado
- observabilidade atual foi montada em torno de `terezia-*`

Impacto:
- alto para reconstruir Docker/Terraform/CI

### A8. Existem artefatos operacionais e dados historicos na arvore ativa

Tipo: funcional e sensivel

Arquivos relevantes:
- `analytics/v1/queries.jsonl`
- `scripts/setup_demo_tenant.py`
- `dashboards/*`
- `logging/*`

Descricao:
- ha exemplos, traces e dados historicos que nao fortalecem a apresentacao publica
- o arquivo `analytics/v1/queries.jsonl` contem conversas e contexto historico do sistema

Impacto:
- medio para seguranca reputacional
- medio para clareza do case

## Scripts Criticos Identificados

Alta criticidade:
- `scripts/ops/deploy.sh`
- `scripts/ops/deploy.ps1`
- `scripts/start_local.sh`
- `scripts/start_local.ps1`
- `scripts/systemd/setup_systemd.sh`
- `scripts/setup_demo_tenant.py`
- `scripts/rag_etl_job.py`
- `scripts/ops/validate_infrastructure.py`
- `scripts/chroma_ingest_base.sh`
- `scripts/chroma_count_collection.sh`

Media criticidade:
- `scripts/db/setup_db.py`
- `scripts/db/create_views.py`
- `scripts/setup_grafana.py`
- `scripts/setup_security.py`
- `scripts/ops/test_webhook_local.py`
- `scripts/ops/verify_meta_tokens.py`

Baixa criticidade ou descarte provavel:
- automacoes de branch/issues
- scripts de debugging local
- artefatos de grafana/loki ligados ao ambiente antigo

## Arquivos Sensiveis e Pontos de Risco

Arquivos versionados de atencao:
- `.env.prod.example`
- `app/secrets.py`
- `nexo-admin/api/credentials.py`
- `nexo-admin/static/views/credentials.js`
- `docs/examples/credentials/README.md`

Pontos de risco:
- endpoints e telas para editar credenciais de tenant em estrutura ativa
- exemplos de `.env` ainda ancorados em hostnames e bancos do ambiente privado
- `GOOGLE_APPLICATION_CREDENTIALS = "service_account.json"` em `app/settings.py`
- `AWS_SECRET_NAME = "terezia/prod"` em `app/settings.py`

Observacao:
- nesta fase nao foi identificado segredo real versionado nas areas ativas lidas
- ainda assim ha forte heranca de operacao sensivel no design atual

## Separacao Entre Funcional e Cosmetico

### Funcional

Deve orientar as proximas fases:
- contrato de tenant incompleto no chat
- fallbacks globais de Meta e tenant
- defaults de base/collection
- deploy via webhook e systemd
- routes e basenames hardcoded do admin
- defaults inseguros de CORS, hosts, JWT e webhook
- infra privada codificada em settings, compose, scripts e examples

### Cosmetico

Pode ser tratado depois que a base estrutural estiver redesenhada:
- cabecalhos de docstring com nomes antigos
- comentarios antigos em arquivos que nao afetam runtime
- nomes visuais em docs secundarias

Observacao:
- varios nomes antigos aparecem em lugares que parecem cosmeticos, mas em muitos arquivos eles sinalizam acoplamento funcional real
- por isso a troca textual nao deve preceder o redesenho estrutural

## Classificacao Por Impacto

### Impacto Alto

- `app/settings.py`
- `app/api/chat.py`
- `app/api/webhook.py`
- `app/channels/meta_sender.py`
- `app/api/admin.py`
- `app/api/deploy.py`
- `app/rag/retriever.py`
- `app/rag/ingest.py`
- `docker-compose.yml`
- `docker-compose.local.yml`
- `.github/workflows/deploy.yml`
- `scripts/ops/deploy.sh`
- `scripts/systemd/*`

### Impacto Medio

- `panel/`
- `admin-panel/`
- `nexo-admin/`
- `logging/`
- `dashboards/`
- `scripts/ops/validate_infrastructure.py`
- `scripts/start_local.*`
- `scripts/setup_demo_tenant.py`

### Impacto Baixo

- docs visuais e textos de apoio
- artefatos de snapshot
- comentarios e headers sem efeito em runtime

## Proximos Cortes Recomendados

### Prioridade P0

- definir a fronteira do que permanece como contrato do produto
- congelar ou remover da estrutura ativa o deploy via webhook/systemd
- neutralizar rotas e naming publicos do admin e painel
- isolar ou remover artefatos de observabilidade e analytics do ambiente antigo

### Prioridade P1

- definir contrato explicito de `tenant_id` para chat e operacoes criticas
- eliminar fallbacks globais de tenant e Meta
- redefinir modelo de configuracao publica do projeto

### Prioridade P2

- reconstruir Docker e ambiente local
- reconstruir CI/CD e deploy
- redesenhar banco e migrations com foco em base publica explicavel

### Prioridade P3

- limpar identidade textual residual
- reconstruir a camada de demo publica e evidencias

## Conclusao da Fase 1

O repositório atual possui uma base conceitual valiosa, mas a implementacao ativa esta fortemente contaminada por:
- multiplas identidades historicas
- acoplamento a infraestrutura privada
- defaults de runtime e seguranca improprios
- contrato multi-tenant incompleto em fluxos importantes
- painel/admin e deploy desalinhados com um case publico reproduzivel

Decisao arquitetural recomendada:
- preservar regras de negocio, contratos, pipeline e principios de tenant-aware
- reescrever infraestrutura, deploy, painel administrativo e boa parte da configuracao operacional
- tratar a implementacao atual como fonte de requisitos e nao como base final
