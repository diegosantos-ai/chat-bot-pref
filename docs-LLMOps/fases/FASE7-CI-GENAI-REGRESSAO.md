# Fase 7 - CI de GenAI com Regressão de Prompt e Dry-Run Experimental

## Metodologia de Recorte de PR (Benchmark Reduzido)

### Por que esse recorte existe?
Para prover um mecanismo de feedback ultra-rápido no *continuous integration* sem a latência e o custo computacional atrelado a um dataset de benchmark completo ou requisições à APIs externas reais.

### O que ele cobre?
- **Parse estrutural:** Garante que a árvore JSON, prompts `.txt` e schemas de chunking/retrieval versionados continuam válidos (`ActiveArtifactResolver`).
- **Dry-run experimental:** Garante que a integração de tracking de métricas via `MLflow` finaliza corretamente.
- **RAG end-to-end com Mock:** Avalia todo o ecossistema RAG local usando amostras locais (`--max-cases 3` em `prefeitura-vila-serena`) interceptado por um provider genérico (`mock`), simulando sucesso sem custo externo.

### O que ele não cobre?
- **Desvios sutis de Inteligência Artificial:** Não avalia com exatidão taxas profundas de *Faithfulness* ou *Relevance* sistêmica devido ao modelo cru (`LLM_PROVIDER=mock`).
- **Dataset Full-Scale:** Avalia apenas uma franja microscópica da base de dados (3 casos) por questões arquiteturais de *timeout/fail-fast*.
