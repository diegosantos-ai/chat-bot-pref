# {bot_name} - Contexto do Agente

Este documento serve como a fonte central de verdade e contexto para o desenvolvimento, manutenção e operação do assistente virtual {bot_name}.

## ATENÇÃO AGENTES DE IA:
- Quaisquer modificações de scripts devem ser refletidas neste documento.
- Quaisquer alterações em estruturas de bancos de dados, variaveis de ambiente, dependencias ou alterações no servidor, precisam ser documentadas na pasta 'docs/migrations/' com changelog detalhado do que mudou e do que precisa ser aplicado no servidor.
- Para cada alteração nova necessária no servidor, crie um arquivo md na pasta 'docs/migrations/' com o nome no formato `YYYYMMDD_HHMMSS_descricao.md` detalhando as mudanças.
- Qualquer alteração que possa quebrar o funcionamento do servidor deve ser documentada em 'docs/migrations/' para ser aplicada em conjunto com o deploy.
- Mantenha este documento atualizado com todas as mudanças.
- O servidor de produção usa Linux (Amazon Linux 2023) e scripts devem ser compatíveis.

### Última Atualização: 2026-02-20
**Migração 1:** Melhorias no RAG para Redução de Fallbacks ([detalhes](docs/migrations/20260214_140000_melhorias_rag_fallbacks.md))
- Thresholds RAG: RAG_MIN_SCORE=0.30, RAG_TOP_K=5
- CHUNK_OVERLAP aumentado para 150
- Busca híbrida por siglas independente
- Expansão de siglas na query implementada
- Sinônimos críticos adicionados
- Prompts do classifier e RAG melhorados

**Migração 2:** Cache de Perfis Meta (Instagram/Facebook) ([detalhes](docs/migrations/20260214_220000_meta_user_profiles_cache.md))
- Nova tabela `meta_user_profiles` para cache de perfis
- Busca de username na API da Meta **apenas durante escalation**
- TTL de 30 dias para atualização automática
- Email de escalation agora inclui @username e nome do perfil
- Fallback para ID numérico se API não disponível

**Migração 3:** Melhorias de Embedding para Semântica do RAG ([detalhes](docs/migrations/20260220_190000_melhorias_embedding_semantico.md))
- Overrides de modelo por provedor e override global (`EMBEDDING_MODEL_*`, `EMBEDDING_MODEL_OVERRIDE`)
- Embeddings via OpenRouter com batch/retry/timeout configuráveis
- Metadados de `embedding_provider` e `embedding_model` registrados em collection/chunks
- Auto-ingest do retriever ajustado para `data/knowledge_base/...` com fallback legado

## 1. Visão Geral do Projeto
**Nome**: {bot_name}
**Cliente**: Prefeitura de {client_name} - PR
**Objetivo**: Chatbot institucional para atendimento ao cidadão via Facebook e Instagram.
**Natureza**: Estritamente informativa. **Não realiza atos administrativos** (agendamentos, isenções, aprovações).
**Status Atual**: Fase 5 (Deploy & Observabilidade) **EM PROGRESSO** (16/01/2025). Fase 4 concluída com sucesso - testes reais via Facebook Messenger validados.

## 2. Diretrizes Éticas e Legais (Crucial)
*   **Caráter Informativo**: A IA atua como triadora e enciclopédia ativa.
    *   *Permitido*: Informar documentos necessários, horários, endereços, procedimentos.
    *   *Proibido*: Agendar consultas, processar isenções, prometer prazos não oficiais, emitir juízo de valor.
*   **Redirecionamento Assistido**: Se o usuário pede um serviço transacional (ex: "quero parcelar dívida"), a IA deve explicar a regra e fornecer o link/contato para o humano ou sistema responsável.
*   **Privacidade (LGPD)**:
    *   **Comentários Públicos**: Detectar e ocultar dados sensíveis. Instruir migração para Inbox.
    *   **Inbox**: Coleta mínima de dados.
*   **Humanização e Transparência**:
    *   Sempre se identificar como IA em treinamento.
    *   Usar Linguagem Simples (evitar "juridiquês").
    *   **Disclaimer Obrigatório**: "Informações baseadas na base oficial. Para decisões legais, consulte o Diário Oficial."

## 3. Protocolos de Segurança e Crise (Policy Guard)
A {bot_name} possui "gatilhos de segurança" que interrompem a geração via LLM e usam respostas estáticas seguras.

| Cenário | Ação do Agente | Contatos de Referência |
| :--- | :--- | :--- |
| **Saúde Mental / Risco à Vida** | Interromper fluxo. Mensagem empática e direta. | CVV (188), SAMU (192), Unidades de Saúde. |
| **Violência (Mulher/Criança/Idoso)** | Fornecer canais de denúncia/proteção. | Violência Mulher (180), Direitos Humanos (100), PM (190), Conselho Tutelar. |
| **Crise Institucional / Fake News** | Não engajar em polêmicas. | Redirecionar para notas oficiais. |
| **Ofensas / Trolls** | Não responder (NO_REPLY). | Notificar moderação humana. |

## 4. Arquitetura Técnica
*   **Modelo**: RAG (Retrieval-Augmented Generation).
*   **Pipeline**:
    1.  **Input**: Webhook FB/IG.
    2.  **Classifier**: Identifica intenção (Saúde, Tributos, etc.).
    3.  **Policy Guard (PRE)**: Filtra injeção de prompt, PII, ofensas.
    4.  **Retriever**: Busca chunks no ChromaDB (Base de Conhecimento).
    5.  **Composer (LLM)**: Gera resposta usando *apenas* o contexto recuperado e a pergunta.
    6.  **Policy Guard (POST)**: Valida se a resposta é segura e não alucinou conselhos médicos/legais.
    7.  **Output**: Resposta final auditada.
*   **Stack**: Python 3.11+, FastAPI, PostgreSQL (Auditoria), ChromaDB (Vetores), Google Gemini (LLM).

## 5. Matriz de Redirecionamento (Telefones Chave)
Quando o atendimento humano for necessário, utilizar estes contatos oficiais:

*   **Prefeitura (Geral)**: (45) 3124-1000 | Av. Paraná, 61
*   **Saúde (Central)**: (45) 3124-1020 | Av. Brasília, 525
*   **SAMU (Emergência)**: 192
*   **Educação**: (45) 3124-1010 | R. Internacional, 1597
*   **Assistência Social**: (45) 3124-1030 | Av. Brasília, 1050
*   **Conselho Tutelar**: (45) 3124-1035 (Plantão via PM 190)
*   **Meio Ambiente**: (45) 3124-1095
*   **Agência do Trabalhador**: (45) 3124-1000

## 6. Referências de Arquivos
*   `docs/estudo.md`: Detalhamento completo das regras de negócio, FAQs e protocolos. Fonte da verdade para comportamento.
*   `README.md`: Detalhes técnicos, setup, e status de desenvolvimento.
*   `app/policy_guard/service.py`: Implementação dos guardrails de segurança.
*   `app/rag/timestamp.py`: Utilitários para tratamento temporal e validação de datas.
*   `data/knowledge_base/BA-RAG-PILOTO-****`: Diretório contendo os documentos markdown ingeridos pelo RAG.
*   `docs/apoio_faq.md`: Material de apoio com FAQs detalhados por cluster (Educação, Saúde, Tributos).

## 7. Estrutura de Diretórios e Arquivos Principais

```
pilot-atendimento/
├── app/                          # Aplicação principal
│   ├── __init__.py
│   ├── main.py                   # FastAPI application entry point
│   ├── settings.py               # Configurações (BaseSettings)
│   ├── analytics.py              # Analytics e QueryAnalytics
│   ├── api/                      # Endpoints da API
│   │   ├── chat.py              # POST /api/chat, /api/chat/simple
│   │   ├── analytics.py         # Analytics endpoints
│   │   └── webhook.py           # Meta webhook endpoints
│   ├── contracts/                # Contratos de dados
│   │   ├── enums.py             # Enums: Intent, Decision, ResponseType, etc.
│   │   └── dto.py               # DTOs: ChatRequest, ChatResponse, RequestContext
│   ├── orchestrator/             # Orquestrador principal
│   │   └── service.py           # OrchestratorService (pipeline completo)
│   ├── classifier/               # Classificação de intenção
│   │   └── service.py           # ClassifierService (fast patterns + LLM)
│   ├── policy_guard/             # Guardrails de segurança
│   │   └── service.py           # PolicyGuardService (PRE e POST)
│   ├── rag/                      # Retrieval-Augmented Generation
│   │   ├── ingest.py            # MarkdownIngester
│   │   ├── retriever.py         # RAGRetriever (ChromaDB)
│   │   ├── composer.py         # RAGComposer (LLM generation)
│   │   └── timestamp.py        # Utilitários temporais
│   ├── nlp/                      # Processamento de linguagem natural
│   │   ├── sentiment.py         # Análise de sentimento
│   │   ├── normalizer.py        # Normalização de texto
│   │   ├── query_expander.py    # Expansão de queries
│   │   └── synonyms.py          # Sinônimos
│   ├── channels/                 # Canais de comunicação
│   │   ├── meta_sender.py       # Envio de mensagens Meta
│   │   └── meta_adapter.py      # Adaptação de eventos Meta
│   ├── integrations/             # Integrações externas
│   │   └── meta/
│   │       ├── webhook.py       # Webhook Meta handler
│   │       ├── security.py      # HMAC verification
│   │       └── client.py        # Meta Graph API client
│   ├── audit/                    # Auditoria
│   │   ├── models.py            # Modelos de auditoria
│   │   └── repository.py        # Repository PostgreSQL
│   └── prompts/                  # Sistema de prompts versionado
│       └── __init__.py          # load_prompt(), get_public_ack()
├── prompts/v1/                   # Templates de prompts
│   ├── manifest.json            # Metadados dos prompts
│   ├── system.txt               # System prompt principal
│   ├── classifier.txt           # Classifier prompt
│   ├── rag_answer.txt           # RAG composition prompt
│   ├── greeting.txt             # Saudação
│   ├── fallback.txt             # Fallback genérico
│   ├── fallback_private.txt    # Fallback inbox
│   ├── public_ack.txt           # ACK público
│   ├── public_redirect.txt      # Redirecionamento público
│   ├── escalate.txt             # Escalate para humano
│   ├── blocked.txt              # Resposta bloqueada
│   ├── ouvidoria_redirect.txt   # Redirecionamento ouvidoria
│   ├── crisis_suicide.txt       # Crise: suicídio
│   └── crisis_violence.txt      # Crise: violência
├── data/                        # Dados estáticos
│   └── knowledge_base/          # Base de conhecimento RAG
│       └── BA-RAG-PILOTO-2026.01.v1/
│           ├── manifest.json    # Metadados da base
│           └── items/           # Documentos markdown
│               ├── 0001_horarios.md
│               ├── ...
├── db/                          # Banco de dados
│   ├── schema.sql              # Schema PostgreSQL (audit_events, rag_queries)
│   └── 01_consultas.sql        # Consultas úteis
├── analytics/v1/                # Analytics e observabilidade
│   ├── views.sql               # Views PostgreSQL (latência, erros, fallbacks, crises, RAG)
│   ├── queries.sql             # Queries prontas para auditoria
│   └── queries.jsonl           # Queries em JSONL
├── scripts/                     # Scripts de desenvolvimento e operação
│   ├── ops/                    # Operações (deploy, backup, webhook)
│   │   ├── validate_infrastructure.py
│   │   ├── start_tunnel.py
│   │   ├── verify_meta_tokens.py
│   │   └── ...
│   ├── db/                     # Gerenciamento de Banco
│   │   ├── setup_db.py
│   │   └── create_views.py
│   ├── debug/                  # Scripts de Debug
│   │   ├── debug_rag_score.py
│   │   └── debug_chroma.py
│   └── ...                     # Scripts de repo/dev
├── tests/                       # Testes
│   ├── e2e/
│   │   └── test_pipeline_e2e.py  # Testes E2E do pipeline completo
│   └── __init__.py
├── docs/                        # Documentação
│   ├── estudo.md               # Estudo completo de regras de negócio
│   ├── apoio_faq.md            # FAQs detalhados por cluster
│   ├── observability.md        # Guia de KPIs, métricas e alertas
│   ├── infrastructure_validation.md  # Validação de infraestrutura
│   ├── db_setup.md             # Guia de setup do banco
│   ├── guia_tokens_meta.md     # Guia de tokens Meta
│   └── labels.md               # Labels para issues
├── artifacts/                   # Artefatos de desenvolvimento
│   ├── issues_mapping.csv      # Mapeamento de issues
│   └── anotacoes/              # Anotações de desenvolvimento
├── .env.example                 # Exemplo de variáveis de ambiente
├── .env                        # Variáveis de ambiente (NÃO commitado)
├── requirements.txt             # Dependências Python
├── README.md                    # Documentação principal
├── AGENTS.md                    # Este arquivo - contexto do agente
├── implementation_plan.md       # Plano de implementação
├── INFRASTRUCTURE_CHECKLIST.md  # Checklist de infraestrutura
└── agents.md                    # Alias para AGENTS.md
```

## 8. Arquitetura de Código e Serviços

### 8.1. Pipeline de Processamento (OrchestratorService)

O pipeline completo implementado em `app/orchestrator/service.py`:

1. **Análise NLP**:
   - Normalização de texto (`normalize_text()`)
   - Detecção de formalidade (`detect_formality_level()`)
   - Análise de sentimento (`analyze_sentiment()`)
   - Expansão de queries (`expand_query()`)

2. **Classificação** (ClassifierService):
   - Fast patterns para intents comuns
   - Fallback para LLM (Gemini)
   - Intents: GREETING, COMPLIMENT, INFO_REQUEST, SCHEDULE_QUERY, CONTACT_REQUEST, COMPLAINT, HUMAN_HANDOFF, OUT_OF_SCOPE

3. **Policy Guard PRE** (PolicyGuardService):
   - Detecção de prompt injection
   - Detecção de PII
   - Detecção de conteúdo ofensivo
   - Detecção de crise (suicídio, violência)
   - Detecção de saúde clínica
   - Validação de tamanho de mensagem
   - Decisões: ALLOW, ALLOW_LIMITED, REDIRECT, NO_REPLY, BLOCK

4. **Decisões Especiais**:
   - GREETING → resposta direta
   - COMPLIMENT em público → ACK (controle de não-repetição)
   - HUMAN_HANDOFF → escalate
   - NO_REPLY → silêncio
   - BLOCK → resposta de bloqueio/ouvidoria
   - CRISIS → resposta estática de acolhimento

5. **RAG**:
   - Retrieval (ChromaDB, top_k=7, min_score=0.35)
   - Composer (Google Gemini 2.0 Flash, temperature=0.3)
   - Query expandida com sinônimos

6. **Policy Guard POST**:
   - Valida se não há conselhos clínicos
   - Valida conteúdo gerado

7. **Resposta Final**:
   - RAG SUCCESS → resposta com sources
   - FALLBACK → direcionamento para prefeitura (inbox) ou silêncio (público)
   - ESCALATE → redirecionamento para humano

### 8.2. Contratos e DTOs

**Enums** (`app/contracts/enums.py`):
- `Intent`: GREETING, COMPLIMENT, INFO_REQUEST, SCHEDULE_QUERY, CONTACT_REQUEST, COMPLAINT, HUMAN_HANDOFF, OUT_OF_SCOPE
- `Decision`: ANSWER_RAG, ANSWER_DIRECT, PUBLIC_ACK, PUBLIC_REDIRECT, FALLBACK, ESCALATE, NO_REPLY, BLOCK
- `ResponseType`: SUCCESS, FALLBACK, BLOCKED, ESCALATED, NO_REPLY, ERROR
- `PolicyDecision`: ALLOW, ALLOW_LIMITED, REDIRECT, NO_REPLY, BLOCK
- `PolicyReason`: OK, OUT_OF_SCOPE, NO_DOCS_FOUND, HEALTH_CLINICAL_DETECTED, POLICY_BLOCKED, PROMPT_INJECTION, PII_DETECTED, OFFENSIVE_CONTENT, MESSAGE_TOO_LONG, CRISIS_SUICIDE, CRISIS_VIOLENCE
- `FallbackReason`: OUT_OF_SCOPE, LOW_CONFIDENCE, NO_DOCS_FOUND, POLICY_BLOCKED
- `Channel`: WEB_WIDGET, INSTAGRAM_DM, INSTAGRAM_COMMENT, FACEBOOK_DM, FACEBOOK_COMMENT
- `SurfaceType`: INBOX, PUBLIC_COMMENT, WEB
- `AuditEventType`: CLASSIFIER_RESULT, POLICY_PRE, POLICY_POST, RAG_RETRIEVE, RESPONSE_SELECTED, MESSAGE_SENT, PUBLIC_ACK

**DTOs** (`app/contracts/dto.py`):
- `ChatRequest`: Requisição de chat (session_id, message, channel, surface_type)
- `ChatResponse`: Resposta do chat (session_id, message, intent, decision, response_type, base_id, docs_found, fallback_used, sources, fallback_reason)
- `RequestContext`: Contexto completo acumulado através do pipeline
- `ClassifierResult`: Resultado da classificação (intent, confidence, raw_output)
- `PolicyPreResult`: Resultado da avaliação PRE (policy_decision, reason, allowed_content, details)
- `PolicyPostResult`: Resultado da avaliação POST (no_clinical_advice, content_validated, details)
- `RAGRetrieveResult`: Resultado da busca RAG (base_id, query_id, k, docs_count, docs_found, doc_ids, source_refs, best_score)

### 8.3. Serviços Principais

**ClassifierService** (`app/classifier/service.py`):
- Classifica intenção da mensagem
- Usa fast patterns para intents comuns
- Fallback para LLM (Gemini)

**PolicyGuardService** (`app/policy_guard/service.py`):
- `evaluate_pre()`: Avalia antes do processamento
- `evaluate_post()`: Valida resposta após RAG
- Detecção de padrões regex:
  - PROMPT_INJECTION_PATTERNS
  - PII_REQUEST_PATTERNS
  - OFFENSIVE_PATTERNS
  - HEALTH_CLINICAL_PATTERNS
  - CRISIS_SUICIDE_PATTERNS
  - CRISIS_VIOLENCE_PATTERNS
  - OUT_OF_SCOPE_PATTERNS

**RAGRetriever** (`app/rag/retriever.py`):
- Busca no ChromaDB com busca semântica (embeddings)
- Busca híbrida: quando siglas são detectadas na query, busca adicional por chunks contendo a sigla explicitamente
- Top-k retrieval com score filtering
- Boost de siglas: chunks contendo siglas da query recebem prioridade (score 0.9)

**Acronyms** (`app/rag/acronyms.py`):
- Mapeamento de 51+ siglas municipais (REFIS, IPTU, MEI, SUS, PSF, etc.)
- Extração de siglas da query do usuário
- Cálculo de boost baseado em match de siglas
- Case-insensitive, evita match parcial (ex: "ME" não casa com "como")

**RAGComposer** (`app/rag/composer.py`):
- Gera resposta via LLM
- Usa apenas contexto recuperado
- Aplica disclaimer obrigatório

**OrchestratorService** (`app/orchestrator/service.py`):
- Coordena todo o pipeline
- Gera eventos de auditoria
- Aplica regras de decisão por superfície

**MetaClient** (`app/integrations/meta/client.py`):
- Cliente para envio de mensagens via APIs da Meta
- **Instagram** (NOVA API): Usa `graph.instagram.com` com Instagram User Access Token
  - Endpoint: `POST /me/messages` ou `/{ig_id}/messages`
  - Token: `META_ACCESS_TOKEN_INSTAGRAM`
  - Não requer Facebook Page vinculada
  - Limite de 1000 caracteres por mensagem
  - Suporte a mensagens longas: divide automaticamente em múltiplas partes sem cortar palavras
  - Remove formatação Markdown automaticamente para compatibilidade
  - Documentação: https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/messaging-api/
- **Facebook** (Legado): Usa `graph.facebook.com` com Page Access Token
  - Endpoint: `POST /me/messages`
  - Token: `META_ACCESS_TOKEN_FACEBOOK`
  - Requer Facebook Page
  - Documentação: https://developers.facebook.com/docs/messenger-platform/

**Funções Auxiliares** (`app/integrations/meta/client.py`):
- `strip_markdown()`: Remove formatação Markdown (**negrito**, *itálico*, `código`, listas)
- `split_message()`: Divide mensagens longas em partes menores sem cortar palavras

## 9. Configurações e Variáveis de Ambiente

**Configurações** (`app/settings.py`):

```python
APP_NAME: str = "Pilot Atendimento API"
ENV: str = "dev"
VERSION: str = "0.0.1"
DEBUG: bool = False
BASE_DIR: str = "."
APP_HOST: str = "0.0.0.0"
APP_PORT: int = 8000

# LLM - Google Gemini
GEMINI_API_KEY: str = ""
GEMINI_MODEL: str = "gemini-2.0-flash"
GEMINI_MAX_TOKENS: int = 1024
GEMINI_TEMPERATURE: float = 0.3

# Database - PostgreSQL
DATABASE_URL: str = "postgresql://localhost:5432/pilot_atendimento"
DATABASE_POOL_SIZE: int = 5
DATABASE_MAX_OVERFLOW: int = 10
USER_HASH_SALT: str = ""

# Vector Store - ChromaDB
CHROMA_PERSIST_DIR: str = "./chroma_data"

# RAG
RAG_BASE_ID: str = "BA-RAG-PILOTO-2026.01.v1"
RAG_COLLECTION_NAME: str = "rag_ba_rag_piloto_2026_01_v1"
RAG_TOP_K: int = 5
RAG_MIN_SCORE: float = 0.30

# Embeddings (RAG semântico)
EMBEDDING_PROVIDER: str = "default"
OPENROUTER_API_KEY: str = ""
EMBEDDING_MODEL_OVERRIDE: str = ""
EMBEDDING_MODEL_GEMINI: str = "google/gemini-embedding-001"
EMBEDDING_MODEL_OPENAI: str = "openai/text-embedding-3-large"
EMBEDDING_MODEL_QWEN: str = "qwen/qwen3-embedding-8b"
EMBEDDING_BATCH_SIZE: int = 32
EMBEDDING_REQUEST_TIMEOUT_SECONDS: float = 60.0
EMBEDDING_MAX_RETRIES: int = 3

# Policy Guard
POLICY_MAX_MESSAGE_LENGTH: int = 2000
POLICY_BLOCKED_PATTERNS: str
POLICY_PUBLIC_COMMENT_MAX_LENGTH: int = 280

# Logging / Observability
LOG_LEVEL: str = "INFO"
LOG_JSON: bool = True
METRICS_STATSD_ENABLED: bool = False
METRICS_STATSD_HOST: str = "127.0.0.1"
METRICS_STATSD_PORT: int = 8125
METRICS_STATSD_PREFIX: str = "terezia"

# Meta API (Instagram/Facebook)
# Access Tokens
META_ACCESS_TOKEN_INSTAGRAM: str = ""
META_ACCESS_TOKEN_FACEBOOK: str = ""
# Page IDs
META_PAGE_ID_FACEBOOK: str = ""
META_PAGE_ID_INSTAGRAM: str = ""  # Instagram Business Account ID
# App Secrets (para verificação de webhook)
META_APP_SECRET_FACEBOOK: str = ""
META_APP_SECRET_INSTAGRAM: str = ""
# Legacy (retrocompatibilidade - usar apenas se as novas não estiverem configuradas)
META_PAGE_ID: str = ""
META_APP_SECRET: str = ""
# Webhook Verify Token
META_WEBHOOK_VERIFY_TOKEN: str = "verify_token_webhook"
META_WEBHOOK_VERIFY_TOKEN_FACEBOOK: str = ""
META_WEBHOOK_VERIFY_TOKEN_INSTAGRAM: str = ""
META_API_VERSION: str = "v19.0"

# Response Formatting
RESPONSE_MODE_INBOX_MAX_LENGTH: int = 1000
RESPONSE_MODE_PUBLIC_MAX_LENGTH: int = 280

# Security - CORS e Rate Limiting
CORS_ORIGINS: list[str] = ["*"]
RATE_LIMIT_ENABLED: bool = True
RATE_LIMIT_PER_MINUTE: int = 30
RATE_LIMIT_WEBHOOK_PER_MINUTE: int = 60

# Secrets Manager (AWS)
USE_SECRETS_MANAGER: bool = False
AWS_REGION: str = "sa-east-1"
AWS_SECRET_NAME: str = "terezia/prod"

# Admin API
ADMIN_API_KEY: str = ""
```

## 10. Scripts e Ferramentas de Desenvolvimento

**Validação de Infraestrutura**:
- `scripts/ops/validate_infrastructure.py`: Valida todas as variáveis de ambiente, conexões com banco, ChromaDB, tokens Meta

**Setup do Banco**:
- `scripts/db/setup_db.py`: Setup via Python usando DATABASE_URL
- `scripts/db/setup_db.ps1`: Setup via PowerShell
- Schema definido no AGENTS.md (tabelas: audit_events, rag_queries, usuarios_anonimos, conversas)

**Configuração do Grafana**:
- `scripts/setup_grafana.py`: Configura automaticamente o Grafana com PostgreSQL local
- `scripts/grafana/README.md`: Guia de configuração manual

**Serviços Systemd**:
- `scripts/systemd/terezia-api.service`: Serviço systemd para a API
- `scripts/systemd/terezia-grafana.service`: Serviço systemd para o Grafana
- `scripts/systemd/setup_systemd.sh`: Script para configurar serviços systemd
- `scripts/systemd/README.md`: Documentação dos serviços systemd

**Webhook Meta**:
- `scripts/ops/start_tunnel.py`: Inicia túnel local (ngrok)
- `scripts/ops/test_webhook_local.py`: Testa webhook localmente
- `scripts/ops/simulate_webhook.py`: Simula requisição webhook
- `scripts/ops/check_token.py`: Verifica tokens Meta
- `scripts/debug/debug_verify.py`: Debug verificação webhook
- `scripts/ops/verify_meta_tokens.py`: Diagnóstico completo de credenciais Meta

**Fallback Híbrido e Auto-Update**:
- `scripts/e2e_sequence.py`: Teste E2E interativo do fluxo `RAG -> Scraper -> Escalation` e verificação manual do Drive (`check_for_updates`) com resumo de arquivos vistos/atualizados e quantidade de subpastas varridas.
- `scripts/verify_features.py`: Smoke test de conectividade para SMTP, Google Drive (com suporte a Shared Drive) e Web Scraper.

**Embeddings e A/B**:
- `scripts/run_embedding_ab_test.py`: Benchmark comparativo entre provedores/modelos de embedding (score, hit rate e latência).

**Analytics**:
- `scripts/db/executar_views.py`: Executa views.sql no PostgreSQL
- `scripts/db/create_views.py`: Cria views no PostgreSQL
- `analytics/v1/views.sql`: Views de observabilidade (latência, erros, fallbacks, crises, RAG)
- `analytics/v1/queries.sql`: Queries prontas para auditoria

## 11. Base de Conhecimento RAG

**Estrutura** (`data/knowledge_base/BA-RAG-PILOTO-2026.01.v1/`):
- `manifest.json`: Metadados da base
- `items/`: Documentos markdown ingeridos

**Documentos**:
- `0001_horarios.md`: Horários de atendimento, secretarias, ônibus
- `0002_contatos.md`: Matriz de redirecionamento, telefones, endereços
- `0003_secretarias.md`: Descrição das secretarias e responsabilidades
- `0004_saude.md`: Unidades de saúde, PSFs, horários, contatos
- `0005_empreendedor.md`: Agência do Trabalhador, MEI, serviços
- `0006_info_geral.md`: Informações gerais e serviços diversos
- `0006_tributacao.md`: IPTU 2025, REFIS, Nota Fiscal
- `0007_assistencia_social.md`: CRAS, Conselho Tutelar, Auxílios
- `0008_educacao.md`: Matrículas 2026, escolas, transporte
- `0009_emergencias_desastres.md`: Emergências, desastres e orientações
- `0010_zeladoria_infraestrutura.md`: Zeladoria, obras e infraestrutura urbana
- `0011_protocolos_governanca.md`: Protocolos, governança e fluxos oficiais

**Ingestão**:
- `app/rag/ingest.py`: MarkdownIngester - parse e ingestão de documentos
- ChromaDB: Armazenamento vetorial (chroma_data/)

## 12. Testes e Validação

**Testes E2E** (`tests/e2e/test_pipeline_e2e.py`):
- Testes do pipeline completo
- Validação de cada etapa
- Testes de crise (suicídio, violência)
- Testes de redirecionamento

**Testes de Siglas** (`tests/test_acronyms.py`):
- Testes de extração de siglas da query
- Testes de cálculo de boost baseado em match
- Testes case-insensitive
- Testes de busca híbrida (semântica + por sigla)

**Testes de Embedding** (`tests/test_embedding_ab.py`):
- Testes unitários da factory de embeddings e resolução de modelo
- Testes de batch/retry para `OpenRouterEmbeddingFunction`
- Testes de integração opcionais para comparar semântica entre provedores

**Smoke Tests** (checklist de produção):
- Qual o telefone da prefeitura?
- Qual o horário de atendimento do posto de saúde?
- Quais documentos preciso para matrícula escolar?
- Como faço para emitir a segunda via do IPTU?
- Quero agendar uma consulta médica (redirecionamento)
- Quero parcelar minha dívida de IPTU (redirecionamento)
- Quero me matar (crise)
- Estou sofrendo violência doméstica (crise)
- Qual a capital da França? (fora de escopo)
- Me conte uma piada (fora de escopo)

## 13. Padrões de Código e Convenções

**Python**:
- Python 3.11+
- Type hints obrigatórios em assinaturas de funções
- Pydantic para validação de dados
- Async/await para I/O bound operations
- Docstrings em formato reStructuredText

**FastAPI**:
- Routers modularizados por domínio
- OpenAPI/Swagger em `/docs`
- CORS habilitado para desenvolvimento
- Prometheus instrumentação

**Banco de Dados**:
- PostgreSQL 15+
- Enum types para campos categoricos
- UUIDs para identificadores
- Timestamptz para timestamps
- Índices para queries comuns
- Cascading deletes para integridade referencial

**Logging**:
- Logs estruturados (planejado)
- Eventos de auditoria em cada etapa do pipeline
- Logs detalhados para debugging de webhooks

**Versionamento**:
- Sistema de prompts versionado (prompts/v1/)
- Base de conhecimento versionada (BA-RAG-PILOTO-2026.01.v1)
- Schema do banco versionado (v1.1)
- **Versão piloto congelada (v1.0)**: Contratos, enums e prompts bloqueados para manter estabilidade durante os testes

**Segurança**:
- HMAC-SHA256 verification para webhooks Meta
- Env variables em .env (NÃO commitado)
- .env.example como template
- Policy guard em duas fases (PRE e POST)
- Detecção de PII e prompt injection

**Documentação Viva**:
- **README.md**: Deve ser mantido **sempre atualizado** refletindo fielmente o estado atual, fases concluídas, changelog e estrutura do projeto. Deve ser a primeira referência para quem chega no repositório.
- **AGENTS.md**: Fonte da verdade para contexto e regras de negócio.

## 14. Comandos de Desenvolvimento

### Configuração Inicial
```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual (Windows)
venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Copiar template de ambiente
copy .env.example .env
# Editar .env com sua configuração (incluir tokens Meta API)
```

### Executando a Aplicação
```bash
# Servidor de desenvolvimento com auto-reload
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Ou usando o módulo principal
python app/main.py
```

### Banco de Dados
```bash
# Aplicar schema (manual por enquanto)
psql -d pilot_atendimento -f db/schema.sql

# Setup via Python
python scripts/db/setup_db.py --database-url postgresql://user:pwd@host:5432/db

# Setup via PowerShell
scripts\db\setup_db.ps1 -Host <host> -Port 5432 -User <user> -Password <pwd> -DbName <db>
```

### Validação e Testes
```bash
# Validar infraestrutura completa
python scripts/ops/validate_infrastructure.py

# Configurar Grafana (após iniciar com docker-compose)
python scripts/setup_grafana.py

# Configurar serviços systemd (inicialização automática)
sudo bash scripts/systemd/setup_systemd.sh

# Teste webhook local
python scripts/ops/test_webhook_local.py

# Simular requisição webhook
python scripts/ops/simulate_webhook.py

# Verificar tokens Meta
python scripts/ops/verify_meta_tokens.py

# Executar testes E2E
pytest tests/e2e/test_pipeline_e2e.py

# Executar testes unitários de embeddings
pytest tests/test_embedding_ab.py -v

# Benchmark A/B de embeddings
python scripts/run_embedding_ab_test.py --providers default,openai --verbose
```

### Analytics
```bash
# Executar views.sql no PostgreSQL
python scripts/db/executar_views.py

# Criar views no PostgreSQL
python scripts/db/create_views.py
```

### Túnel Local (ngrok)
```bash
# Iniciar túnel local para testar webhooks
python scripts/ops/start_tunnel.py
```

## 15. Stack Tecnológico Detalhado

### Framework Principal
- **FastAPI**: Framework Python moderno para construção de APIs
- **Pydantic**: Validação de dados e gerenciamento de configurações usando type annotations do Python
- **Uvicorn**: Servidor ASGI para executar a aplicação FastAPI

### Componentes da Arquitetura
- **Integração LLM**: Google Gemini 2.0 Flash para processamento de linguagem natural
- **Banco de Dados Vetorial**: ChromaDB para armazenamento de documentos RAG (Retrieval-Augmented Generation)
- **Banco de Dados**: PostgreSQL 15+ para logs de auditoria e dados estruturados
- **APIs Externas**: Meta API para Instagram e Facebook (DMs e comentários)
- **Sistema de Prompts**: Prompts versionados em arquivos de texto com manifest JSON
- **Configuração**: Configurações baseadas em ambiente com suporte a arquivo `.env`

### Integração com Meta
- Webhooks para receber mensagens do Instagram e Facebook
- Parsing unificado de DMs e comentários através do `meta_adapter`
- Envio de respostas via `meta_sender`
- Suporte a diferentes tipos de superfície (privado/público)

## 16. Notas de Produto

### Propósito Central
- Fornece atendimento automatizado aos cidadãos através de múltiplos canais digitais
- Trata consultas sobre horários de funcionamento, contatos de setores e informações públicas
- Escala consultas complexas para atendimento humano quando necessário
- Opera como **{bot_name}**, assistente virtual institucional da prefeitura

### Canais Suportados
- **Web Widget**: Chat no site da prefeitura
- **Instagram**: DMs e comentários em posts
- **Facebook**: DMs e comentários em posts
- **Superfícies**: Inbox privado e comentários públicos

### Funcionalidades Principais
- **Classificação de Intenção**: Categoriza mensagens (saudações, elogios, solicitações de informação, consultas de horário, contatos, transferência humana, fora de escopo)
- **Sistema RAG**: Recupera informações da base de conhecimento autorizada
- **Policy Guard**: Filtra conteúdo inadequado e aplica limites por tipo de superfície
- **Trilha de Auditoria**: Log completo de todas as interações para conformidade
- **Respostas Contextuais**: Adapta formato e tamanho conforme canal (inbox vs comentário público)
- **Sistema de Prompts**: Prompts versionados e congelados para consistência

### Domínio
Atendimento digital institucional para cidadãos de {client_name}, com foco em informações públicas, orientação e encaminhamento.

### Status
Versão piloto congelada (v1.0) com contratos, enums e prompts bloqueados para manter estabilidade durante os testes.

---
*Este arquivo deve ser consultado pelo agente antes de planejar modificações ou novas features para garantir alinhamento com as regras de negócio e restrições legais.*

**Guia rápido de referência**: Consulte `docs/QUICKSTART_AGENT.md` para acesso rápido às informações mais importantes.*
