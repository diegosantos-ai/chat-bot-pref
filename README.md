# Nexo Basis Governador — White-Label SaaS de Chatbot Municipal

Plataforma **multi-tenant** de atendimento ao cidadão via Instagram e Facebook, projetada para prefeituras brasileiras. Cada cliente (prefeitura) opera em isolamento completo de dados, com base de conhecimento própria (RAG) e identidade visual customizada.

Caráter estritamente informativo: não agenda consultas, não concede isenções, não toma decisões administrativas. O assistente sempre se identifica como IA.

---

## Status do Projeto

| Fase | Descrição | Status | Conclusão |
|------|-----------|--------|-----------|
| **Fase 1** | Adequação de Infraestrutura & Networking Compartilhado | ✅ Completa | 05/03/2026 |
| **Fase 2** | Fundação Multi-Tenant (RLS PostgreSQL + Collections ChromaDB) | ✅ Completa | 05/03/2026 |
| **Fase 3** | Middleware de Roteamento de Tenant (Webhook Router) | 🔄 Em andamento | — |
| **Fase 4** | Operação, Automação RAG & Demo Tenant | ⏳ Pendente | — |

---

## Arquitetura

O sistema opera como **um contêiner** conectado à rede compartilhada `infra_nexo-network`, sem hospedar bancos de dados próprios.

```
Cidadão (Meta IG/FB)
        │
        ▼
  Traefik (Ingress / TLS)      ← infra/ compartilhado
        │
        ▼
 nexo-gov-api :8101             ← este repositório
   ├── TenantMiddleware          (resolve Page ID → tenant_id via contextvars)
   ├── FastAPI Webhook Router    (POST /webhook/meta)
   ├── RAGRetriever              ({tenant_id}_knowledge_base)
   └── AuditRepository          (SET LOCAL app.tenant_id → RLS ativa)
        │                 │
        ▼                 ▼
  nexo-postgres:5432   nexo-chromadb:8000   ← infra/ compartilhado (RLS)
```

### Estratégia Multi-Tenant
- **PostgreSQL**: Row-Level Security via `SET LOCAL app.tenant_id`. Nenhuma query vaza dados entre prefeituras.
- **ChromaDB**: Collections isoladas por tenant (`{tenant_id}_knowledge_base`). Drop da collection = direito ao esquecimento (LGPD).
- **FastAPI**: `contextvars` propaga o `tenant_id` sem passar em cada função.

---

## Stack

| Camada | Tecnologia |
|--------|-----------|
| **API** | Python 3.11+, FastAPI, Pydantic, Uvicorn |
| **LLM** | Google Gemini 2.0 Flash (via `GEMINI_API_KEY`) |
| **Vector Store** | ChromaDB (HTTP Client → `nexo-chromadb`) |
| **Banco** | PostgreSQL 15+ com RLS (→ `nexo-postgres`) |
| **Cache** | Redis (→ `nexo-redis`) |
| **Proxy / TLS** | Traefik (gerenciado pela `infra/`) |
| **Container** | Docker (porta host: `8101`) |

---

## Quickstart (Dev Local)

> **Pré-requisito:** A rede `infra_nexo-network` deve estar ativa (`docker network ls`). Consulte o repositório `infra/` para subir os serviços compartilhados.

### 1. Ambiente
```bash
cp .env.example .env
# Preencha: GEMINI_API_KEY, DATABASE_URL (→ nexo-postgres), CHROMA_URL, REDIS_URL
```

### 2. Dependências
```bash
pip install -r requirements.txt
```

### 3. Banco de Dados
```bash
# Schema base (se banco novo)
psql -f db/schema.sql

# Migration multi-tenant (RLS)
psql -f db/migrations/001_multi_tenant_rls.sql
```

### 4. Rodar API
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Docker (produção)
```bash
docker-compose up -d --build
# API disponível em localhost:8101
```

---

## Variáveis de Ambiente Essenciais

| Variável | Descrição |
|----------|-----------|
| `GEMINI_API_KEY` | Chave Google Gemini |
| `DATABASE_URL` | `postgresql://user:pass@nexo-postgres:5432/core_saas_gov` |
| `CHROMA_URL` | `http://nexo-chromadb:8000` |
| `REDIS_URL` | `redis://nexo-redis:6379` |
| `EMBEDDING_PROVIDER` | `default` \| `openai` \| `gemini` \| `qwen` |
| `OPENROUTER_API_KEY` | Necessário para providers externos |

---

## Endpoints Principais

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/health` | Health check |
| `POST` | `/webhook/meta` | Entrada de eventos Instagram/Facebook |
| `POST` | `/api/chat` | Chat direto (web widget) |
| `GET` | `/analytics/summary` | Dashboard de auditoria |
| `GET` | `/metrics` | Prometheus metrics |

---

## Arquivos de Especificação

| Arquivo | Descrição |
|---------|-----------|
| `white-label-project/design.md` | Arquitetura alvo e diagramas de fluxo |
| `white-label-project/requirements.md` | Requisitos funcionais e não-funcionais |
| `white-label-project/task.md` | Plano de implementação faseado |
| `progresso.md` | Rastreamento de sessões e marcos |
| `PORTS.md` | Registro de alocação de portas da stack |
| `GUIA_INFRA.md` | Guia de integração com a infra compartilhada |
| `docs/deploy_guide.md` | Guia de deploy em VPS |
| `docs/runbook.md` | Operação e resolução de incidentes |

---

## Estrutura de Diretórios

```
├── app/
│   ├── api/              # Routers FastAPI
│   ├── audit/            # Repository asyncpg (RLS-aware)
│   ├── rag/              # Retriever, Ingest, Embeddings
│   ├── tenant_context.py # contextvars para isolamento de tenant
│   └── settings.py       # Configurações (pydantic-settings)
├── db/
│   ├── schema.sql        # Schema base
│   └── migrations/       # Migrations versionadas
│       └── 001_multi_tenant_rls.sql
├── data/knowledge_base/  # Bases RAG (por tenant)
├── white-label-project/  # Especificações do produto
└── docker-compose.yml    # Apenas nexo-gov-api (sem DBs locais)
```

---

## Changelog

### v2.0.0 (05/03/2026) — Refatoração SaaS Multi-Tenant
- Arquitetura migrada de monolítico single-tenant para **multi-tenant isolado**.
- PostgreSQL com **Row-Level Security** (`001_multi_tenant_rls.sql`) e tabela `tenants`.
- ChromaDB migrado de `PersistentClient` local para **HttpClient** centralizado (`nexo-chromadb`).
- Novo módulo `app/tenant_context.py` com `contextvars` para propagação assíncrona de tenant.
- `audit/repository.py`: injeção automática de `SET LOCAL app.tenant_id` em cada conexão.
- `rag/retriever.py`: collections dinâmicas por tenant (`{tenant_id}_knowledge_base`).
- `docker-compose.yml`: removido Caddy e Grafana; API conectada à `infra_nexo-network` na porta `8101`.

### v0.7.2 (20/02/2026) — Embeddings Semânticos (OpenRouter)
- Robustez com batch, retry/backoff e timeout configuráveis.
- Seleção de modelo por provedor e override global via env vars.

### v0.7.0 (03/02/2026) — Schema DB & Analytics
- Schema completo em `db/schema.sql` com tipos ENUM e índices.
- Queries e views SQL (`analytics/v1/`).
- Anonimização LGPD com `usuarios_anonimos`.

### v0.4.0 (15/01/2026) — Integração Meta API
- Webhook unificado `POST /webhook/meta` com verificação de assinatura HMAC.
- Pipeline completo validado: Webhook → Classifier → RAG → Resposta → Auditoria.

---

## Compliance & Segurança

- **LGPD**: Coleta mínima. Direito ao Esquecimento via `DROP COLLECTION` por tenant.
- **RLS**: Isolamento de dados garantido na camada de banco, independente do app.
- **Policy Guard**: Protocolos de crise (suicídio/violência) com respostas estáticas.
- **Disclaimer**: Obrigatório em todas as respostas. O assistente se identifica como IA.

---

## Licença

Projeto Nexo Basis — Uso interno. © 2026