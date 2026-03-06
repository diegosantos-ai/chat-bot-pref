<!-- .github/copilot-instructions.md - concise guidance for AI coding agents -->
# Copilot / AI Agent Instructions

Purpose: quickly orient an AI coding agent to be productive in this repo.

- ## ATENÇÃO AGENTES DE IA:
- Quaisquer modificações de scripts devem ser refletidas neste documento.
- Quaisquer alterações em estruturas de bancos de dados, variaveis de ambiente, dependencias ou alterações no servidor, precisam ser documentadas na pasta 'docs/migrations/' com changelog detalhado do que mudou e do que precisa ser aplicado no servidor.
- Para cada alteração nova necessária no servidor, crie um arquivo md na pasta 'docs/migrations/' com o nome no formato `YYYYMMDD_HHMMSS_descricao.md` detalhando as mudanças.
- Qualquer alteração que possa quebrar o funcionamento do servidor deve ser documentada em 'docs/migrations/' para ser aplicada em conjunto com o deploy.
- Mantenha este documento atualizado com todas as mudanças.
- O servidor de produção usa Linux (Amazon Linux 2023) e scripts devem ser compatíveis.

- **Big picture**: this is a RAG-based FastAPI service (app/) that receives Meta webhooks and `POST /api/chat`, runs an NLP + classifier, applies a PRE policy guard, retrieves context from ChromaDB, composes an LLM answer, runs a POST policy guard, then emits and audits the response. See `app/orchestrator/service.py` for the pipeline.

- **Key components**:
  - `app/main.py`: FastAPI entrypoint and routes.
  - `app/orchestrator/service.py`: full pipeline orchestration (NLP → classifier → policy → RAG → composer → audit).
  - `app/policy_guard/service.py`: PRE/POST guard logic and regex patterns for PII, prompt injection, crises.
  - `app/rag/`: ingestion, retriever, composer; use `prompts/v1/` templates for LLM prompts.
  - `app/channels/meta_sender.py` and `app/integrations/meta/`: Meta Graph API / webhook handling.
  - `data/knowledge_base/` and `chroma_data/`: RAG documents and persistent vector store.

- **What to read first (quick)**: `AGENTS.md`, `README.md`, `app/settings.py`, `app/orchestrator/service.py`, `app/policy_guard/service.py`, `prompts/v1/manifest.json`.

- **Local dev & verification commands** (used across repo):
  - Install deps: `pip install -r requirements.txt`.
  - Validate env/infrastructure: `python scripts/ops/validate_infrastructure.py`.
  - Start DB & Grafana (compose): `docker-compose up -d grafana postgres`.
  - Run API locally: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`.
  - Run E2E tests: `pytest tests/e2e` or specific: `pytest tests/e2e/test_pipeline_e2e.py`.
  - Run RAG validation: `python scripts/run_validation_test.py` (produces `test_output.txt`).

- **Project-specific conventions** (do not invent alternatives):
  - Prompts are versioned in `prompts/v1/`. Modify prompts there and update `manifest.json`.
  - RAG base IDs and collection names are defined in `app/settings.py` (e.g., `RAG_BASE_ID`). Use those constants when adding collections.
  - Policy decisions are explicit enums in `app/contracts/enums.py`. Use existing Decision/PolicyReason values for audit events.
  - Crisis handling and static responses live in `prompts/v1/` (e.g., `crisis_suicide.txt`, `crisis_violence.txt`) — do not replace with generative text.
  - Public vs Inbox behavior: keep public responses short (policy max length). Follow `RESPONSE_MODE_PUBLIC_MAX_LENGTH` and `RESPONSE_MODE_INBOX_MAX_LENGTH` in settings.

- **Integrations & external dependencies**:
  - LLM: configured via settings (OpenAI/Gemini keys in `.env`).
  - ChromaDB: vector store persisted under `chroma_data/` (ingest with `app/rag/ingest.py` or `scripts/chroma_ingest_base.sh`).
  - Meta (Facebook/Instagram): webhook and Graph API clients under `app/integrations/meta/` — HMAC verify logic exists; tests rely on `scripts/start_tunnel.py`/`test_webhook_local.py`.
  - PostgreSQL: audit events and RAG query logs; schema in `db/schema.sql` and helpers in `scripts/db/`.

- **Editing guidance & safe changes**:
  - When touching schema, add a migration note in `docs/migrations/` with `YYYYMMDD_HHMMSS_descr.md`.
  - If changing prompts, run `scripts/run_validation_test.py` to validate regressions in RAG answers.
  - If modifying policy rules, update tests in `tests/e2e` that assert crisis/no-advice behavior.
  - Avoid altering crisis static responses; escalate changes to maintainers and update `AGENTS.md`.

- **Examples of common edits**:
  - Add a new prompt variant: add file in `prompts/v1/`, bump `manifest.json`, run validation script.
  - Add a new document to RAG: put markdown into `data/knowledge_base/.../items/`, run `app/rag/ingest.py` and persist to Chroma.
  - Adjust top_k or min_score: update `app/settings.py` values `RAG_TOP_K` / `RAG_MIN_SCORE` and validate with `run_validation_test.py`.

- **Where not to guess**:
  - Do not invent API contracts; use DTOs in `app/contracts/dto.py` and enums in `app/contracts/enums.py`.
  - Do not change public crisis responses or remove required disclaimers.

If anything is unclear or you want more granular guidance (e.g., common code patterns, testing recipe, or a sample PR), tell me which area to expand. 
