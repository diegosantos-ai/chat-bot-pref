# ADR-006 — Deriva Semântica como Sinal Operacional

## Status
Aceito

## Contexto

A Fase 1 do Chat Pref introduz avaliação formal de RAG, benchmark por tenant, experiment tracking, versionamento de artefatos e orquestração offline.

Com essa evolução, o projeto passa a depender não apenas da qualidade do modelo ou do prompt, mas também da qualidade semântica da base de conhecimento utilizada por cada tenant. Em uma arquitetura multi-tenant, a degradação da base vetorial pode ocorrer por múltiplos fatores, entre eles:

- ingestão documental inconsistente;
- chunking inadequado;
- reindexação mal calibrada;
- atualização da base sem controle comparativo;
- aumento de ruído documental;
- perda de aderência entre perguntas recorrentes e contexto recuperado.

Sem tratar esse fenômeno como sinal operacional explícito, o projeto corre risco de atribuir piora de resposta ao modelo, ao prompt ou ao retrieval quando o problema real está na qualidade semântica da base.

## Decisão

O projeto passa a tratar **deriva semântica** como um sinal operacional relevante da Fase 1, passível de observação, registro e análise por tenant.

Deriva semântica, no contexto do Chat Pref, será entendida como deterioração mensurável da capacidade da base documental e do pipeline de recuperação de sustentar respostas adequadas, relevantes e consistentes ao longo do tempo.

## Justificativa

A decisão foi adotada pelos seguintes motivos:

1. **coerência com arquitetura multi-tenant**
   Cada tenant possui base documental própria e, portanto, pode degradar de forma independente.

2. **melhor diagnóstico de falha**
   Tratar deriva semântica explicitamente ajuda a distinguir problemas de base, retrieval, prompt ou modelo.

3. **alinhamento com benchmark por tenant**
   A avaliação formal só produz valor pleno quando também permite detectar perda de qualidade ao longo do tempo.

4. **governança da camada RAG**
   A base vetorial precisa ser tratada como ativo versionável e monitorável, não como componente estático presumidamente saudável.

5. **operabilidade**
   Sem esse sinal, a manutenção da qualidade do sistema tende a ficar dependente de percepção subjetiva e análise reativa.

## Escopo da decisão

Esta decisão cobre:

- leitura da saúde semântica da base vetorial;
- comparação entre versões de base e configuração de ingestão;
- benchmark recorrente por tenant;
- sinais de piora em recuperação e resposta;
- apoio à decisão de reindexar, revisar ingestão ou recalibrar retrieval.

## Definição operacional

Para esta fase, deriva semântica deve ser tratada como hipótese sustentada por evidência, e não como impressão informal.

Ela pode ser sinalizada por combinação de fatores como:

- queda de métricas de benchmark;
- piora de `faithfulness` ou `answer_relevance`;
- aumento de retrieval vazio;
- aumento de fallback;
- piora do contexto recuperado em cenários antes estáveis;
- degradação localizada em tenant específico;
- queda após mudança de base, chunking ou indexação.

## Regras de adoção

### 1. Sempre por tenant
A análise de deriva semântica deve preservar o recorte por tenant.

### 2. Sempre comparativa
Nenhum diagnóstico de deriva deve existir sem comparação contra baseline ou versão anterior válida.

### 3. Sempre contextualizada
A leitura deve considerar também:
- versão da base vetorial;
- configuração de retrieval;
- versão do prompt;
- política aplicada;
- dataset de benchmark.

### 4. Sempre sustentada por evidência
Deriva semântica não deve ser declarada apenas por sensação de piora ou por caso isolado.

### 5. Sempre tratada como sinal operacional
Mesmo quando detectada em benchmark, a deriva deve informar ação concreta de operação, avaliação ou revisão técnica.

## Alternativas consideradas

### 1. Tratar piora de resposta apenas como problema de prompt ou modelo
Rejeitada.

Motivo:
- simplifica excessivamente o problema;
- ignora o papel central da base vetorial no comportamento do sistema;
- prejudica diagnóstico correto.

### 2. Não formalizar deriva semântica nesta fase
Rejeitada.

Motivo:
- enfraquece a governança da camada RAG;
- reduz capacidade de manutenção da qualidade;
- dificulta explicação de regressões por tenant.

### 3. Tratar deriva semântica como sinal operacional explícito
Aceita.

Motivo:
- melhora a leitura da saúde do sistema;
- fortalece benchmark e reindexação controlada;
- aumenta maturidade da fase LLMOps.

## Consequências

### Positivas
- melhor diagnóstico de degradação;
- maior clareza sobre quando reindexar ou revisar ingestão;
- melhor correlação entre benchmark e operação;
- fortalecimento da governança da base vetorial;
- maior aderência ao princípio de GenAI com método.

### Negativas / trade-offs
- necessidade de benchmark mais disciplinado;
- aumento da responsabilidade sobre versionamento da base vetorial;
- maior complexidade de análise em comparação a uma leitura puramente agregada.

## Impacto na arquitetura

A partir desta decisão:
- a arquitetura da fase deve tratar a base vetorial como ativo monitorável;
- a camada offline ganha relevância para benchmark recorrente e análise de saúde semântica;
- tracking experimental deve registrar contexto suficiente para suportar comparação;
- benchmark por tenant passa a servir também como instrumento de monitoramento.

## Impacto na implementação

Esta decisão implica:
- registrar versão da base vetorial e configuração de ingestão quando aplicável;
- comparar benchmark entre versões de base;
- mapear sinais de piora operacional por tenant;
- integrar análise de deriva às rotinas offline e à leitura de benchmark.

## Impacto na documentação

A partir desta decisão:
- planejamento deve incluir fase específica de deriva semântica;
- arquitetura deve posicionar o tema como capacidade da camada offline e de avaliação;
- runbooks de avaliação devem considerar leitura de degradação;
- futuras documentações operacionais devem contemplar ações de resposta ao sinal.

## Relação com outras decisões

Esta ADR se conecta diretamente com:
- benchmark por tenant como contrato de avaliação;
- adoção de MLflow como stack de experimentação;
- versionamento de prompts, policies e configurações;
- adoção de Airflow como orquestrador offline.

## Referências internas
- `docs-LLMOps/CONTEXTO-LLMOps.md`
- `docs-LLMOps/ARQUITETURA-LLMOps.md`
- `docs-LLMOps/PLANEJAMENTO-LLMOps.md`
- `docs-LLMOps/runbooks/avaliacao-rag.md`
- `docs-LLMOps/runbooks/operacao-airflow.md`
- `docs-LLMOps/adrs/ADR-002-mlflow-como-stack-de-experimentacao.md`
- `docs-LLMOps/adrs/ADR-003-airflow-como-orquestrador-offline.md`
- `docs-LLMOps/adrs/ADR-004-versionamento-de-prompts-policies-e-configuracoes.md`
- `docs-LLMOps/adrs/ADR-005-benchmark-por-tenant-como-contrato-de-avaliacao.md`
