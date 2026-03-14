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
- workflow de CI versionado com regressao automatizada localmente validada
- deploy remoto minimo validado em AWS com smoke publico
- matriz de evidencias e diario de bordo para leitura por terceiros

Hoje a base ainda nao possui:

- provedor LLM externo real validado como default reproduzivel

## 4. Cobertura validada hoje

O requisito ja possui cobertura objetiva, mas ainda nao completa.

Cobertura validada no runtime e nos testes:

- `SCN-01` pergunta institucional normal
- `SCN-02` fora de escopo institucional
- `SCN-04` baixa confianca no retrieval
- `SCN-05` pedido transacional nao suportado
- `SCN-06` conteudo clinico, crise ou risco
- ausencia de base com `NO_KNOWLEDGE_BASE` em teste automatizado do chat

Cobertura ativa no runtime, mas ainda sem cenario dedicado no smoke:

- uso de provedor LLM externo real como caminho validado

Cobertura automatizada em teste fora do smoke:

- `SENSITIVE_DATA_REQUEST`
- `PROMPT_INJECTION_SUSPECTED`

## 5. Checklist final do requisito

| Dimensao | Status final na branch | Evidencia principal | Artefato |
| --- | --- | --- | --- |
| Pipeline explicito | atende | `ChatService` com `policy_pre -> retrieval -> compose -> policy_post -> response` | `docs/arquitetura.md` |
| Composicao generativa controlada | atende | adaptador LLM isolado com prompts versionados | `docs/fase_10_composicao_generativa.md` |
| Separacao retrieval / policy / compose / response | atende | servicos e contratos separados no runtime | `docs/arquitetura.md` |
| Guardrails pre e post | atende | `PolicyDecision` e `reason_codes` ativos | `docs/guardrail_rastreavel.md` |
| Fallback controlado | atende | cenarios `NO_KNOWLEDGE_BASE`, fora de escopo e baixa confianca | `docs/matriz_cenarios_validacao.md` |
| Avaliacao por cenarios | atende | smoke e testes cobrindo cenarios normais e de risco | `docs/matriz_cenarios_validacao.md` |
| Auditoria de comportamento | atende | `audit.v1` e eventos correlacionados por request | `docs/guardrail_rastreavel.md` |
| Rastreabilidade ponta a ponta | atende | logs, metricas e traces com o mesmo `request_id` | `docs/fase_11_observabilidade_aplicada.md` |
| Versionamento de prompt / policy / config | atende | versoes explicitas de prompt base, fallback e policy | `docs/guardrail_rastreavel.md` |
| Criterios objetivos de qualidade | atende em corte minimo | rubrica de qualidade e checks objetivos no workflow | `docs/rubrica_qualidade_resposta.md` |
| Regressao de comportamento | atende | workflow de CI e testes bloqueantes | `docs/fase_12_github_actions.md` |
| Aderencia ao escopo institucional | atende | tenant profile, prompts e cenarios controlados | `docs/fase_10_composicao_generativa.md` |
| Tenant-awareness no fluxo de IA | atende | chat, webhook, Telegram, auditoria e RAG por tenant | `docs/arquitetura.md` |
| Observabilidade util | atende | `/metrics`, logs e traces persistidos | `docs/fase_11_observabilidade_aplicada.md` |
| Fechamento de evidencias do case | atende | diario, matriz de evidencias e smoke remoto | `docs/evidencias_case.md` |

## 6. Relacao entre os blocos do sistema

- RAG fornece contexto segregado por tenant
- guardrail limita o comportamento antes e depois da resposta
- composicao generativa usa o contexto recuperado e o prompt versionado
- auditoria registra a trilha da decisao
- matriz de cenarios valida comportamento esperado
- rubrica de qualidade qualifica a resposta
- observabilidade consolida logs, metricas e traces

## 7. Mapa por fase

### Fase 9

- colocar o Telegram sob o mesmo contrato do chat direto
- correlacionar canal, tenant e auditoria

### Fase 10

- composicao generativa controlada introduzida
- prompt, policy e schema de auditoria versionados
- guardrails com `reason_codes` ativos
- cenarios e qualidade das respostas validados no smoke e nos testes

### Fase 11

- logs estruturados, metricas e traces implementados
- trilha `request -> policy_pre -> retrieval -> compose -> policy_post -> response` validada no smoke
- correlacao por `request_id` consolidada entre auditoria, logs e traces

### Fase 12

- regressao automatizada de comportamento e rastreabilidade versionada em CI
- cobertura local da Fase 10 e Fase 11 levada para workflow com quality gates, Docker build e smoke reduzido

### Fases 13 e 14

- preservar esses contratos no deploy
- fechar a narrativa final do case com `claim -> evidencia -> artefato`

## 8. Limites declarados

O case fecha `GenAI com metodo` em um corte minimo controlado, mas ainda sem vender maturidade inexistente.

Limites assumidos:

- `LLM_PROVIDER=mock` continua sendo o caminho default reproduzivel do runtime
- o provedor externo real existe como opcional, nao como baseline obrigatorio
- o Telegram foi validado como canal demonstrativo, mas o bootstrap publico estavel nao faz parte do caminho padrao do repositorio
- o deploy AWS validado e minimo, sem dominio proprio, HTTPS ou CD completo

## 9. Veredito final

Hoje, a branch atende o requisito `GenAI com metodo` no recorte proposto pelo projeto:

- pipeline explicito e tenant-aware
- composicao generativa controlada
- guardrails rastreaveis
- auditoria, observabilidade e regressao automatizada
- evidencias locais e remotas que sustentam o comportamento declarado

## 10. Documentos relacionados

- `docs/guardrail_rastreavel.md`
- `docs/matriz_cenarios_validacao.md`
- `docs/rubrica_qualidade_resposta.md`
- `docs/planejamento_fases.md`
- `docs/arquitetura.md`
- `docs/evidencias_case.md`

Sempre que houver diferenca entre expectativa futura e runtime atual, prevalece o estado real do codigo validado na branch.
