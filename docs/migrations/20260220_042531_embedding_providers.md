# Migração: Suporte a Múltiplos Provedores de Embedding + Testes A/B

**Data:** 2026-02-20  
**Versão:** v1.2  
**Impacto:** Baixo — retrocompatível. Padrão `default` mantém comportamento atual.

---

## Resumo

Adiciona suporte a múltiplos modelos de embedding para o RAG, com isolamento por
collection ChromaDB e testes A/B para comparação de qualidade de recuperação.

**Provedores adicionados:**
| Provedor | Modelo | API Key |
|----------|--------|---------|
| `default` | `all-MiniLM-L6-v2` (ChromaDB built-in) | — |
| `gemini` | `google/gemini-embedding-001` | `GEMINI_API_KEY` (já existente) |
| `openai` | `openai/text-embedding-3-large` | `OPENAI_API_KEY` (nova variável) |
| `qwen` | `qwen/qwen3-embedding-8b` via OpenRouter | `OPENROUTER_API_KEY` (nova variável) |

---

## Arquivos Modificados

### Novos arquivos
- `app/rag/embeddings.py` — Abstração de provedores de embedding
- `tests/test_embedding_ab.py` — Testes A/B (unitários + integração)
- `scripts/run_embedding_ab_test.py` — Script de comparação interativo

### Arquivos alterados
- `app/settings.py` — +3 variáveis de ambiente
- `app/rag/ingest.py` — Aceita `embedding_provider` param
- `app/rag/retriever.py` — Aceita `embedding_provider` param
- `.env.prod.example` — Documenta novas variáveis

---

## Variáveis de Ambiente Novas

```env
# EMBEDDING PROVIDER
# Opções: default | gemini | openai | qwen
EMBEDDING_PROVIDER=default

# Necessário apenas se EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=

# Necessário apenas se EMBEDDING_PROVIDER=qwen
OPENROUTER_API_KEY=
```

> **Nota:** `GEMINI_API_KEY` já existia e é reaproveitada para `EMBEDDING_PROVIDER=gemini`.

---

## Comportamento de Collections

Cada provedor usa uma **collection ChromaDB separada** porque vetores de modelos
diferentes são incompatíveis. O nome da collection é derivado do base name + sufixo:

```
rag_ba_rag_piloto_2026_01_v1          → default
rag_ba_rag_piloto_2026_01_v1_gemini   → gemini
rag_ba_rag_piloto_2026_01_v1_openai   → openai
rag_ba_rag_piloto_2026_01_v1_qwen     → qwen
```

> **Importante:** Ao trocar de `EMBEDDING_PROVIDER`, é necessário **re-ingerir** os
> documentos para popular a nova collection.

---

## Como Re-ingerir para um Novo Provedor

```bash
# 1. Configure a nova variável no .env
EMBEDDING_PROVIDER=gemini  # ou openai, qwen

# 2. Execute a ingestão
python -m app.rag.ingest data/knowledge_base/BA-RAG-PILOTO-2026.01.v1 --force

# 3. Valide a ingestão
python -m app.rag.retriever 'qual o horário de atendimento?'
```

---

## Como Executar o Teste A/B

```bash
# Instalar dependências (sem mudanças em requirements.txt)
pip install -r requirements.txt

# Rodar apenas testes unitários (sem API keys)
pytest tests/test_embedding_ab.py -v

# Rodar testes de integração (requer API keys)
pytest tests/test_embedding_ab.py -v -m integration

# Script de comparação interativo (todos os provedores disponíveis)
python scripts/run_embedding_ab_test.py

# Comparar apenas alguns provedores
python scripts/run_embedding_ab_test.py --providers default,gemini

# Salvar relatório em JSON
python scripts/run_embedding_ab_test.py --output /tmp/ab_results.json --verbose
```

---

## Compatibilidade com Sistema Atual

- **Zero impacto no sistema em produção**: `EMBEDDING_PROVIDER=default` (valor padrão)
  mantém exatamente o comportamento anterior.
- **Sem novas dependências** no `requirements.txt`: Gemini usa `google-genai` (já
  instalado). OpenAI e Qwen usam `httpx` (já instalado) diretamente via REST.
- **Retrocompatível**: `RAGRetriever()` e `ingest_base()` sem parâmetros continuam
  funcionando como antes.

---

## Aplicação no Servidor de Produção

**Não são necessárias ações imediatas** — a mudança é retrocompatível.

Caso queira testar um novo provedor em produção:

1. Adicione a API key correspondente ao `.env` do servidor
2. Configure `EMBEDDING_PROVIDER=<novo_provedor>`
3. Execute a ingestão: `python -m app.rag.ingest data/knowledge_base/... --force`
4. Reinicie o serviço: `sudo systemctl restart terezia-api`
5. Monitore fallbacks e scores nos logs
