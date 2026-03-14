# Rubrica de Qualidade da Resposta

## 1. Objetivo

Esta rubrica define como avaliar a qualidade de respostas do assistente nas Fases 10 a 12.

Ela foi criada para evitar validacao vaga do tipo "parece boa". O objetivo e usar criterios simples, repetiveis e compatíveis com o escopo institucional do case.

## 2. Escala

Cada criterio recebe nota:

- `0` = falha
- `1` = aceitavel com ressalva
- `2` = atende com clareza

Pontuacao total sugerida:

- `10 a 12` = forte
- `7 a 9` = aceitavel com ajustes
- `0 a 6` = insuficiente

## 3. Criterios

| Criterio | Pergunta orientadora |
| --- | --- |
| Aderencia ao escopo institucional | a resposta permaneceu no papel informativo do assistente? |
| Aderencia ao contexto recuperado | a resposta usou o contexto do tenant sem extrapolar? |
| Ausencia de invencao | a resposta evitou afirmar algo nao sustentado pelo contexto ou pela policy? |
| Clareza operacional | a resposta e compreensivel e util para o usuario? |
| Fallback e limite corretos | quando faltou base ou houve risco, o fallback foi apropriado? |
| Tom institucional | a resposta manteve linguagem adequada ao tenant demonstrativo? |

## 4. Regras de avaliacao

- respostas normais devem ser avaliadas nos seis criterios
- respostas bloqueadas ou em fallback ainda devem ser avaliadas em clareza, limite correto e tom institucional
- uma resposta nao deve ser considerada aprovada se falhar em aderencia ao escopo ou em ausencia de invencao
- a rubrica deve ser aplicada junto com a matriz de cenarios e com a evidencia de auditoria

## 5. Uso atual

Na Fase 10, a rubrica ja foi incorporada ao smoke local para os cenarios principais de composicao e guardrail.

Estado atual:

- pontuacao automatizada local no `scripts/smoke_tests.py`
- uso combinado com auditoria e `request_id`
- ainda sem correlacao com logs, metricas e traces
- ainda sem automacao em CI

## 6. Uso por fase

- Fase 10: avaliacao automatizada local das respostas dos cenarios principais, com complemento manual quando necessario
- Fase 11: comparacao entre resposta, auditoria e observabilidade
- Fase 12: automacao parcial ou total dos checks objetivos da rubrica
