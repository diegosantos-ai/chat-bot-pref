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
- persistencia local em arquivo
- auditoria minima por tenant
- retrieval tenant-aware em Chroma
- tenant demonstrativo versionado
- execucao local e via Docker

Rotas ativas no `app/main.py`:

- `GET /`
- `GET /health`
- `POST /api/chat`
- `POST /api/webhook`
- `GET /api/rag/status`
- `POST /api/rag/documents`
- `POST /api/rag/ingest`
- `POST /api/rag/query`
- `POST /api/rag/reset`

## 3. Componentes ativos do backend

| Componente | Papel atual |
| --- | --- |
| `app/main.py` | bootstrap do FastAPI e registro dos routers ativos |
| `app/api/chat.py` | entrada HTTP do chat direto com `tenant_id` explicito |
| `app/api/webhook.py` | entrada HTTP do webhook minimo com resolucao controlada de tenant |
| `app/api/rag.py` | operacoes de documentos, ingest, query, status e reset do RAG |
| `app/api/health.py` | endpoints de raiz e healthcheck |
| `app/services/chat_service.py` | fluxo principal atual de chat, retrieval e auditoria minima |
| `app/services/rag_service.py` | operacoes do RAG por tenant |
| `app/services/demo_tenant_service.py` | validacao e bootstrap do tenant demonstrativo |
| `app/tenant_context.py` | injecao, leitura e limpeza do tenant no fluxo por request |
| `app/tenant_resolver.py` | resolucao de tenant em fluxos externos simples |
| `app/storage/chat_repository.py` | historico de conversa em arquivo por tenant |
| `app/storage/audit_repository.py` | auditoria minima em arquivo por tenant |
| `app/storage/document_repository.py` | persistencia de documentos da base RAG por tenant |
| `app/storage/chroma_repository.py` | collections e retrieval no Chroma segregados por tenant |

## 4. Fluxo ativo atual

### Chat direto

1. `POST /api/chat` recebe `tenant_id` e `message`
2. o endpoint injeta `tenant_id` no `tenant_context`
3. `ChatService` confirma o tenant ativo
4. o fluxo gera `request_id` e `session_id`
5. o request e auditado
6. o `RagService` consulta a collection do tenant
7. a resposta e devolvida ao cliente
8. historico e auditoria sao persistidos em arquivo

### Webhook minimo

1. `POST /api/webhook` recebe `tenant_id` explicito ou `page_id`
2. o tenant e resolvido de forma controlada
3. o endpoint injeta o tenant no contexto
4. o fluxo reaproveita o mesmo `ChatService`
5. a resposta volta em HTTP com o mesmo contrato funcional do chat

## 5. Persistencia ativa

### Historico de conversa

- repositorio ativo: `app/storage/chat_repository.py`
- formato: JSONL
- segregacao: `data/runtime/<tenant_id>/<session_id>.jsonl`

### Auditoria

- repositorio ativo: `app/storage/audit_repository.py`
- formato: JSONL
- segregacao: `data/runtime/audit/<tenant_id>/<session_id>.jsonl`
- schema ativo hoje: `AuditEventRecord`

Campos atuais do `AuditEventRecord`:

- `request_id`
- `tenant_id`
- `session_id`
- `event_type`
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
- webhook nao usa tenant default silencioso
- persistencia e retrieval devem respeitar segregacao por tenant
- `request_id` ja existe no fluxo de chat e na auditoria minima
- o runtime atual continua usando persistencia local em arquivo

## 7. Componentes fora do runtime ativo atual

Os itens abaixo podem existir como narrativa do case, artefato antigo ou objetivo futuro, mas nao fazem parte do runtime minimo validado hoje:

- `app/orchestrator/service.py`
- `app/classifier/service.py`
- `app/policy_guard/service.py`
- `app/audit/` como modulo-fonte ativo
- analytics e deploy como routers ativos
- webhook Meta especifico como canal validado
- pipeline completo de logs estruturados, Prometheus, Grafana e Loki
- PostgreSQL e Redis como dependencias operacionais do runtime atual

Quando estes elementos voltarem ao projeto, devem ser reintroduzidos como implementacao nova e validada, nao como heranca assumida.

## 8. Eixo planejado: Guardrail Rastreavel

As Fases 9 a 12 passam a carregar um eixo transversal de guardrail rastreavel.

Objetivo:

- tornar a trilha de decisao auditavel
- correlacionar request, tenant, canal, logs e traces
- registrar guardrails com vocabulario minimo consistente

Modelo de correlacao planejado:

- `request_id`
- `tenant_id`
- `session_id`
- `channel`

Evolucoes planejadas:

- `PolicyDecision` padronizado
- `AuditEvent` versionado
- `policy_pre`
- `policy_post`
- composicao generativa controlada
- `reason_codes`
- prompts e politicas versionados
- logs estruturados
- `/metrics`
- OpenTelemetry

Esses itens ainda nao fazem parte do runtime atual. Os documentos normativos desse eixo sao:

- `docs/guardrail_rastreavel.md`
- `docs/genai_com_metodo.md`

### Arquitetura-alvo das Fases 10 a 12

A partir da Fase 10, o projeto deixa de ser apenas retrieval-first e passa a demonstrar GenAI controlada.

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
- a observabilidade da Fase 11 deve observar o pipeline completo, nao apenas HTTP

## 9. Evolucao planejada por fase

### Fase 9 — Telegram

- integrar o tenant demonstrativo a um canal Telegram
- manter consistencia funcional com `POST /api/chat`
- adicionar auditoria correlacionada do canal

### Fase 10 — Composicao generativa, guardrails e evidencias

- introduzir a composicao generativa minima controlada
- isolar o adaptador de provedor LLM
- versionar prompt base, prompt de fallback e politica textual
- introduzir `PolicyDecision`
- versionar o schema de auditoria
- executar `policy_pre` e `policy_post`
- registrar evidencias por `request_id`

### Fase 11 — Observabilidade aplicada

- expor `/metrics`
- adicionar logs estruturados correlacionados
- instrumentar traces com OpenTelemetry
- consolidar a trilha `request -> policy_pre -> retrieval -> compose -> policy_post -> response`

### Fase 12 — CI

- automatizar regressao dos contratos de correlacao
- validar schema de auditoria
- bloquear pipeline em falhas relevantes

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

## 11. Regras de manutencao do documento

- descrever como presente apenas o que esta no runtime validado
- marcar como planejado o que ainda depende das Fases 9 a 12
- preservar coerencia com `README.md`, `docs/contexto.md` e `docs/planejamento_fases.md`
- atualizar o documento sempre que um contrato de runtime mudar de fato
