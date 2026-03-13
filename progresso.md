# Controle de Progresso - Nexo Basis White-Label SaaS

**Projeto:** Chatbot Governador (White-label SaaS)
**Arquiteto/PM:** Kiro

## Estado Atual
- **Fase Atual:** 🚧 FASE 5 — Elevação Comercial (Demo / GTM)
- **Último Marco Atingido:** Fase 4 completa. Criação do plano `gtm-elevation-plan.md` para as "Killer Features" de mercado.

## Resumo das Fases Entregues

| Fase | Status | Principais Entregas |
|------|--------|---------------------|
| **1** — Infra | ✅ | `docker-compose.yml` → `nexo-gov-api:8101`, `infra_nexo-network` |
| **2** — Multi-Tenant DB | ✅ | Migration RLS, `tenant_context.py`, ChromaDB `{tenant_id}_knowledge_base` |
| **3** — Camada Lógica | ✅ | Webhook router com HMAC-SHA256, `TenantResolver` (LRU+DB), `TenantConfig`, `get_tenant_prompt()` |
| **4** — Pipeline/Ops | ✅ | `rag_etl_job.py` (cron multi-tenant), `setup_demo_tenant.py` (GTM), logs com `tenant_id` |
| **5** — Comerc./GTM | 🚧 | Plano de Elevação `gtm-elevation-plan.md` gerado. Mocks de features matadoras. |

## Novos Arquivos Criados

```
app/
├── tenant_context.py          # contextvars: set/get/require_tenant
├── tenant_resolver.py         # LRU cache + DB: page_id → tenant_id
├── tenant_config.py           # TenantConfig: perfil + tokens Meta do banco
├── logging_config.py          # JsonFormatter com tenant_id automático
├── channels/meta_sender.py    # _get_access_token() async e DB-first
├── prompts/__init__.py        # get_tenant_prompt() com vars do tenant
├── api/webhook.py             # Router HMAC-SHA256, isolamento por tenant
db/migrations/
├── 001_multi_tenant_rls.sql   # tenant_id, RLS policies
├── 002_tenant_identity_and_credentials.sql  # bot_name, tokens Meta, rag_base_path
scripts/
├── rag_etl_job.py             # ETL incremental multi-tenant (CLI + cron)
├── setup_demo_tenant.py       # Seed GTM: "Prefeitura de Nova Esperança"
```

## Comandos de Operação

```bash
# Setup demo tenant (GTM/vendas)
python scripts/setup_demo_tenant.py

# ETL RAG (todos os tenants)
python scripts/rag_etl_job.py

# ETL forçado para um tenant específico
python scripts/rag_etl_job.py --force --tenant prefeitura_nova_esperanca

# Migrations no banco
psql $DATABASE_URL -f db/migrations/001_multi_tenant_rls.sql
psql $DATABASE_URL -f db/migrations/002_tenant_identity_and_credentials.sql
```

## Histórico de Handoffs
- **[2026-03-05]** Sessão de Planejamento Inicial: Pilares (Design, Requisitos, Tasks) criados em `white-label-project/`.
- **[2026-03-05]** Sessão Fase 1 e 2: Branch `infra-rede` — Docker, .env, RLS, ChromaDB per-tenant.
- **[2026-03-05]** Sessão Fase 3: Branch `camada-logica` — Webhook router, TenantResolver, TenantConfig, prompts dinâmicos, MetaSender async.
- **[2026-03-05]** Sessão Fase 4: Branch `limpeza-pipeline` — ETL job, demo tenant seed, logs com tenant_id, ALLOWED_HOSTS.
