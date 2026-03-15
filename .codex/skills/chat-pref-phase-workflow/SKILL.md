---
name: chat-pref-phase-workflow
description: Usar no repositorio Chat Pref quando a tarefa estiver ampla ou ligada ao planejamento por fases e for preciso enquadrar ciclo, fase, task, criterio de aceite e validacao minima antes de editar. Acionar tambem quando for necessario escolher entre backend, RAG, DevOps, QA ou documentacao sem expandir o escopo.
---

# Chat Pref Phase Workflow

Enquadrar toda task do Chat Pref no ciclo correto antes de editar. Usar este skill como camada inicial e, depois, acionar o skill especializado mais aderente.

## Ler antes de editar

- `AGENTS.md`
- `README.md`
- `docs-fundacao-operacional/contexto.md`, `docs-fundacao-operacional/arquitetura.md`, `docs-fundacao-operacional/planejamento_fases.md` quando a task tocar runtime validado
- `docs-LLMOps/README.md`, `docs-LLMOps/CONTEXTO-LLMOps.md`, `docs-LLMOps/ARQUITETURA-LLMOps.md`, `docs-LLMOps/PLANEJAMENTO-LLMOps.md` quando a task tocar a Fase 1
- `.github/agents/`
- `.ai/skills/`
- `.ai/workflows/refatoracao-fase.md`

## Workflow

1. Identificar o ciclo atual: Fundacao Operacional validada ou Fase 1 de LLMOps.
2. Identificar a fase ativa, a task relacionada, o criterio de aceite e a forma minima de validacao.
3. Listar arquivos afetados, risco de regressao e contratos que nao podem quebrar.
4. Escolher o skill complementar:
- `chat-pref-backend-architect` para FastAPI, contratos HTTP, `tenant_id` e `request_id`
- `chat-pref-rag-ml` para ingest, retrieval, colecoes por tenant e avaliacao RAG
- `chat-pref-devops-platform` para Docker, CI, Terraform, AWS e scripts operacionais
- `chat-pref-qa-validation` para estrategia de teste, smoke, evidencia e risco residual
- `chat-pref-docs-operator` para README, AGENTS, docs de arquitetura, operacao e governanca
5. Executar a menor mudanca possivel.
6. Validar apenas o que o criterio de aceite exigir.
7. Encerrar sempre com arquivos alterados, validacao executada, status atual e proximo passo.

## Guardrails

- Distinguir com rigor runtime ativo, contrato consolidado, arquitetura-alvo e item apenas planejado.
- Tratar `tenant_id` como contrato estrutural e `request_id` como contrato transversal ja consolidado.
- Nao misturar operacao, auditoria operacional, experimentacao, benchmark e orquestracao offline.
- Evitar mudanca paralela fora do escopo da task.
- Se houver bloqueio, registrar onde ele esta, por que existe, qual dependencia falta e qual o menor proximo passo valido.
