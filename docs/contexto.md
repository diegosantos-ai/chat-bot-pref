# Contexto do Projeto

## 1. Identificacao

- **Projeto:** Chat Pref
- **Repositorio:** `/media/diegosantos/TOSHIBA EXT/Projetos/Desenvolvendo/chat-bot-pref`
- **Responsavel:** Diego Santos
- **Status atual:** em andamento
- **Fase ativa:** Fase 13 — Infraestrutura como Codigo e Deploy em AWS
- **Status da fase atual:** concluida e validada na branch de trabalho
- **Eixo transversal aprovado:** Guardrail Rastreavel nas Fases 9 a 12

## 2. Objetivo do projeto

O projeto existe para demonstrar uma plataforma de atendimento institucional com IA aplicada ao setor publico, com:

- backend organizado em FastAPI
- contrato multi-tenant explicito
- base RAG segregada por tenant
- composicao generativa minima controlada
- guardrails executaveis com `reason_codes`
- auditoria versionada util
- demonstracao funcional com tenant ficticio
- evolucao controlada para CI e deploy em nuvem

O valor do case esta em provar arquitetura, refatoracao controlada, explicabilidade operacional e capacidade de evolucao.

## 3. Runtime ativo hoje

O runtime validado atual e um nucleo minimo, explicavel e testavel.

Ele inclui:

- `GET /`
- `GET /health`
- `POST /api/chat`
- `POST /api/webhook`
- `POST /api/telegram/webhook`
- `GET /api/rag/status`
- `POST /api/rag/documents`
- `POST /api/rag/ingest`
- `POST /api/rag/query`
- `POST /api/rag/reset`

Capacidades atualmente validadas:

- `tenant_id` explicito nos fluxos criticos
- `tenant_context` por request
- resolucao minima de tenant no webhook
- integracao demonstrativa do Telegram com o mesmo fluxo do chat
- adaptador LLM isolado com composicao generativa minima
- prompts base, fallback e politica textual versionados
- `PolicyDecision` ativo em `policy_pre` e `policy_post`
- auditoria `audit.v1` com `event_id`, `channel` e `policy_decision`
- `X-Request-ID` aceito em `POST /api/chat` e `POST /api/webhook`
- historico de chat em arquivo por tenant
- auditoria versionada em arquivo por tenant
- logs estruturados persistidos por `request_id`
- metricas minimas expostas em `/metrics`
- traces OpenTelemetry persistidos por `request_id`
- base documental e retrieval por tenant em Chroma
- tenant demonstrativo `prefeitura-vila-serena`
- ambiente local reproduzivel com Docker e smoke tests
- deploy remoto minimo validado em AWS com EC2 unica, Docker e Terraform

### Diagnostico executivo da base

Hoje o projeto ja demonstra metodo real em:

- RAG tenant-aware
- contrato multi-tenant
- composicao generativa minima com prompt versionado
- guardrails executaveis com `PolicyDecision`
- auditoria versionada com correlacao por `request_id`
- validacao operacional com testes e smoke

O principal gap para `GenAI com metodo` ainda e:

- ausencia de validacao reproduzivel com provedor LLM externo real
- ausencia de automacao de evidencias no pipeline de entrega

As Fases 9 a 12 foram redefinidas para fechar esse gap de forma incremental e rastreavel.

## 4. O que ja foi estabilizado

Bloco estrutural concluido:

- Fase 1 — diagnostico e inventario do legado
- Fase 2 — sanitizacao funcional do runtime
- Fase 3 — consolidacao do contrato multi-tenant
- Fase 4 — reset da base RAG e reingestao limpa
- Fase 5 — containerizacao e ambiente local reproduzivel
- Fase 6 — validacao estrutural da base refatorada

Bloco demonstrativo ja concluido:

- Fase 7 — tenant demonstrativo ficticio
- Fase 8 — base documental ficticia e ingest limpa

## 5. O que nao faz parte do runtime ativo hoje

Os itens abaixo continuam sendo direcao futura, nao comportamento presente do runtime:

- orchestrator e classifier como pipeline ativo do backend
- bot Telegram operando com webhook publico estavel como parte do bootstrap reproduzivel
- provedor LLM externo real validado como default do runtime
- painel admin como servico validado no ambiente local

## 6. Fase atual e direcao aprovada

### Fase 9

Entregas validadas na branch:

- tenant demonstrativo operando no webhook do Telegram
- reutilizacao do mesmo `ChatService` do chat direto
- auditoria correlacionada com `request_id`, `tenant_id`, `chat_id`, `message_id` e `update_id`
- smoke local validando o canal em `dry_run`

### Fase 10

Entregas validadas na branch:

- adaptador LLM isolado com `LLM_PROVIDER=mock` como default e suporte opcional a `gemini`
- composicao controlada usando contexto recuperado, tenant profile e prompts versionados
- `policy_pre` e `policy_post` com `reason_codes`
- `PolicyDecision` padronizado e `AuditEventRecord` versionado em `audit.v1`
- cenarios normais, fora de escopo, baixa confianca, transacional e risco validados
- evidencias correlacionadas por `request_id` no smoke e nos testes

### Fase 11

Entregas validadas na branch:

- logs estruturados persistidos e acessiveis por `request_id`
- metricas minimas expostas em `/metrics`
- traces OpenTelemetry persistidos por `request_id`
- trilha observavel `request -> policy_pre -> retrieval -> compose -> policy_post -> response`
- correlacao consistente entre auditoria, logs e traces no smoke `prod` e `dev`

### Fase 12

Entregas validadas na branch:

- workflow de CI versionado em `.github/workflows/ci.yml`
- lint minimo, `pytest`, `compileall` e varredura anti-residuos automatizados
- validacao automatica de `docker compose config` e `docker build`
- smoke `prod` reduzido automatizado com `runtime-mode=reuse`
- upload do artefato `fase11-smoke-prod.json` no workflow
- regressao automatica de `audit.v1`, `request_id`, `tenant_id` e `reason_codes` em `tests/test_phase12.py`
- nenhuma credencial nova obrigatoria para o corte atual da CI; deploy continua separado

### Fase 13

Entregas validadas na branch:

- stack minima em `infra/terraform/aws/minimal` validada com `terraform fmt`, `init`, `validate`, `plan` e `apply`
- infraestrutura provisionada com VPC dedicada, subnet publica, Security Group, role SSM, EC2 unica e Elastic IP
- deploy remoto reproduzivel via `user_data` e `scripts/deploy_aws_instance.sh`
- tenant demonstrativo bootstrapped na instancia com ingest limpa da base institucional
- validacao remota aprovada em `GET /`, `GET /health`, `GET /metrics` e `POST /api/chat`
- nenhuma credencial nova obrigatoria para o corte atual do deploy; `LLM_PROVIDER=mock` e Telegram seguem em modo controlado

Referencia normativa desse eixo:

- `docs/guardrail_rastreavel.md`
- `docs/genai_com_metodo.md`

## 7. Contratos arquiteturais que ja valem

- `tenant_id` deve ser explicito nos fluxos criticos
- ausencia de tenant deve gerar erro controlado
- historico, auditoria e retrieval devem permanecer segregados por tenant
- o runtime atual usa persistencia local em arquivo
- o repositorio ativo de auditoria e `app/storage/audit_repository.py`
- o `request_id` ja existe no fluxo de chat e deve evoluir para contrato transversal

## 8. Principais riscos atuais

- documentacao voltar a descrever como ativo o que ainda e apenas alvo arquitetural
- integracao do Telegram divergir do comportamento ja validado em `POST /api/chat`
- crescimento do escopo de guardrail antes de existir trilha rastreavel minima
- reintroducao de fallback silencioso para tenant
- mistura entre stack-alvo do case e runtime minimo da branch

## 9. Criterio de sucesso imediato

O proximo ciclo sera considerado bem encaminhado quando:

- README, contexto, arquitetura, diario e evidencias contarem a mesma historia da branch
- o deploy minimo remoto permanecer alinhado aos contratos de `request_id`, `tenant_id` e observabilidade
- a preparacao da Fase 14 organizar o case final sem inflar promessa tecnica

## 10. Forma de validacao

Validacoes minimas esperadas nesta etapa:

- leitura cruzada de `README.md`, `docs/contexto.md`, `docs/arquitetura.md` e `docs/planejamento_fases.md`
- coerencia entre estado do runtime e descricoes dos documentos
- ausencia de declaracao indevida de features ainda nao implementadas
- alinhamento das Fases 9 a 12 com `docs/guardrail_rastreavel.md`
- `pytest`
- smoke `prod` e `dev` da fase ativa
- smoke remoto da Fase 13

## 11. Observacoes de continuidade

- a stack-alvo do projeto continua maior do que o runtime ativo da branch
- o `README.md` deve manter a espinha dorsal do case e sinalizar fase/status
- `docs/arquitetura.md` deve continuar como fonte de verdade do runtime ativo
- o deploy minimo em AWS ja foi validado na branch, mas ainda sem dominio proprio, HTTPS ou CD completo
- toda evolucao futura deve priorizar contrato, evidencia e coerencia entre codigo e documentacao
- a narrativa legivel do case pode ser mantida em `docs/diario_bordo.md` e `docs/evidencias_case.md` sem inflar os documentos-base
