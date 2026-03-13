# GenAI com Metodo

## 1. Objetivo

Este documento define o que o Chat Pref considera `GenAI com metodo`.

Ele nao substitui `docs/arquitetura.md` nem `docs/planejamento_fases.md`.
Sua funcao e transformar o requisito em criterio operacional para as Fases 9 a 14.

## 2. Definicao pratica

Neste projeto, `GenAI com metodo` significa:

- pipeline explicito
- composicao generativa controlada
- separacao entre retrieval, policy, composicao e resposta
- guardrails rastreaveis
- fallback controlado
- evidencias de comportamento
- regressao verificavel
- isolamento por tenant
- observabilidade util

Nao basta usar IA ou RAG. O comportamento precisa ser explicavel, versionavel e validavel.

## 3. Estado atual vs. estado alvo

Hoje a base ja possui:

- contrato explicito de `tenant_id`
- `request_id` no fluxo de chat
- RAG tenant-aware
- auditoria minima por tenant
- tenant demonstrativo e base documental controlada
- smoke tests e retrieval checks

Hoje a base ainda nao possui:

- composicao generativa ativa com provedor LLM
- `PolicyDecision`
- `AuditEvent` versionado
- prompts e politicas versionados
- `policy_pre` e `policy_post`
- logs estruturados
- metricas em `/metrics`
- traces com OpenTelemetry
- regressao automatica de comportamento

## 4. Checklist do requisito

| Dimensao | Estado atual | Fechamento previsto |
| --- | --- | --- |
| Pipeline explicito | parcial | Fases 9 a 11 |
| Composicao generativa controlada | nao implementado | Fase 10 |
| Separacao retrieval / policy / compose / response | parcial | Fase 10 |
| Guardrails pre e post | nao implementado | Fase 10 |
| Fallback controlado | parcial | Fases 10 e 12 |
| Avaliacao por cenarios | parcial | Fases 10 e 12 |
| Auditoria de comportamento | parcial | Fase 10 |
| Rastreabilidade ponta a ponta | parcial | Fases 9 a 11 |
| Versionamento de prompt / policy / config | nao implementado | Fase 10 |
| Criterios objetivos de qualidade | nao implementado | Fase 10 |
| Regressao de comportamento | nao implementado | Fase 12 |
| Aderencia ao escopo institucional | parcial | Fases 10 e 12 |
| Tenant-awareness no fluxo de IA | implementado no nucleo atual | Fases 9 a 10 |
| Observabilidade util | nao implementado | Fase 11 |
| Fechamento de evidencias do case | parcial | Fases 11 a 14 |

## 5. Relacao entre os blocos do sistema

- RAG fornece contexto segregado por tenant
- guardrail limita o comportamento antes e depois da resposta
- composicao generativa usa o contexto recuperado e o prompt versionado
- auditoria registra a trilha da decisao
- matriz de cenarios valida comportamento esperado
- rubrica de qualidade qualifica a resposta
- observabilidade consolida logs, metricas e traces

## 6. Mapa por fase

### Fase 9

- colocar o Telegram sob o mesmo contrato do chat direto
- correlacionar canal, tenant e auditoria

### Fase 10

- introduzir composicao generativa controlada
- versionar prompt, policy e schema de auditoria
- executar guardrails com `reason_codes`
- validar cenarios e qualidade das respostas

### Fase 11

- observar o pipeline completo com logs, metricas e traces
- consolidar a trilha `request -> policy_pre -> retrieval -> compose -> policy_post -> response`

### Fase 12

- automatizar regressao de comportamento e rastreabilidade

### Fases 13 e 14

- preservar esses contratos no deploy
- fechar a narrativa final do case com `claim -> evidencia -> artefato`

## 7. Documentos relacionados

- `docs/guardrail_rastreavel.md`
- `docs/matriz_cenarios_validacao.md`
- `docs/rubrica_qualidade_resposta.md`
- `docs/planejamento_fases.md`
- `docs/arquitetura.md`

Sempre que houver diferenca entre expectativa futura e runtime atual, prevalece o estado real do codigo validado na branch.
