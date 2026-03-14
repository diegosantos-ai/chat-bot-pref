# Contexto do Projeto

## 1. Identificacao

- **Projeto:** Chat Pref
- **Repositorio:** `/media/diegosantos/TOSHIBA EXT/Projetos/Desenvolvendo/chat-bot-pref`
- **Responsavel:** Diego Santos
- **Status atual:** em andamento
- **Fase ativa:** Fase 9 — Operacionalizacao do chat via Telegram
- **Status da fase atual:** concluida e validada na branch de trabalho
- **Eixo transversal aprovado:** Guardrail Rastreavel nas Fases 9 a 12

## 2. Objetivo do projeto

O projeto existe para demonstrar uma plataforma de atendimento institucional com IA aplicada ao setor publico, com:

- backend organizado em FastAPI
- contrato multi-tenant explicito
- base RAG segregada por tenant
- auditoria minima util
- demonstracao funcional com tenant ficticio
- evolucao planejada para guardrails, observabilidade, CI e deploy

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
- historico de chat em arquivo por tenant
- auditoria minima em arquivo por tenant
- base documental e retrieval por tenant em Chroma
- tenant demonstrativo `prefeitura-vila-serena`
- ambiente local reproduzivel com Docker e smoke tests

### Diagnostico executivo da base

Hoje o projeto ja demonstra metodo real em:

- RAG tenant-aware
- contrato multi-tenant
- auditoria minima
- validacao operacional com testes e smoke

O principal gap para `GenAI com metodo` ainda e:

- ausencia de composicao generativa ativa e governada
- ausencia de guardrails executaveis com `reason_codes`
- ausencia de observabilidade do pipeline completo

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

- orchestrator, classifier e policy guard como pipeline ativo do backend
- auditoria versionada com `PolicyDecision`
- logs estruturados no runtime
- endpoint `/metrics`
- traces com OpenTelemetry
- bot Telegram operando com token real e webhook publico em ambiente externo
- painel admin como servico validado no ambiente local
- CI executando validacoes no GitHub Actions
- deploy em AWS provisionado por Terraform

## 6. Fase atual e direcao aprovada

### Fase 9

Entregas validadas na branch:

- tenant demonstrativo operando no webhook do Telegram
- reutilizacao do mesmo `ChatService` do chat direto
- auditoria correlacionada com `request_id`, `tenant_id`, `chat_id`, `message_id` e `update_id`
- smoke local validando o canal em `dry_run`

### Fases 10 a 12

Direcao aprovada:

- introduzir a camada generativa minima controlada
- introduzir guardrails rastreaveis sem criar nova macrofase
- padronizar `PolicyDecision`
- versionar o schema de auditoria
- correlacionar logs, auditoria e traces
- automatizar regressao desses contratos em CI

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

- a composicao generativa minima entrar sem quebrar o contrato multi-tenant
- `PolicyDecision` e auditoria versionada surgirem com evidencias por `request_id`
- a documentacao-base continuar separando claramente presente e planejado
- a Fase 10 introduzir GenAI controlada sem regredir o runtime validado

## 10. Forma de validacao

Validacoes minimas esperadas nesta etapa documental:

- leitura cruzada de `README.md`, `docs/contexto.md`, `docs/arquitetura.md` e `docs/planejamento_fases.md`
- coerencia entre estado do runtime e descricoes dos documentos
- ausencia de declaracao indevida de features ainda nao implementadas
- alinhamento das Fases 9 a 12 com `docs/guardrail_rastreavel.md`

## 11. Observacoes de continuidade

- a stack-alvo do projeto continua maior do que o runtime ativo da branch
- o `README.md` deve manter a espinha dorsal do case e sinalizar fase/status
- `docs/arquitetura.md` deve continuar como fonte de verdade do runtime ativo
- toda evolucao futura deve priorizar contrato, evidencia e coerencia entre codigo e documentacao
