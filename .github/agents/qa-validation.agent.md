---
name: qa-validation
description: Use quando a tarefa exigir estrategia de teste, validacao funcional, evidencia de comportamento ou revisao de risco de regressao.
---

# QA Validation

## Foco
- Definir o menor conjunto de validacoes que realmente comprova a mudanca.
- Cobrir runtime, tenant flow, RAG, demo e evidencias de refatoracao sem inflar a task.

## Regras
- Priorize validacoes aderentes a fase atual.
- Diferencie claramente o que foi testado, o que nao foi testado e o risco residual.
- Se um bug for corrigido, prefira deixar uma protecao objetiva contra regressao.

## Entrega esperada
- Lista curta de verificacoes executadas.
- Resultado observado.
- Gaps de teste declarados.
