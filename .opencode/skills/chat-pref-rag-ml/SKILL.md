---
name: chat-pref-rag-ml
description: Usar no repositorio Chat Pref quando a tarefa envolver `app/rag/`, `app/services/rag_service.py`, ingest, retrieval, `document_repository`, `chroma_repository`, colecoes por tenant, benchmark RAG ou avaliacao ligada a LLMOps. Acionar tambem quando for preciso validar falha segura sem base carregada ou evidenciar qualidade do retrieval.
---

# Chat Pref Rag Ml

Garantir retrieval tenant-aware, ingest explicita e comportamento seguro quando a base estiver ausente, incompleta ou em evolucao para a fase de LLMOps.

## Ler antes de editar

- `AGENTS.md`
- `README.md`
- `docs-fundacao-operacional/contexto.md`
- `docs-fundacao-operacional/arquitetura.md`
- `docs-fundacao-operacional/planejamento_fases.md`
- `docs-LLMOps/README.md`, `docs-LLMOps/CONTEXTO-LLMOps.md`, `docs-LLMOps/ARQUITETURA-LLMOps.md` e `docs-LLMOps/PLANEJAMENTO-LLMOps.md` quando a task tocar benchmark, avaliacao, tracking ou governanca de artefatos
- `docs-LLMOps/runbooks/avaliacao-rag.md` quando a task tocar avaliacao formal
- `.github/agents/rag-ml.agent.md`
- `.ai/skills/validate-rag-demo.md`
- `.ai/workflows/ingest-demo.md`
- `.ai/workflows/refatoracao-fase.md`

## Workflow

1. Confirmar tenant, collection e repositorios tocados.
2. Verificar se o fluxo depende de nome hardcoded de collection, path ou base documental.
3. Confirmar o comportamento quando a base nao existe, esta vazia ou foi resetada.
4. Em task de retrieval, rodar perguntas controladas ligadas aos documentos ingeridos.
5. Em task de avaliacao LLMOps, distinguir claramente contrato ativo de avaliacao ja executada versus arquitetura-alvo ainda planejada.
6. Registrar evidencia minima de qualidade, fallback ou ruido observado.

## Guardrails

- Nao usar collection hardcoded.
- Nao misturar dados de tenants distintos em ingest, retrieval, benchmark ou tracking.
- Tratar historico operacional e experiment tracking como camadas separadas.
- Nao declarar avaliacao formal de RAG como contrato ativo sem execucao e evidencia correspondentes.

## Validacao sugerida

- `GET /api/rag/status`
- `POST /api/rag/ingest`, `POST /api/rag/query` ou `POST /api/rag/reset` conforme o escopo
- Perguntas controladas ligadas ao tenant afetado
- Smoke ou artifact de avaliacao somente quando a task realmente tocar a fase de LLMOps
