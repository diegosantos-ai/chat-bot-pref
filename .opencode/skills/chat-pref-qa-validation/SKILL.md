---
name: chat-pref-qa-validation
description: Usar no repositorio Chat Pref quando a tarefa exigir estrategia de teste, smoke, evidencia de comportamento, revisao de risco de regressao, validacao de tenant flow, validacao do runtime ou verificacao do RAG da demo. Acionar apos mudancas em codigo, docs operacionais ou automacoes quando for preciso declarar claramente o que foi ou nao foi testado.
---

# Chat Pref Qa Validation

Definir o menor conjunto de validacoes que realmente prova a mudanca, sem inflar a task nem esconder risco residual.

## Ler antes de validar

- `AGENTS.md`
- `README.md`
- `docs-fundacao-operacional/matriz_cenarios_validacao.md` e `docs-fundacao-operacional/rubrica_qualidade_resposta.md` quando a task tocar resposta, guardrail ou cenarios
- `docs-fundacao-operacional/evidencias_case.md` quando a task tocar demonstracao ou portfolio tecnico
- `docs-LLMOps/PLANEJAMENTO-LLMOps.md` e `docs-LLMOps/runbooks/avaliacao-rag.md` quando a task tocar benchmark ou avaliacao formal
- `.github/agents/qa-validation.agent.md`
- `.ai/skills/validate-runtime.md`
- `.ai/skills/validate-tenant-flow.md`
- `.ai/skills/validate-rag-demo.md`
- `.ai/skills/prepare-demo-evidence.md`
- `.ai/workflows/validacao-demo.md`
- `.ai/workflows/refatoracao-fase.md`

## Workflow

1. Partir dos arquivos alterados e do criterio de aceite, nao de uma bateria fixa de testes.
2. Escolher a menor combinacao confiavel entre startup, endpoint, pytest, smoke, validacao de tenant e validacao de RAG.
3. Preferir uma protecao objetiva contra regressao quando houver bug corrigido.
4. Registrar o resultado observado, nao apenas o comando executado.
5. Distinguir claramente o que foi testado, o que nao foi testado e o risco residual.

## Guardrails

- Priorizar validacoes aderentes a fase atual.
- Nao vender como executado aquilo que foi apenas inferido.
- Nao confundir evidencia operacional da Fundacao com avaliacao formal da Fase 1.
- Se a validacao depender de ambiente externo indisponivel, declarar a lacuna e o menor proximo passo valido.

## Validacao sugerida

- Startup do backend
- `GET /`, `GET /health`, `POST /api/chat`, `POST /api/webhook`, `GET /api/rag/status` conforme o fluxo tocado
- `python3 -m pytest tests -q`
- `docker compose -f docker-compose.yml config`
- Smoke local, remoto ou artifact de LLMOps somente quando o escopo exigir
