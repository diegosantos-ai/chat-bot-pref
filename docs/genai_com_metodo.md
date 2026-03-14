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
- composicao generativa minima com adaptador isolado
- `PolicyDecision` e auditoria `audit.v1`
- prompts e politica textual versionados
- fallback controlado e cenarios validados
- tenant demonstrativo e base documental controlada
- smoke tests e retrieval checks

Hoje a base ainda nao possui:

- logs estruturados
- metricas em `/metrics`
- traces com OpenTelemetry
- regressao automatica de comportamento em CI
- provedor LLM externo real validado como default reproduzivel

## 4. Checklist do requisito

| Dimensao | Estado atual | Fechamento previsto |
| --- | --- | --- |
| Pipeline explicito | implementado no nucleo atual | Fases 10 a 11 |
| Composicao generativa controlada | implementado no corte minimo da Fase 10 | Fase 10 |
| Separacao retrieval / policy / compose / response | implementado no corte minimo da Fase 10 | Fase 10 |
| Guardrails pre e post | implementado no corte minimo da Fase 10 | Fase 10 |
| Fallback controlado | implementado no nucleo atual | Fases 10 e 12 |
| Avaliacao por cenarios | implementado localmente na Fase 10 | Fases 10 e 12 |
| Auditoria de comportamento | implementado no nucleo atual | Fase 10 |
| Rastreabilidade ponta a ponta | parcial | Fases 9 a 11 |
| Versionamento de prompt / policy / config | implementado no corte minimo da Fase 10 | Fase 10 |
| Criterios objetivos de qualidade | implementado localmente na Fase 10 | Fase 10 |
| Regressao de comportamento | parcial | Fase 12 |
| Aderencia ao escopo institucional | implementado no corte minimo da Fase 10 | Fases 10 e 12 |
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

- composicao generativa controlada introduzida
- prompt, policy e schema de auditoria versionados
- guardrails com `reason_codes` ativos
- cenarios e qualidade das respostas validados no smoke e nos testes

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
