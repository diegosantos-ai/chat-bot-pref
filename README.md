# {bot_name} - Assistente Virtual da Prefeitura de {client_name}

Chatbot institucional para atendimento ao cidadão via Web Widget, Instagram e Facebook.
Natureza estritamente informativa: não agenda consultas, não concede isenções, não toma decisões administrativas.
Disclaimer obrigatório em todas as respostas: "Informações baseadas na base oficial. Para decisões legais, consulte o Diário Oficial."
A assistente sempre se identifica como IA em treinamento.

## Status do Projeto
| Fase | Descrição | Status | Data |
|------|-----------|--------|------|
| **Fase 1** | Foundation (Contratos, Settings, Schema) | Completa | 10/01/2025 |
| **Fase 2** | RAG Base (Ingester, Retriever, Composer) | Completa | 10/01/2025 |
| **Fase 3** | Pipeline E2E (Classifier, Policy, Orchestrator) | Completa | 11/01/2025 |
| **Fase 3.1** | Protocolos de Crise & Expansão RAG | Completa | 12/01/2025 |
| **Fase 4** | API & Integração Meta | Completa | 15/01/2025 |
| **Fase 5** | Deploy & Observabilidade | Em Progresso | 16/01/2025 |
| **Fase 5.1** | Saneamento e Reestruturação | Completa | 22/01/2026 |
| **Fase 5.2** | Refino RAG (Análise Forense) | Completa | 22/01/2026 |
| **Fase 5.3** | Schema DB & Analytics Views | Completa | 03/02/2026 |

## Visão Geral
- Canais suportados: Web Widget, Instagram DM/Comentários, Facebook DM/Comentários.
- Superfícies: Inbox (privado) e Public Comment (comentário público).
- LGPD: coleta mínima, ocultação de PII em comentários públicos e redirecionamento para inbox.
- Protocolos de crise: suicídio e violência com respostas estáticas e canais oficiais.

## Arquitetura (Visão Rápida)
- Entrada: `POST /api/chat` (web/widget) e `POST /webhook/meta` (Meta).
- Pipeline: NLP -> Classifier -> Policy Guard PRE -> RAG (ChromaDB) -> Composer (Gemini) -> Policy Guard POST -> Seleção.
- Saída: resposta formatada por canal + auditoria em PostgreSQL.
- Observabilidade: métricas Prometheus (`/metrics`), Grafana dashboards e analytics SQL.

## Stack
- Python 3.11+, FastAPI, Pydantic, Uvicorn
- LLM: Google Gemini 2.0 Flash (configurável via `GEMINI_MODEL`)
- Vector store: ChromaDB (`chroma_data/`)
- Banco: PostgreSQL 15+ (auditoria e analytics)
- Observabilidade: Grafana + Prometheus FastAPI Instrumentator
- Infra: Docker, Caddy (HTTPS), systemd (Linux)

## Quickstart (dev local)
### 1. Pré-requisitos
- Python 3.11+
- PostgreSQL 15+ (local ou remoto)
- (Opcional) Docker Desktop para Grafana/Caddy

### 2. Ambiente
- Copie `.env.example` para `.env`.
- Variáveis mínimas: `GEMINI_API_KEY`, `DATABASE_URL`, `CHROMA_PERSIST_DIR`.
- Para embeddings semânticos externos: `EMBEDDING_PROVIDER` (`gemini|openai|qwen`) + `OPENROUTER_API_KEY`.
- Ajustes finos opcionais: `EMBEDDING_MODEL_OVERRIDE`, `EMBEDDING_MODEL_*`, `EMBEDDING_BATCH_SIZE`, `EMBEDDING_MAX_RETRIES`.
- Para Meta: `META_ACCESS_TOKEN_*`, `META_PAGE_ID_*`, `META_APP_SECRET_*`, `META_WEBHOOK_VERIFY_TOKEN*`.
- Valide: `python scripts/ops/validate_infrastructure.py`.

### 3. Dependências
`pip install -r requirements.txt`

### 4. Banco de dados
- Schema: `psql -f db/schema.sql`
- Views: `python scripts/db/create_views.py` ou `psql -f analytics/v1/views.sql`

### 5. Ingestão RAG
`python -m app.rag.ingest data/knowledge_base/BA-RAG-PILOTO-2026.01.v1`

### 6. Rodar API
`python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`

### 7. Teste rápido
`POST /api/chat/simple?message=Qual o telefone da prefeitura?&channel=instagram_dm&surface=INBOX`

## Docker / Deploy
- `docker-compose.yml` sobe API, Caddy e Grafana (PostgreSQL externo).
- Scripts: `scripts/ops/deploy.sh` e `scripts/ops/deploy.ps1`.
- Guia completo: `docs/deploy_guide.md`.
- Serviços systemd: `scripts/systemd/`.

## Observabilidade e Analytics
- Métricas Prometheus: `GET /metrics`.
- Grafana dashboards: `dashboards/terezia/` e provisioning em `provisioning/`.
- Queries e views: `analytics/v1/queries.sql`, `analytics/v1/views.sql`.
- API Analytics: `GET /analytics/summary`, `GET /analytics/export-csv`, `POST /analytics/save-summary`.

## Base RAG
- Base versionada em `data/knowledge_base/BA-RAG-PILOTO-2026.01.v1`.
- Ingestão e manutenção: `app/rag/ingest.py`.
- Scripts úteis: `scripts/chroma_*`.
- Benchmark de embeddings: `python scripts/run_embedding_ab_test.py --providers default,openai --verbose`.

## Scripts Úteis
### Operação
- `scripts/ops/validate_infrastructure.py`
- `scripts/ops/start_tunnel.py`
- `scripts/ops/test_webhook_local.py`
- `scripts/ops/verify_meta_tokens.py`
- `scripts/ops/smoke_tests_prod.py`
- `scripts/ops/backup_postgres.py`
- `scripts/ops/backup_chroma.py`
- `scripts/ops/backup_all.ps1`

### Banco de dados
- `scripts/db/setup_db.py`
- `scripts/db/setup_db.ps1`
- `scripts/db/create_views.py`
- `scripts/db/executar_views.py`

### Debug / QA
- `scripts/debug/debug_rag_score.py`
- `scripts/debug/debug_chroma.py`
- `scripts/run_validation_test.py`
- `scripts/run_bulk_chatbot.py`

## Endpoints Principais
- `GET /` e `GET /health`
- `POST /api/chat`
- `POST /api/chat/simple`
- `GET /analytics/summary`
- `POST /webhook/meta`
- `GET /metrics`

## Documentação
| Arquivo | Descrição |
|---------|-----------|
| `AGENTS.md` / `agents.md` | Contexto central do agente {bot_name} |
| `docs/QUICKSTART_AGENT.md` | Guia rápido para agentes e manutenção |
| `docs/estudo.md` | Regras de negócio e FAQs |
| `docs/apoio_faq.md` | FAQs por cluster |
| `docs/observability.md` | KPIs, métricas e alertas |
| `docs/runbook.md` | Operação e incidentes |
| `docs/deploy_guide.md` | Deploy em Windows/VPS |
| `docs/guia_tokens_meta.md` | Tokens e configuração Meta |
| `docs/meta_app_review_troubleshooting.md` | Guia para App Review da Meta |
| `docs/infrastructure_validation.md` | Validação de infraestrutura |
| `docs/db_setup.md` | Setup do banco de dados |
| `docs/migrations/` | Changelogs de mudanças em servidor/banco |
| `analytics/v1/views.sql` | Views SQL para dashboards |
| `analytics/v1/queries.sql` | Consultas de auditoria |

## Changelog
### v0.7.2 (20/02/2026) - Embeddings semânticos (OpenRouter)
- Robustez de embeddings com batch, retry/backoff e timeout configuráveis.
- Seleção de modelo por provedor (`EMBEDDING_MODEL_GEMINI|OPENAI|QWEN`) e override global (`EMBEDDING_MODEL_OVERRIDE`).
- Metadados de `embedding_provider`/`embedding_model` em ingestão RAG para rastreabilidade.
- Auto-ingest do retriever ajustado para `data/knowledge_base/...` com fallback legado.

### v0.7.1 (04/02/2026) - Integração Meta IG/FB
- Separação de credenciais Meta por plataforma (Instagram/Facebook).
- Webhook unificado em `POST /webhook/meta` com verificação de assinatura.
- Rate limiting e headers de segurança aplicados por padrão.

### v0.7.0 (03/02/2026) - Fase 5.3: Schema DB & Analytics
- **Banco de Dados**: Schema completo em `db/schema.sql` com tipos ENUM, tabelas normalizadas e índices.
- **Analytics**: Queries SQL prontas (`analytics/v1/queries.sql`) e Views de observabilidade (`analytics/v1/views.sql`).
- **Documentação**: Guia de troubleshooting para App Review do Meta (`docs/meta_app_review_troubleshooting.md`).
- **Anonimização**: Nova tabela `usuarios_anonimos` para compliance LGPD.

### v0.6.0 (22/01/2026) - Fase 5.1: Saneamento e Organização
- **Estrutura de Pastas**: Reorganização de scripts em `scripts/ops`, `scripts/db`, `scripts/debug` e base RAG em `data/knowledge_base`.
- **Imports**: Ajuste de paths para compatibilidade com nova estrutura.
- **RAG**: Otimização de Score/Top-K e correção de imports.

### v0.5.0 (22/01/2026) - Fase 5: Melhorias RAG & Observabilidade
- **Observabilidade**: Grafana integrado via Docker Compose.
- **RAG**: Base enriquecida com "Emergências/Desastres" e "Zeladoria/Infraestrutura".
- **Prompts**: Fallbacks mais claros, com proteção de dados em canais públicos.
- **Testes**: Novo script `scripts/run_validation_test.py` para validação em massa.

### v0.4.0 (15/01/2025) - Fase 4: Integração Meta
- Primeiro teste real bem-sucedido no Facebook Messenger.
- Webhook `/webhook/meta` com assinatura HMAC e verify token.
- Pipeline completo validado: Webhook -> Classifier -> RAG -> Resposta -> Auditoria.

### v0.3.0 (11/01/2025) - Fase 3
- ClassifierService com fast patterns + fallback LLM.
- PolicyGuard PRE/POST com detecção de saúde clínica e gatilhos de crise.
- OrchestratorService com eventos de auditoria e seleção de resposta.

### v0.2.0 (10/01/2025) - Fase 2
- MarkdownIngester, RAGRetriever e RAGComposer.
- Base de conhecimento inicial (BA-RAG-PILOTO-2026.01.v1).

### v0.1.0 (10/01/2025) - Fase 1
- Contratos (Enums, DTOs), Settings e schema PostgreSQL.
- Sistema de prompts versionado.

## Compliance e Segurança
- Caráter informativo: não realiza atos administrativos.
- LGPD: coleta mínima; ocultar PII em comentários públicos; retenção definida.
- Policy Guard com gatilhos de crise (suicídio/violência), redirecionamentos e bloqueios.
- Disclaimer obrigatório nas respostas.

## Licença
Projeto interno - Prefeitura de {client_name} (2026)
#   c h a t - b o t - p r e f 
 
 