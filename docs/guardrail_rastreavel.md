# Guardrail Rastreavel

## 1. Objetivo

Este documento define o eixo transversal de guardrail rastreavel para as Fases 9 a 12 do Chat Pref.

Ele existe para alinhar:

- contratos de correlacao entre request, tenant, canal e auditoria
- vocabulario minimo de decisao de politica
- padrao de log e trilha de evidencias
- referencia de governanca para risco e comportamento do assistente

Este documento descreve o estado atual da base e o estado alvo planejado. Ele nao declara como ativo algo que ainda nao entrou no runtime.

## 2. Padroes adotados

### OWASP Logging Cheat Sheet

Papel no projeto:

- definir o conteudo minimo do log e da trilha de auditoria
- orientar o que deve ser registrado
- orientar o que nao deve ser registrado

### OWASP LLM Top 10

Papel no projeto:

- servir como catalogo inicial de ameacas para o case
- justificar o conjunto inicial de guardrails
- orientar a definicao dos `reason_codes`

### NIST AI RMF

Papel no projeto:

- servir como referencia de governanca e risco
- orientar a narrativa de seguranca, explicabilidade e rastreabilidade
- nao atuar como contrato tecnico de runtime

### OpenTelemetry

Papel no projeto:

- correlacionar logs, traces e metricas
- materializar a trilha ponta a ponta do fluxo
- entrar apenas a partir da Fase 11

## 3. Estado atual da base

O runtime ativo hoje ja possui uma base minima reaproveitavel:

- `tenant_id` explicito nos fluxos criticos
- `request_id` gerado no fluxo de chat e devolvido na resposta
- auditoria minima por tenant em `app/storage/audit_repository.py`
- segregacao por tenant no historico, na auditoria e no RAG

O runtime ativo hoje ainda nao possui:

- `PolicyDecision`
- `AuditEvent` versionado
- `policy_pre`
- `policy_post`
- `reason_codes`
- logging estruturado
- `/metrics`
- traces com OpenTelemetry

## 4. Estado alvo planejado

Ao final das Fases 9 a 12, o projeto deve ter:

- correlacao minima consistente entre HTTP, Telegram, auditoria, logs e traces
- decisoes de politica registradas antes e depois da resposta
- composicao generativa controlada sobre contexto recuperado
- evidencia rastreavel por `request_id` e `tenant_id`
- validacao automatica do schema de auditoria e dos campos obrigatorios

## 5. Contratos planejados

### PolicyDecision

Objeto padronizado para decisao de politica:

- `stage`: `policy_pre | policy_post`
- `decision`: `allow | block | fallback | review`
- `reason_codes`: `list[str]`
- `policy_version`: `str`
- `summary`: `str`
- `metadata`: `dict[str, str]`

### AuditEvent

Schema versionado para auditoria:

- `schema_version`: `audit.v1`
- `event_id`
- `request_id`
- `tenant_id`
- `session_id`
- `channel`
- `event_type`
- `policy_decision` opcional
- `payload`
- `created_at`

### Versionamento de prompt e policy

Quando a camada generativa entrar, cada comportamento relevante deve apontar para versoes explicitas de:

- prompt base
- prompt de fallback
- politica textual do assistente
- adaptador do provedor LLM

O objetivo e impedir que a camada generativa evolua sem baseline rastreavel.

## 6. Onde entra a composicao generativa

O eixo de guardrail rastreavel nao existe para observar apenas HTTP e retrieval.

Ele deve atravessar o pipeline futuro:

1. entrada HTTP ou Telegram
2. resolucao de tenant
3. `policy_pre`
4. retrieval
5. composicao generativa
6. `policy_post`
7. auditoria, logs e traces
8. resposta final

Regra planejada:

- o mesmo `request_id` deve atravessar entrada, auditoria, composicao e resposta
- toda decisao de `policy_pre` e `policy_post` deve gerar um `PolicyDecision`
- prompt e policy associados ao request devem permanecer identificaveis por versao

## 7. Campos obrigatorios de correlacao

Os fluxos criticos devem convergir para estes campos:

- `request_id`
- `tenant_id`
- `session_id`
- `channel`

Regras planejadas:

- `request_id` obrigatorio em todo fluxo critico
- `tenant_id` obrigatorio em todo fluxo critico
- `session_id` mantido como identificador de conversa
- `channel` sempre persistido em auditoria
- HTTP deve aceitar `X-Request-ID` quando recebido e devolver o mesmo header na resposta
- Telegram deve persistir `chat_id`, `message_id` e `update_id` no `payload`

## 8. Catalogo inicial de reason_code

- `OUT_OF_SCOPE`
- `NO_KNOWLEDGE_BASE`
- `LOW_CONFIDENCE_RETRIEVAL`
- `UNSUPPORTED_TRANSACTIONAL_ACTION`
- `SENSITIVE_DATA_REQUEST`
- `PROMPT_INJECTION_SUSPECTED`
- `CRISIS_OR_MEDICAL_RISK`
- `POLICY_POST_RESPONSE_REWRITE`

## 9. Mapeamento minimo de ameaca para guardrail

| Ameaca / situacao | Guardrail esperado | `reason_code` principal | Evidencia minima esperada |
| --- | --- | --- | --- |
| Pergunta fora do escopo institucional | bloquear ou redirecionar resposta | `OUT_OF_SCOPE` | `PolicyDecision`, `request_id`, resposta limitada |
| Base nao carregada | fallback controlado | `NO_KNOWLEDGE_BASE` | evento de auditoria e resposta de fallback |
| Retrieval fraco ou ambíguo | fallback ou resposta com baixa confianca | `LOW_CONFIDENCE_RETRIEVAL` | score baixo ou ausencia de contexto + decisao registrada |
| Pedido transacional nao suportado | bloqueio institucional | `UNSUPPORTED_TRANSACTIONAL_ACTION` | decisao pre ou post + resposta explicita |
| Pedido de dado sensivel | bloqueio ou resposta limitada | `SENSITIVE_DATA_REQUEST` | decisao de policy + evento correlacionado |
| Tentativa de injecao ou bypass | bloqueio ou fallback defensivo | `PROMPT_INJECTION_SUSPECTED` | decisao de policy + trilha por `request_id` |
| Conteudo clinico, crise ou risco | bloqueio e encaminhamento seguro | `CRISIS_OR_MEDICAL_RISK` | decisao registrada + resposta segura |

## 10. Regras de logging e auditoria

Campos minimos planejados para logs estruturados:

- `timestamp`
- `level`
- `event_name`
- `request_id`
- `tenant_id`
- `session_id`
- `channel`
- `event_type`
- `policy_stage`
- `decision`
- `reason_codes`

Regras operacionais:

- registrar o minimo necessario para rastreabilidade
- nao registrar segredo, token, credencial ou dado pessoal desnecessario
- nao registrar prompt bruto sensivel sem justificativa operacional
- manter coerencia entre auditoria, logs e traces

## 11. Mapa de implementacao por fase

### Fase 9

- correlacao minima do canal Telegram
- auditoria correlacionada com `request_id`, `tenant_id`, `chat_id`, `message_id` e `update_id`
- consistencia comportamental entre Telegram e `POST /api/chat`

### Fase 10

- introducao da composicao generativa minima controlada
- introducao de `PolicyDecision`
- introducao de `AuditEvent` versionado
- versionamento de prompt base, prompt de fallback e politica textual
- `policy_pre` e `policy_post` com `reason_codes`
- matriz de cenarios ligada ao catalogo de ameaças e fallbacks

### Fase 11

- logs estruturados correlacionados
- endpoint `/metrics`
- OpenTelemetry para traces e correlacao do fluxo principal
- observabilidade da trilha `request -> policy_pre -> retrieval -> compose -> policy_post -> response`

### Fase 12

- validacao automatica do schema de auditoria
- regressao de `request_id`, `tenant_id`, `reason_codes` e integridade do audit trail
- CI bloqueando regressao relevante

## 12. Fonte de verdade

Este documento deve ser lido junto com:

- `docs/planejamento_fases.md`
- `docs/contexto.md`
- `docs/arquitetura.md`
- `docs/genai_com_metodo.md`
- `docs/matriz_cenarios_validacao.md`
- `docs/rubrica_qualidade_resposta.md`
- `docs/contrato_operacional_tenant.md`

Sempre que houver diferenca entre expectativa futura e runtime atual, prevalece o estado real do codigo validado na branch.
