# Fase 9 — Deriva Semântica e Saúde da Base Vetorial

## Contexto e Objetivo

Este documento registra a fundação diagnóstica da **Fase 9**, focada em criar mecanismos para detectar a degradação da qualidade semântica da base documental.

Operamos sob os seguintes princípios:
- **Tenant-aware**: Toda análise de degradação e saúde se dá isolada por tenant.
- **Isolamento de contextos**: Auditoria operacional (logs de atendimento real), tracking experimental (MLflow), benchmark offline e runtime transacional não devem se misturar.
- **Sem novas dependências**: Aproveita-se unicamente a evolução instrumental viabilizada pelas fases anteriores.

Esta entrega consolida a primeira etapa da fase e garante a visão clara sobre o que é desgaste semântico no RAG do projeto.

---

## 1. Indicadores de Saúde Semântica da Base (CPPX-F9-T1)

O que caracteriza a "saúde" de uma base vetorial neste projeto não é a capacidade de responder qualquer coisa, mas quão alinhada a base está com os cenários reais demandados pelo tenant. A saúde semântica perde qualidade (sofre *deriva*) quando o espaço vetorial configurado já não aproxima razoavelmente as "dúvidas reais" dos "documentos de referência".

Para isso, definem-se três dimensões operacionais observáveis:

### 1.1 Cobertura de Retrieval (Hit Rate Semântico)
- **O que é**: O percentual de vezes em que uma query (com as mesmas características de queries de benchmark conhecidas) obtém resultados de alta similaridade na busca nativa (score via Chroma ou fallback híbrido).
- **Indicador**: Distribuição de scores brutos de distância no RAG. Um aumento contínuo da distância semântica na distribuição final do *Top K* é o primeiro indicador de base envelhecida.

### 1.2 Estabilidade do Zero-Shot e Recusa Controlada
- **O que é**: O aumento da taxa de recusa legítima da lógica de fallback (`policy_post` ou guardrail) e respostas "Não sei" devido à falta de contexto útil no retrieval.
- **Indicador**: `% de Respostas Sem Contexto no RAG` via auditoria de logs. Se sobe bruscamente com a mesma base e configuração, os usuários reais estão perguntando coisas para as quais a base indexada original não tem match adequado.

### 1.3 Alinhamento de Intenção RAG (Relevance Decay)
- **O que é**: Quantificação de como o `rag_hit_rate` num mesmo dataset temporal de benchmark se comporta ao longo dos meses contra o mesmo corpus.

---

## 2. Versionamento de Base Vetorial e Ingest Config (CPPX-F9-T2)

Para garantir que a performance semântica de uma base é reprodutível ou diagnosticável, a base populada é tratada como um snapshot no tempo.

### 2.1 Contrato Mínimo de Snapshot
Uma "Base Vetorial Versão X" para o Tenant Y requer metadados que formem um hash combinando:
- **`tenant_id`**: O escopo dos dados de consulta.
- **`dataset_version` / `corpus_reference`**: Versão temporal dos arquivos-fonte do tenant (ex: `dataset_docs_v3`).
- **`chunking_config`**: Referência resolvida via artefatos (ex: da store `ai_artifacts/rag/chunking/`).
- **`embedding_model`**: As propriedades e versões da representação matricial usada na ingestão.

### 2.2 Estrutura do Snapshot de Ingestão (Definição de Objeto)
Não reimplementaremos a base. A arquitetura passa a tratar este metadado durante a transição do lifecycle offline. Todo re-index gera um registro na tracking store ou arquivo estático de manifesto de RAG:
```json
{
  "tenant_id": "prefeitura-demo",
  "vector_base_version": "v_epoch",
  "timestamp": "2026-03-18T10:00:00Z",
  "components": {
    "corpus_reference": "doc_base_folder_v3",
    "chunking_artifact": "chunking_config.paragraph_split.paragraph_split_v1...",
    "embedding_model": "text-embedding-3-small"
  },
  "metrics_at_ingest": {
    "total_chunks": 412,
    "total_documents": 14
  }
}
```
Isso permite isolar testes se, por exemplo, a mesma query gera score menor apenas mudando a *vector_base_version* (mantendo modelo de LLM estático).

---

## 3. Mapeamento de Sinais Operacionais de Degradação (CPPX-F9-T4)

O runtime transacional principal transborda sinais essenciais para diagnóstico, coletados passivamente pelos mecanismos de `audit.v1` e OpenTelemetry.

Sinais diretos da atual arquitetura:
1. **Falha estrutural de Transação (`/api/chat`)**: O log emite erros ou timeouts no acesso à camada de DB. Isto não é deriva, é incidente técnico.
2. **Taxa de acionamento do Guardrail / Retenção Pré-Post**: Falhas sistêmicas na obtenção de chunks levam o modelo a alucinar na tentativa e erro. A "Policy Decision" barrea respostas muito frequentemente.
3. **Escassez do Context**: Observado no `audit_repository`, quando `context_chunks` frequentemente reporta zero ou baixa cardinalidade no RAG mesmo sob uma query que antigamente populava 3 a 5 items.

---

## 4. Matriz: Sintomas vs Causas Prováveis por Tenant (CPPX-F9-T5)

Como discernir a origem de uma resposta degradada no ecossistema atual? Utilizamos a seguinte matriz de correlação baseada nos domínios independentes do sistema:

| Relato / Sintoma Observado | Evidência Técnica (Logs e Tracking) | Causa Provável Diagnóstica | Acionamento |
| :--- | :--- | :--- | :--- |
| **"O bot inventou algo (Alucinação)"**. | Offline Evaluation acusa baixo score em *Faithfulness*. Os chunks recuperados pela run **não continham** o fato respondido. | **Modelo/Prompt Ruim**: A LLM não obedeceu as boundaries de contenção aos chunks entregues. | Atualizar os prompts na camada de AI Artifacts. |
| **"O bot não soube informar uma lei vigente"** (Falso Negativo). | A lei está nos arquivos brutos do bot, mas os `context_chunks` extraídos via Chroma retornaram vazios ou de baixo score ao auditar a request. | **Problema de Chunking ou Similaridade / Estratégia de Retrieval**. | Refazer testes com variados parâmetros de Chunking/Retrieval no ambiente Experimental. |
| **"O bot informou dados da gestão passada"**. | O avaliador confirma acerto factual. O RAG recuperou os chunks que **estão indexados**, e o modelo interpretou certo os chunks. | **Base Ruim / Desatualizada (Deriva)**: O sistema respondeu excelentemente ao fato do ano passado. O "mundo virou" e a base estagnou. | Execução restrita da DAG de Ingest com nova atualização do Corpus do Tenant. |
| **Timeout Frequente para os cidadãos do Tenant**. | Logs indicam latência brutal nos spans do serviço LLM ou Vectorstore, independente da query. | **Infraestrutura / Custo Oculto** (Não é erro semântico). | Investiga rede, rate limits de API ou scaling via cloud. |

---

## 5. Narrativa Técnica Inicial de Deriva Semântica (CPPX-F9-T7 Parte 1)

A deriva semântica não se trata de um "bug" introduzido por um mal push do fluxo CI/CD; ela é a progressiva fricção entre a evolução orgânica das necessidades reais de atendimento e a petrificação do setup vetorial/de conhecimentos no instante da indexação.

O ecossistema prevê o seguinte framework temporal:
1. O Tenant `t-alpha` nasce e injeta sua base (Dia 1). Os dados são convertidos numa `vector_base_version`.
2. Após alguns meses, os `request_id` daquele tenant, antes satisfeitos, começam a acumular policy blocks ou retornos de contexto empobrecido (Observabilidade aponta a Drift).
3. O diagnóstico usa a matriz de correlação. Se inferido envelhecimento, atua-se na camada Offline/Airflow para uma ingestão controlada (Dia N), criando uma nova *version of index*.
4. A nova *base vetorial* é submetida ao Dataset de Benchmark do tenant no sistema de Experimentos MLflow comparada ao branch `main`, validando se hit-rate retomou o nível ideal antes de ser comissionada online.

---

## 6. Protocolo de Comparação entre Versões de Base (CPPX-F9-T3)

A degradação não é um palpite empírico; a recuperação da relevância precisa ser provada. Para garantir que uma reindexação trará vantagem pragmática, o protocolo experimental deve respeitar balizas bem delineadas.

### 6.1 Unidade de Comparação
Qualquer "Run" experimental que avalia melhoria de RAG devido à correção da Deriva Semântica DEVE declarar no tracking os seguintes componentes para ser válida:
- **`tenant_id` alvo**: A análise de RAG é intransferível entre prefeituras.
- **Snapshot do Corpus**: Qual a tag dos arquivos-fonte do teste (ex: leis_2025 vs leis_2026).
- **Configuração de Ingestão**: Versão do `chunking_artifact` utilizado.
- **Configuração de Retrieval**: A estratégia ativa consumida pelo pipeline.

### 6.2 Baseline de Referência
A baseline de comparação não é o melhor resultado de ontem, mas o **snapshot estrutural que atende a produção hoje**. Para avaliar uma nova base, testa-se a "base antiga produtiva" contra "dataset de fallback autônomo atualizado", e em seguida compara-se a performance do "novo corpus indexado" contra o mesmo dataset.

### 6.3 Regras de Interpretação (Métricas)
Utiliza-se o arcabouço avaliativo introduzido via MLflow nas fases pretéritas:
- **Oscilação Tolerável**: Variações relativas de ~5% no hit-rate de chunks corretos entre a base atual e a nova base.
- **Regressão Relevante**: Queda persistente de pontuação em *Relevance* ou scores densos e baixos na recuperação estrita da vectorstore comparado com a performance histórica documentada.
- **Vitória de Reindexação**: A nova combinação (corpus recente + config de chunking estabilizada) resgata o *rag_hit_rate* da amostra atual acima da base produtiva envelhecida.

---

## 7. Rotina Mínima de Reavaliação (CPPX-F9-T6)

A rotina de reavaliação diz como a operação transiciona de "observar" para "atuar".

### 7.1 Critérios de Disparo (Triggers Mínimos)
Na configuração presente, o time deve enfileirar reavaliação por tenant quando um destes fatores isolados transborda:
1. **Pico Sintomático de Recusa**: Saltos observáveis (ex: >15% no mês) nas *policy blocks* registradas via `audit.v1` associadas a relatórios de *zero-context chunks* para o RAG.
2. **Denúncia Qualitativa Relevante**: A moderação do Tenant (prefeitura) notifica ou reencaminha interações com desinformação contumaz advindas de atualização gerencial (uma secretaria mudou mas o RAG desconhece).
3. **Turnover Legislativo**: Tempo decorrido vs. publicações da praça. Mesmo sem queda de hit-rate, uma "reindexação forçada" na virada fiscal é justificada sem trânsito preditivo.

### 7.2 Orquestração Offline vs Runtime
A segregação entre os limites do modelo permanece vital:
- **Ação Online (Runtime)**: FastAPI no ambiente transacional serve apenas instâncias de requisição. Ele **nunca** calcula comparativos MLflow, **nunca** efetua `upsert` colossal de bases guiado pelo usuário final e não mede sua própria deriva retroativa no request context.
- **Ação Offline Primária**: De forma manual, engenheiros disparam a reindexação no CLI/scripts e envidenciam nos repositórios experimentais usando a DAG de "re-ingestion".
- **Camada Airflow**: Tendo base na Fase 8, a observabilidade contínua (rodar `eval` sobre as log-queries noturnas) **pode e deve** ser encapsulada como uma DAG agendada cronologicamente na plataforma do Apache Airflow que opera alijada do path da API principal.

---

## 8. Narrativa Técnica Consolidada (Fechamento CPPX-F9-T7)

Para a plataforma **Chat Pref**, a Deriva Semântica não configura um *bug estrutural de software* introduzido por deploys arbitrários. Trata-se da degeneração termodinâmica provinda do contínuo distanciamento temporal entre a **base de dados indexada e cristalizada** (o vetor RAG inicial da Prefeitura) e a contínua fluência do **real comportamento orgânico e linguístico** das demandas da população atendida.

Conforme a prefeitura dita novas portarias, o cidadão usa semânticas diferentes de busca, ou os prefeitos migram políticas públicas, os *embeddings* outrora correspondentes a fatos atuais gradualmente falham em produzir clusters precisos de associação. A degradação semântica atinge então a API.

A saúde sistêmica protege o core do produto transacional, pois o RAG impõe limites de aceitação que barram alucinações via *guardrails*. A "pior" degradação num cenário bem desenhado é falhar educadamente (*policy_post* recusando por abstenção de contexto), e não inventar a lei desatualizada com roupagem falaciosa.

Assim, rastrear, analisar com precisão quantitativa numa camada *offline*, e re-indexar periodicamente versões das bases vetoriais com experimentação paralela, compõe não meramente um ajuste de qualidade pontual, mas sim a prática perene de MLOps imposta nesta infraestrutura arquitetural.
