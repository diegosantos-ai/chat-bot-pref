# Arquitetura do Projeto

## 1. Visao geral

Este documento descreve a arquitetura real da base ativa do Chat Pref.

O `README.md` continua mantendo a stack-alvo do case. Aqui, a prioridade e registrar:

- o runtime ativo hoje
- os contratos ja validados
- o que ainda e apenas evolucao planejada

## 2. Runtime ativo hoje

O runtime ativo e um backend FastAPI minimo, com foco em:

- contrato explicito de `tenant_id`
- contexto de tenant por request
- composicao generativa minima controlada
- prompts e politica textual versionados
- `policy_pre` e `policy_post`
- persistencia local em arquivo
- auditoria versionada por tenant
- logs estruturados correlacionados por `request_id`
- metricas minimas expostas em `/metrics`
- traces OpenTelemetry persistidos por `request_id`
- retrieval tenant-aware em Chroma
- tenant demonstrativo versionado
- execucao local e via Docker
- deploy remoto minimo validado em AWS com EC2 unica provisionada por Terraform

Rotas ativas no `app/main.py`:

- `GET /`
- `GET /health`
- `POST /api/chat`
- `POST /api/webhook`
- `POST /api/telegram/webhook`
- `GET /metrics`
- `GET /api/rag/status`
- `POST /api/rag/documents`
- `POST /api/rag/ingest`
- `POST /api/rag/query`
- `POST /api/rag/reset`

Topologia remota validada na Fase 13:

- `infra/terraform/aws/minimal` provisiona VPC, subnet publica, Internet Gateway, route table, Security Group, role SSM, EC2 e Elastic IP
- `user_data` instala Docker, Compose, Git e Python 3
- `scripts/deploy_aws_instance.sh` sincroniza a branch, sobe `docker compose` e executa o bootstrap do tenant demonstrativo
- `scripts/smoke_remote.py` valida `/`, `/health`, `/metrics` e `POST /api/chat` a partir da URL publica do ambiente

## 3. Componentes ativos do backend

| Componente | Papel atual |
| --- | --- |
| `app/main.py` | bootstrap do FastAPI e registro dos routers ativos |
| `app/api/chat.py` | entrada HTTP do chat direto com `tenant_id` explicito |
| `app/api/webhook.py` | entrada HTTP do webhook minimo com resolucao controlada de tenant |
| `app/api/telegram.py` | webhook demonstrativo do Telegram com validacao de secret e reaproveitamento do chat |
| `app/api/metrics.py` | exposicao de metricas Prometheus do runtime atual |
| `app/api/rag.py` | operacoes de documentos, ingest, query, status e reset do RAG |
| `app/api/health.py` | endpoints de raiz e healthcheck |
| `app/observability/` | middleware, contexto, logs, metricas e traces correlacionados |
| `app/services/chat_service.py` | fluxo principal atual com retrieval, composicao, guardrails e auditoria |
| `app/services/telegram_service.py` | resolucao do tenant no canal Telegram, envio de resposta e auditoria correlacionada |
| `app/services/llm_service.py` | adaptador LLM e composicao controlada com provedores `mock` e `gemini` |
| `app/services/prompt_service.py` | carregamento e renderizacao de prompts e politica textual versionados |
| `app/services/rag_service.py` | operacoes do RAG por tenant |
| `app/services/demo_tenant_service.py` | validacao e bootstrap do tenant demonstrativo |
| `app/services/tenant_profile_service.py` | perfil institucional do tenant para composicao e fallback |
| `app/policy_guard/service.py` | `policy_pre`, `policy_post` e emissao de `PolicyDecision` |
| `app/tenant_context.py` | injecao, leitura e limpeza do tenant no fluxo por request |
| `app/tenant_resolver.py` | resolucao de tenant em fluxos externos simples |
| `app/storage/chat_repository.py` | historico de conversa em arquivo por tenant |
| `app/storage/audit_repository.py` | auditoria `audit.v1` em arquivo por tenant |
| `app/storage/document_repository.py` | persistencia de documentos da base RAG por tenant |
| `app/storage/chroma_repository.py` | collections e retrieval no Chroma segregados por tenant |

## 4. Fluxo ativo atual

### Chat direto

1. `POST /api/chat` recebe `tenant_id` e `message`
2. o endpoint aceita `X-Request-ID` opcional
3. o endpoint injeta `tenant_id` no `tenant_context`
4. `ChatService` confirma o tenant ativo
5. o fluxo normaliza `request_id` e `session_id`
6. o request e auditado em `audit.v1`
7. `policy_pre` decide entre seguir, bloquear ou preparar fallback
8. o `RagService` consulta a collection do tenant ou o retrieval e pulado
9. `LLMComposeService` compoe resposta ou fallback usando prompt versionado
10. `policy_post` valida a resposta candidata e pode reescrever para fallback
11. a resposta e devolvida ao cliente com `X-Request-ID`
12. historico e auditoria sao persistidos em arquivo

### Webhook minimo

1. `POST /api/webhook` recebe `tenant_id` explicito ou `page_id`
2. o tenant e resolvido de forma controlada
3. o endpoint injeta o tenant no contexto
4. o endpoint aceita `X-Request-ID` opcional
5. o fluxo reaproveita o mesmo `ChatService`
6. a resposta volta em HTTP com o mesmo contrato funcional do chat

### Telegram demonstrativo

1. `POST /api/telegram/webhook` recebe um update do Telegram
2. o endpoint valida o secret do webhook quando configurado
3. o tenant e resolvido por `TELEGRAM_DEFAULT_TENANT_ID` ou `TELEGRAM_CHAT_TENANT_MAP`
4. o fluxo reaproveita o mesmo `ChatService` do chat direto com `channel="telegram"`
5. a resposta e entregue por cliente Telegram em modo `api`, `dry_run` ou `disabled`
6. a auditoria registra `telegram_update_received`, os eventos do fluxo de chat e `telegram_message_delivery`

## 5. Persistencia ativa

### Historico de conversa

- repositorio ativo: `app/storage/chat_repository.py`
- formato: JSONL
- segregacao: `data/runtime/<tenant_id>/<session_id>.jsonl`

### Auditoria

- repositorio ativo: `app/storage/audit_repository.py`
- formato: JSONL
- segregacao: `data/runtime/audit/<tenant_id>/<session_id>.jsonl`
- schema ativo hoje: `AuditEventRecord` em `audit.v1`

Campos atuais do `AuditEventRecord`:

- `schema_version`
- `event_id`
- `request_id`
- `tenant_id`
- `session_id`
- `channel`
- `event_type`
- `policy_decision`
- `payload`
- `created_at`

### Base documental e retrieval

- documentos persistidos por tenant
- collections do Chroma separadas por tenant
- o chat usa a collection do tenant ativo
- historico de conversa nao e promovido automaticamente para base RAG

## 6. Contratos arquiteturais ativos

- `tenant_id` e obrigatorio nos fluxos criticos
- ausencia de tenant gera erro controlado
- `request_id` pode ser recebido de fora em HTTP e e devolvido na resposta
- webhook nao usa tenant default silencioso
- Telegram nao usa tenant silencioso fora de `TELEGRAM_DEFAULT_TENANT_ID` ou `TELEGRAM_CHAT_TENANT_MAP`
- `PolicyDecision` e emitido em `policy_pre` e `policy_post`
- prompt base, prompt de fallback e politica textual sao versionados
- persistencia e retrieval devem respeitar segregacao por tenant
- `request_id`, `tenant_id`, `session_id` e `channel` formam a correlacao minima do pipeline ativo
- auditoria, logs estruturados e traces devem compartilhar os mesmos IDs de correlacao
- o runtime atual continua usando persistencia local em arquivo

## 7. Componentes fora do runtime ativo atual

Os itens abaixo podem existir como narrativa do case, artefato antigo ou objetivo futuro, mas nao fazem parte do runtime minimo validado hoje:

- `app/orchestrator/service.py`
- `app/classifier/service.py`
- `app/audit/` como modulo-fonte ativo
- analytics e deploy como routers ativos
- webhook Meta especifico como canal validado
- bot Telegram em webhook publico estavel como parte do bootstrap reproduzivel
- provedor LLM externo real como caminho principal validado do runtime
- stack completa de Prometheus, Grafana e Loki como operacao externa do case
- PostgreSQL e Redis como dependencias operacionais do runtime atual

Quando estes elementos voltarem ao projeto, devem ser reintroduzidos como implementacao nova e validada, nao como heranca assumida.

## 8. Eixo ativo e planejado: Guardrail Rastreavel

As Fases 9 a 12 passam a carregar um eixo transversal de guardrail rastreavel.

Objetivo:

- tornar a trilha de decisao auditavel
- correlacionar request, tenant, canal, logs e traces
- registrar guardrails com vocabulario minimo consistente

Modelo de correlacao ativo desde a Fase 10:

- `request_id`
- `tenant_id`
- `session_id`
- `channel`

Contratos ja ativos:

- `PolicyDecision` padronizado
- `AuditEvent` versionado
- `policy_pre`
- `policy_post`
- composicao generativa controlada
- `reason_codes`
- prompts e politicas versionados
- logs estruturados correlacionados por `request_id`
- metricas minimas em `/metrics`
- traces OpenTelemetry persistidos por `request_id`

Evolucoes ainda planejadas:

- validacao remota desses contratos no runner GitHub apos push/PR
- stack externa mais ampla de observabilidade do case

Os documentos normativos desse eixo sao:

- `docs/guardrail_rastreavel.md`
- `docs/genai_com_metodo.md`

### Arquitetura-alvo das Fases 12 a 14

A partir da Fase 10, o projeto deixou de ser apenas retrieval-first e passou a demonstrar GenAI controlada. A Fase 11 fechou a observabilidade minima do runtime, e as proximas fases fecham regressao automatizada e entrega.

Pipeline alvo:

1. entrada HTTP ou Telegram
2. resolucao de `tenant_id`
3. `policy_pre`
4. retrieval tenant-aware
5. composicao generativa sobre o contexto recuperado
6. `policy_post`
7. auditoria versionada
8. logs estruturados, metricas e traces
9. resposta final

Regras dessa arquitetura-alvo:

- a composicao generativa nao deve bypassar retrieval e policy
- o adaptador LLM deve ficar isolado da logica de transporte
- prompt base, prompt de fallback e politica textual devem ser versionados
- a trilha deve permanecer correlacionavel por `request_id`, `tenant_id`, `session_id` e `channel`
- a observabilidade ativa da Fase 11 observa o pipeline completo, nao apenas HTTP

## 9. Evolucao planejada por fase

### Fase 9 — Telegram

- integrar o tenant demonstrativo a um canal Telegram
- manter consistencia funcional com `POST /api/chat`
- adicionar auditoria correlacionada do canal

### Fase 10 — Composicao generativa, guardrails e evidencias

- composicao generativa minima introduzida
- adaptador de provedor LLM isolado
- prompt base, prompt de fallback e politica textual versionados
- `PolicyDecision` ativo
- schema de auditoria versionado em `audit.v1`
- `policy_pre` e `policy_post` ativos
- evidencias registradas por `request_id`

### Fase 11 — Observabilidade aplicada

- `GET /metrics` exposto no runtime
- logs estruturados correlacionados por `request_id`
- traces OpenTelemetry persistidos por `request_id`
- trilha `request -> policy_pre -> retrieval -> compose -> policy_post -> response` validada no smoke
- cobertura minima dos guardrails e `reason_codes` tornada observavel

### Fase 12 — CI

- workflow versionado em `.github/workflows/ci.yml`
- `quality gates` com lint minimo, anti-residuos, `compileall` e `pytest`
- validacao automatica de `docker compose config` e `docker build`
- smoke `prod` reduzido reaproveitando o mesmo runtime da Fase 11
- upload do artefato JSON do smoke no GitHub Actions
- bloqueio do pipeline em regressao de `audit.v1`, `request_id`, `tenant_id`, `reason_codes` e integridade do audit trail

### Fase 13 — Deploy minimo em AWS

- stack Terraform minima em `infra/terraform/aws/minimal`
- EC2 unica com Docker e Elastic IP
- deploy remoto reproduzivel via `user_data` e `scripts/deploy_aws_instance.sh`
- bootstrap do tenant `prefeitura-vila-serena` na instancia
- smoke remoto aprovado via `scripts/smoke_remote.py`

## 10. Validacao arquitetural

Validacoes minimas desta base:

- startup do backend
- `GET /`
- `GET /health`
- `POST /api/chat`
- `POST /api/webhook`
- fluxo tenant-aware
- persistencia por tenant
- auditoria por tenant
- smoke local e via Docker
- smoke remoto do deploy em AWS

## 11. Regras de manutencao do documento

- descrever como presente apenas o que esta no runtime validado
- marcar como planejado o que ainda depende das Fases 9 a 12
- preservar coerencia com `README.md`, `docs/contexto.md` e `docs/planejamento_fases.md`
- atualizar o documento sempre que um contrato de runtime mudar de fato
