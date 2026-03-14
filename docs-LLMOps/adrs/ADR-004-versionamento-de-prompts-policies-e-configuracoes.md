# ADR-004 — Versionamento de Prompts, Policies e Configurações

## Status
Aceito

## Contexto

A Fase 1 do Chat Pref introduz uma camada formal de LLMOps com foco em rastreabilidade experimental, benchmark reproduzível, avaliação formal de RAG e governança de artefatos de IA.

Na fundação operacional, prompts, policies e parâmetros de retrieval já exercem papel relevante no comportamento do sistema. No entanto, à medida que a arquitetura evolui para suportar comparação entre versões, regressão de comportamento e tracking experimental, torna-se necessário tratar esses elementos como artefatos versionáveis e não apenas como configuração implícita.

Sem versionamento explícito, o projeto fica exposto a problemas como:
- dificuldade de reconstruir qual configuração gerou determinado resultado;
- comparação experimental sem contexto suficiente;
- regressão sem rastreabilidade;
- promoção de mudanças sem trilha clara de origem;
- acoplamento entre implementação e comportamento sem contrato documental.

## Decisão

O projeto passa a tratar **prompts, policies e configurações críticas do pipeline de IA** como artefatos versionáveis, com identificação explícita e associação obrigatória aos contextos de avaliação, comparação e execução experimental.

Isso inclui, quando aplicável:
- prompts de sistema;
- prompts de composição;
- prompts de fallback;
- policies pre e post;
- configurações de retrieval;
- parâmetros relevantes de chunking;
- parâmetros de top_k;
- estratégia de reranking;
- dataset de benchmark;
- versão da base vetorial.

## Justificativa

A decisão foi tomada pelos seguintes motivos:

1. **rastreabilidade**
   O projeto precisa saber, com precisão, qual combinação de artefatos produziu determinado comportamento.

2. **comparabilidade**
   Sem versionamento explícito, não existe base técnica suficiente para comparar experimentos.

3. **governança**
   Alterações em prompt, retrieval ou policy devem ser tratadas como mudança arquitetural relevante, não como ajuste informal.

4. **reprodutibilidade**
   A avaliação do pipeline depende da capacidade de reexecutar ou reconstruir um contexto anterior.

5. **alinhamento com a Fase 1**
   A maturidade buscada nesta etapa exige controle sobre os elementos que mais influenciam a resposta final.

## Escopo da decisão

A decisão cobre o versionamento lógico e documental dos seguintes grupos de artefato:

### 1. Prompts
- prompt de sistema
- prompt de composição
- prompt de fallback
- prompts auxiliares, quando existirem

### 2. Policies
- policy pre
- policy post
- regras textuais ou declarativas associadas ao comportamento de segurança, bloqueio ou fallback

### 3. Configurações de retrieval
- top_k
- chunking
- estratégia de busca
- query rewriting / query expansion
- reranking
- configuração de base vetorial, quando aplicável

### 4. Artefatos de avaliação
- dataset de benchmark
- versão de base vetorial usada em avaliação
- conjunto de parâmetros experimentais relevantes

## Regras de adoção

A adoção desta decisão deve seguir as regras abaixo.

### 1. Nenhum resultado sem versão
Nenhuma execução experimental relevante deve existir sem associação a versões explícitas dos artefatos que a influenciam.

### 2. Versão como metadado obrigatório
Versões devem ser tratadas como metadados obrigatórios em tracking, benchmark e comparação entre runs.

### 3. Mudança de comportamento exige nova versão
Sempre que uma alteração impactar comportamento observável do pipeline, uma nova versão deve ser registrada.

### 4. Convenção consistente
A nomenclatura das versões deve seguir convenção estável, legível e correlacionável.

### 5. Promoção controlada
Mudanças em artefatos versionáveis devem passar por critério mínimo de comparação antes de promoção.

## Alternativas consideradas

### 1. Manter versionamento implícito por commit
Rejeitada.

Motivo:
- insuficiente para rastreabilidade prática da camada de IA;
- dificulta leitura por experimento;
- não resolve bem a correlação entre comportamento e configuração.

### 2. Versionar apenas prompts
Rejeitada.

Motivo:
- retrieval, policy e benchmark também alteram comportamento do sistema;
- versionar apenas prompt gera visão parcial e enganosa.

### 3. Versionar prompts, policies e configurações críticas
Aceita.

Motivo:
- melhor aderência à necessidade real de governança e comparação da fase.

## Consequências

### Positivas
- maior rastreabilidade de comportamento;
- melhor qualidade de benchmark e regressão;
- clareza na comparação entre versões;
- fortalecimento da camada de experimentação;
- suporte melhor à explicabilidade técnica.

### Negativas / trade-offs
- aumento da disciplina necessária para registrar mudanças;
- necessidade de convenção estável de naming;
- mais metadados para manter de forma consistente.

## Impacto na arquitetura

A partir desta decisão:
- a arquitetura da fase passa a tratar esses artefatos como contratos versionáveis;
- tracking experimental deve registrar suas versões;
- benchmark e avaliação devem referenciar explicitamente o contexto versionado;
- governança e explicabilidade passam a depender dessa trilha.

## Impacto na implementação

Esta decisão implica:
- criação de convenção de versionamento;
- inclusão de metadados versionados em runs e avaliações;
- revisão de pontos do pipeline onde a configuração precisa ser explicitada;
- integração da versão dos artefatos com MLflow e benchmark.

## Impacto na documentação

A partir desta decisão:
- planejamento deve refletir a fase de versionamento como fundacional;
- arquitetura deve tratar versionamento como contrato transversal;
- runbooks de avaliação devem exigir identificação das versões;
- documentação de governança deve citar os artefatos cobertos por esta ADR.

## Relação com outras decisões

Esta ADR se conecta diretamente com:
- separação entre auditoria operacional e tracking experimental;
- adoção de MLflow como stack de experimentação;
- necessidade de benchmark reproduzível.

## Referências internas
- `docs-LLMOps/CONTEXTO-LLMOps.md`
- `docs-LLMOps/ARQUITETURA-LLMOps.md`
- `docs-LLMOps/PLANEJAMENTO_LLMOps.md`
- `docs-LLMOps/runbooks/avaliacao-rag.md`
- `docs-LLMOps/adrs/ADR-001-separacao-auditoria-vs-tracking.md`
- `docs-LLMOps/adrs/ADR-002-mlflow-como-stack-de-experimentacao.md`