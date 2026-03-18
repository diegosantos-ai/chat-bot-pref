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

## 4. Status de Definição (Bloco 1)
Neste bloco entregamos:
- **Contrato Estrutural DTO**: Definido e integrado de forma opcional (`app/contracts/evidence.py` -> `AuditEvidence`).
- **Reason Codes**: Catalogadas as razões de decisão lógicas (Fallback, Limitado, Bloqueio).
- **Sem preenchimento reativo ativo ainda**: O core de orquestração (`chat_service`) **NÃO** popula o `AuditEvidence` até que esta fase amadureça como componente reativo, respeitando a instrução "preparar e não declarar entregue o que está incompleto". O DTO foi apenas anexado sem injetar dependência forte na pipeline ativa.

## 5. Próximos Passos
- Implementar a agregação da evidência na jornada do orquestrador (`chat_service.py`), construindo iterativamente e respeitando o RAG Tenant.
- Vincular a saída JSON real nos Logs transacionais e garantir a resposta no Postman/Webhook com o Evidence object.
