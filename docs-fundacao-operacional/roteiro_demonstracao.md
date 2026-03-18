# Roteiro de Demonstração Técnica

## Objetivo
Fornecer um guia estruturado e replicável para apresentar os principais componentes da arquitetura ativa do **Chat Pref**, destacando soluções de engenharia para sistemas baseados em LLMs.

---

## Passo 1: Contextualização e Escopo (2 min)
**O que falar:**
- Apresentar o Chat Pref como uma plataforma de atendimento tenant-aware.
- O foco da arquitetura não é construir a interface mais bonita, mas sim uma base rastreável, governável e preparada para GenAI.
- Explicar a separação estrita da arquitetura:
  - **Pipeline Síncrono:** FastAPI, RAG Isolado, Guardrails imperativos.
  - **Fluxo Assíncrono/Offline (LLMOps):** Benchmark de respostas e avaliação de métricas (MLflow).

---

## Passo 2: Execução Local e Isolamento Multi-Tenant (3 min)
**O que focar:** `tenant_id` como contrato rígido.

**Ação:**
1. Subir a aplicação usando o setup mapeado para o ambiente local:
   ```bash
   docker compose up -d
   ```
2. Realizar uma requisição para a rota REST `/api/chat` **sem** o `tenant_id`, demonstrando a falha "fail-fast" exigida pelo guardrail sistêmico.
3. Fornecer o RAG com e sem escopo, evidenciando que coleções do ChromaDB recebem injeção por partição isolada.

---

## Passo 3: Rastreabilidade e Tracing (3 min)
**O que focar:** Telemetria nativa sem dependências de frameworks caixa-preta.

**Ação:**
1. Apresentar o cabeçalho de resposta contendo o `X-Request-ID`.
2. Acessar os arquivos locais de logs (`logs/trace_...jsonl`) e fazer um "grep" ou pesquisa por esse ID de requisição.
3. Mostrar que o ciclo de vida completo do atendimento foi registrado:
   - Chegada do request
   - Decisão da `policy_pre`
   - Recuperação Semântica (RAG)
   - Resposta candidata a geração (mock/gemini)
   - Decisão da `policy_post`

---

## Passo 4: Políticas Controladas e Fallback (2 min)
**O que focar:** Segurança de marca (Brand Safety) através de guardrails explícitos.

**Ação:**
1. Realizar o envio de uma mensagem propositalmente violadora com uma keyword banida localmente na configuração base da aplicação.
2. Demonstrar o runtime abortando o repasse ao LLM por meio da `PolicyDecision(deny)`.
3. Evidenciar como a plataforma retorna a mensagem padrão de *fallback* institucional, garantindo baixo custo arquitetural ao não acionar provedores comerciais atoa.

---

## Passo 5: CI/CD e Fechamento (2 min)
**O que focar:** Maturidade de Deploy.

**Ação:**
1. Mostrar o job de CI no GitHub limitando Pull Requests que quebrem a camada Semântica.
2. Demonstrar os artefatos de fumaça (Smoke Tests JSON) emitidos automáticos por ambiente (Dev/Prod).
3. Concluir revisando que a infraestrutura AWS (EC2/Terraform) reflete a espinha dorsal desta base consolidada.
