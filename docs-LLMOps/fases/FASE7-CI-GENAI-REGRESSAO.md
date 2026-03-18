# Fase 7 - CI de GenAI com Regressão de Prompt e Dry-Run Experimental (CONCLUÍDA)

## Status e Resumo do Fechamento
**Status: Concluída tecnicamente na branch `feat/ci-genai-regressao`**

Esta fase entregou um framework de validação assíncrono para os Pull Requests sem infligir os hard-limits de custo operacional e rate-limits. Foram cumpridos os objetivos de separação de *tracking* vs *auditoria*, isolamento de tenant mantido e integração realística do Ragas via ambiente local simulado.

**Entregue:**
* Job `genai-dry-run` integrado ao pipeline principal em `.github/workflows/ci.yml`.
* Avaliação reduzida com `--max-cases 3` utilizando `LLM_PROVIDER=mock`, permitindo o teste das integrações sem chamadas as APIs de GenAI pagas.
* Registro de experimentação capturado num runtime efêmero com isolamento ao Action (SQLIte DB exportado como *artifact* `genai-ci-mlflow-tracking`).
* Gate automatizado customizado em `scripts/evaluate_genai_ci_gate.py` travando o merge no caso de erro na coleta da base ou quebras em prompts.
* Diferenciação de limites bem estabelecida em manual de políticas.

**Preparado:**
* A arquitetura sublinhada no `.yml` permite adoção futura de provedores reais ou datasets extensos através de simples injeções via Github Secrets.
* Integração base (MLflow) configurado em *append* ou via SQL URI, prevendo a viabilidade de repositório Cloud mantido remotamente se e quando necessário na Fase correspondente.

**Fora de escopo (Não contemplado nesta fase):**
* Avaliação semântica fina real. (A atual está propositalmente enviesada para 0.0 pelas alucinações matemáticas devido ao mock).
* Substituição/Over-ride da métrica `faithfulness` em regime bloqueante.
* Rastreamento acoplado ao *runtime* transacional de operação na raiz: tracking experimental continua asséptico ao RAG principal.

---

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
