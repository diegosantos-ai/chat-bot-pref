# ADR-005 — Benchmark por Tenant como Contrato de Avaliação

## Status
Aceito

## Contexto

A Fase 1 do Chat Pref introduz avaliação formal do pipeline RAG, experiment tracking e comparação entre versões de prompts, policies, retrieval e base vetorial.

Como o projeto é multi-tenant, o comportamento do sistema não pode ser avaliado apenas por um conjunto genérico de perguntas. Cada tenant pode apresentar:
- base documental distinta;
- padrões de pergunta distintos;
- sensibilidade diferente a fallback e baixa confiança;
- risco diferente de degradação semântica;
- impacto diferente para mudanças em retrieval, prompt ou policy.

Sem um benchmark por tenant, o projeto corre risco de:
- mascarar regressões locais com médias agregadas;
- promover mudanças que melhoram um tenant e pioram outro;
- perder capacidade de explicar degradações específicas;
- reduzir a validade da avaliação formal em ambiente multi-tenant.

## Decisão

O projeto adota **benchmark por tenant** como contrato estrutural de avaliação da Fase 1.

Toda avaliação formal relevante do pipeline RAG deve considerar o tenant como unidade explícita de referência, seja por benchmark dedicado, seja por recorte lógico claro dentro de um benchmark maior versionado.

## Justificativa

A decisão foi adotada pelos seguintes motivos:

1. **tenant-awareness como requisito estrutural**
   O projeto não pode misturar avaliação entre tenants como se fossem um mesmo sistema semântico.

2. **maior fidelidade de avaliação**
   A qualidade do pipeline depende fortemente da base documental e do contexto institucional do tenant.

3. **melhor capacidade de diagnóstico**
   Benchmark por tenant facilita identificar se a degradação vem de base, retrieval, prompt ou policy.

4. **maior segurança na promoção de mudanças**
   Mudanças deixam de ser promovidas por média global e passam a ser avaliadas em recortes mais realistas.

5. **coerência com a arquitetura multi-tenant**
   Se a operação é segregada por tenant, a avaliação também deve ser.

## Escopo da decisão

Esta decisão cobre:
- benchmark usado para avaliação formal;
- benchmark usado para regressão;
- benchmark usado para comparação entre versões;
- benchmark usado para detectar deriva semântica;
- benchmark usado em validação de mudanças relevantes no pipeline.

## Regras de adoção

### 1. Tenant explícito
Toda execução de benchmark deve declarar explicitamente o `tenant_id` avaliado.

### 2. Recorte institucional válido
O conjunto de avaliação deve refletir perguntas, contexto e comportamento plausíveis para o tenant.

### 3. Versionamento obrigatório
O benchmark deve possuir `dataset_version` e contexto de artefatos associados.

### 4. Comparação homogênea
Comparações entre runs só devem ser tratadas como válidas quando realizadas sobre benchmark compatível.

### 5. Média global não substitui leitura local
Indicadores agregados podem existir, mas não substituem leitura por tenant.

## Alternativas consideradas

### 1. Um benchmark único global para todos os tenants
Rejeitada.

Motivo:
- simplifica demais o problema;
- oculta regressões locais;
- enfraquece a avaliação em contexto multi-tenant.

### 2. Avaliação apenas qualitativa por amostragem
Rejeitada.

Motivo:
- insuficiente para regressão controlada;
- pouco reprodutível;
- fraca como contrato técnico.

### 3. Benchmark por tenant como contrato estrutural
Aceita.

Motivo:
- melhor aderência à arquitetura do projeto;
- melhor governança de qualidade;
- melhor sustentação para explicação técnica.

## Consequências

### Positivas
- avaliação mais realista;
- maior precisão diagnóstica;
- melhor segurança na promoção de mudanças;
- melhor leitura de degradação semântica;
- coerência com segregação multi-tenant.

### Negativas / trade-offs
- maior esforço para construção e manutenção do benchmark;
- necessidade de curadoria por tenant;
- maior disciplina na organização dos datasets.

## Impacto na arquitetura

A partir desta decisão:
- benchmark deixa de ser genérico e passa a ser tratado como artefato contextualizado por tenant;
- experiment tracking deve registrar `tenant_id` e `dataset_version`;
- deriva semântica passa a depender de leitura local por tenant;
- comparação entre estratégias deve respeitar recorte institucional.

## Impacto na implementação

Esta decisão implica:
- modelagem do benchmark com recorte por tenant;
- definição de convenção de dataset versionado;
- revisão dos fluxos de avaliação para garantir isolamento lógico;
- possibilidade de benchmark mínimo por tenant e expansão incremental posterior.

## Impacto na documentação

A partir desta decisão:
- o planejamento deve tratar benchmark por tenant como fundacional;
- a arquitetura deve explicitar benchmark como componente contextual;
- runbooks de avaliação devem exigir identificação do tenant avaliado;
- futuras ADRs sobre deriva semântica e regressão devem respeitar esta base.

## Relação com outras decisões

Esta ADR se relaciona diretamente com:
- separação entre auditoria e tracking experimental;
- adoção de MLflow como stack de experimentação;
- versionamento de prompts, policies e configurações;
- futura detecção de deriva semântica.

## Referências internas
- `docs-LLMOps/CONTEXTO-LLMOps.md`
- `docs-LLMOps/ARQUITETURA-LLMOps.md`
- `docs-LLMOps/PLANEJAMENTO-LLMOps.md`
- `docs-LLMOps/runbooks/avaliacao-rag.md`
- `docs-LLMOps/adrs/ADR-001-separacao-auditoria-vs-tracking.md`
- `docs-LLMOps/adrs/ADR-002-mlflow-como-stack-de-experimentacao.md`
- `docs-LLMOps/adrs/ADR-004-versionamento-de-prompts-policies-e-configuracoes.md`
