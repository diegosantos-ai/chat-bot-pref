# Fase 11: Governança, Explicabilidade e Evidência de Decisão

## 1. O Problema
Com a expansão de estratégias de RAG (Multi-LLM, Fallback, Guardrails textuais, e múltiplas policies), uma resposta ao final da API de Chat era opaca se a rastreabilidade precisasse ser auditada.

**Até a Fase 10:**
- Entendíamos *qual* LLM gerou a resposta no experimental (MLFlow).
- O log tinha chaves, mas a decisão final e suas versões atreladas não viajavam na resposta HTTP de maneira coerente e canônica para observabilidade transacional.

## 2. A Solução: Contrato de Evidência
Criamos uma estrutura de `AuditEvidence` injetada como opcional no `ChatResponse` (e formalizada na camada HTTP).
O foco dessa estrutura é responder **apenas**:
1. Quem atendeu? (Tenant, Request)
2. Foi com sucesso ou bloqueado? (`DecisionStatus`)
3. Qual a causa raiz do caminho escolhido? (`ReasonCode`)
4. Quais as configurações *exatas* aplicadas? (Versão de Prompt, Versão de Policy, Qual estratégia de Retrieval)
5. Metadados resumidos de modelo (ex: usou GPT-4o-mini ou Fallback Mock).

## 3. Delimitação Operacional vs Experimental

### 3.1 O que vai para Evidência Operacional (`AuditEvidence`)
A evidência acompanha o request HTTP quando solicitado ou no fluxo normal (no futuro):
- **Razão da resposta**: Sucesso Normal, Sucesso em Fallback, Bloqueio por Policy Pre/Post, Limitação por Falta de Contexto.
- **Identidade do Motor**: Qual prompt e versão foi usada (ex: `v2-cot-system`).
- **Resumo**: Foi recuperado documento? Se sim, a contagem de documentos. NENHUM conteúdo do documento é trafegado de volta e NENHUMA métrica como `latency_ms` da chamada do provedor passa aqui.

### 3.2 O que PERMANECE no Experimento MLOps (MLFlow / RAGas)
- Custos exatos de tokens (só transacional interno ou offline report, via LangSmith / MLFlow).
- Latência em milissegundos por layer (vai para OpenTelemetry/Prometheus/MLFlow).
- Scores RAGas (Answer Relevancy, Faithfulness). Isso nunca deve transbordar para evidência transacional de um usuário num chat, não faz sentido lógico e acopla a latência do app ao loop de avaliação offline.

## 4. Status de Definição (Blocos 1 e 2)
Neste ciclo entregamos a funcionalidade fim a fim:
- **Contrato Estrutural DTO**: Definido e integrado de forma opcional (`app/contracts/evidence.py` -> `AuditEvidence`).
- **Reason Codes Dinâmicos**: Catalogadas as razões lógicas (Fallback, Limitado, Bloqueio, Sucesso Normal).
- **Core de Orquestração Reativo**: O orquestrador (`chat_service`) passou a inferir, em tempo de execução, metadados contextuais (ex: se o Fallback triggou `NO_KNOWLEDGE_BASE` com 0 documentos; se o RAG falhou em semântica com 3 documentos recuperados; ou se a IA principal respondeu com sucesso) amarrando isso tudo transparentemente na API JSON.

## 5. Fechamento vs Fora de Escopo
Foram concluídas as mecânicas de observabilidade aplicadas à requisição HTTP ativa. **Ficaram fora de escopo (preservando fronteiras arquiteturais)**:
- Métricas experimentais como Faithfulness, Answer Relevancy;
- Análise de Token/Latência em sub-nós (estes continuam segregados em log / OpenTelemetry).
