# Migração: Provedores de Embedding Unificados via OpenRouter

**Data:** 2026-02-20  
**Versão:** v1.2.1  
**Impacto:** Baixo — apenas a configuração de provedores externos mudou. Comportamento padrão (`default`) inalterado.

---

## Resumo

Todos os provedores de embedding externos (gemini, openai, qwen) passam a usar a
API unificada do **OpenRouter** (`https://openrouter.ai/api/v1/embeddings`).

Agora apenas **uma chave de API** é necessária para todos os modelos:

| Provedor | Modelo OpenRouter | API Key |
|----------|-------------------|---------|
| `default` | ChromaDB built-in (all-MiniLM-L6-v2) | — |
| `gemini` | `google/gemini-embedding-001` | `OPENROUTER_API_KEY` |
| `openai` | `openai/text-embedding-3-large` | `OPENROUTER_API_KEY` |
| `qwen` | `qwen/qwen3-embedding-8b` | `OPENROUTER_API_KEY` |

---

## Arquivos Modificados

- `app/rag/embeddings.py` — Substituídas `GeminiEmbeddingFunction`, `OpenAIEmbeddingFunction`, `QwenEmbeddingFunction` por uma única `OpenRouterEmbeddingFunction`; `DEFAULT_MODELS` atualizado para IDs OpenRouter
- `app/settings.py` — Removida `OPENAI_API_KEY`; `OPENROUTER_API_KEY` agora cobre todos os provedores externos
- `tests/test_embedding_ab.py` — Testes atualizados para `OpenRouterEmbeddingFunction`
- `scripts/run_embedding_ab_test.py` — Check de disponibilidade usa `OPENROUTER_API_KEY` para todos
- `.env.prod.example` — Removida `OPENAI_API_KEY`, comentário atualizado

---

## Variável de Ambiente

Antes desta mudança eram necessárias até 3 chaves diferentes. Agora:

```env
# Antes (v1.2):
GEMINI_API_KEY=...     # para gemini
OPENAI_API_KEY=...     # para openai
OPENROUTER_API_KEY=... # para qwen

# Depois (v1.2.1):
OPENROUTER_API_KEY=... # para gemini, openai E qwen
```

> **Nota:** `GEMINI_API_KEY` continua sendo necessária para a geração de texto (LLM Gemini 2.0 Flash).  
> Para **embeddings**, somente `OPENROUTER_API_KEY` é usada.

---

## Aplicação no Servidor

**Não são necessárias ações imediatas** (padrão `default` inalterado).

Para ativar provedores externos:
1. Adicione `OPENROUTER_API_KEY=<sua_chave>` ao `.env` do servidor
2. Configure `EMBEDDING_PROVIDER=gemini` (ou `openai` ou `qwen`)
3. Re-ingira os documentos: `python -m app.rag.ingest data/knowledge_base/... --force`
4. Reinicie o serviço: `sudo systemctl restart terezia-api`
