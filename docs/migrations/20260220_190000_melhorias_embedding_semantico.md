# Migracao: Melhorias de Embedding para Semantica do RAG

**Data:** 2026-02-20  
**Versao:** v1.2.2  
**Impacto:** Medio (requer revisar `.env` se for usar novos controles de embedding).

---

## Resumo

Esta migracao reforca o RAG semantico com foco em qualidade e estabilidade de retrieval:

- configuracao de modelo de embedding por provedor (e override global);
- batch de embeddings configuravel para ingestao grande;
- retry com backoff para erros transientes (timeout/429/5xx);
- metadados de `embedding_provider` e `embedding_model` gravados em chunks/collection;
- correção do caminho de auto-ingest do retriever para `data/knowledge_base/...` (com fallback legado `base/...`).

---

## Arquivos alterados

- `app/rag/embeddings.py`
- `app/rag/ingest.py`
- `app/rag/retriever.py`
- `app/settings.py`
- `.env.example`
- `.env.prod.example`
- `scripts/run_embedding_ab_test.py`
- `tests/test_embedding_ab.py`
- `AGENTS.md`

---

## Novas variaveis de ambiente

```env
# Override global opcional (tem prioridade sobre todos)
EMBEDDING_MODEL_OVERRIDE=

# Overrides por provedor
EMBEDDING_MODEL_GEMINI=google/gemini-embedding-001
EMBEDDING_MODEL_OPENAI=openai/text-embedding-3-large
EMBEDDING_MODEL_QWEN=qwen/qwen3-embedding-8b

# Robustez/performance da chamada de embeddings no OpenRouter
EMBEDDING_BATCH_SIZE=32
EMBEDDING_REQUEST_TIMEOUT_SECONDS=60
EMBEDDING_MAX_RETRIES=3
```

> `OPENROUTER_API_KEY` continua sendo a chave unica para provedores externos.

---

## Aplicacao no servidor (Amazon Linux 2023)

1. Atualizar o `.env` do servidor com as novas variaveis (ou manter defaults).
2. Se trocar `EMBEDDING_PROVIDER` ou modelo, reingerir a base:
   - `python -m app.rag.ingest data/knowledge_base/BA-RAG-PILOTO-2026.01.v1 --force`
3. Reiniciar a API:
   - `sudo systemctl restart terezia-api`
4. Validar:
   - query de smoke test RAG;
   - logs sem erro de embedding timeout/429;
   - script opcional: `python scripts/run_embedding_ab_test.py --providers default,openai`.

---

## Observacoes

- Sem mudanca de schema de banco.
- Retrocompativel com `EMBEDDING_PROVIDER=default`.
- Para melhorar semantica, recomenda-se comparar provedores/modelos no A/B antes de fixar em producao.
