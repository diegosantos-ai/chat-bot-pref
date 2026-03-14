# CONTEXTO-LLMOps

## Contexto

Com a consolidação da **Fundação Operacional do Chat Pref**, o projeto atingiu um ponto de estabilidade suficiente para sustentar uma nova etapa de evolução técnica.

A fase anterior estabeleceu a base funcional da solução: backend operacional, pipeline principal de atendimento, integração com RAG, guardrails, trilha mínima de auditoria, observabilidade inicial, segregação multi-tenant e estrutura mínima de deploy. Essa fundação permitiu validar a coerência da arquitetura, o funcionamento do fluxo principal e a viabilidade do projeto como solução aplicada ao contexto público.

A partir deste ponto, o foco do desenvolvimento deixa de ser apenas a sustentação de um sistema funcional e passa a ser a construção de uma camada mais madura de engenharia para IA, com ênfase em reprodutibilidade, governança, rastreabilidade experimental e avaliação formal.

Esta nova etapa passa a ser documentada em `docs-LLMOps/`, preservando a documentação anterior em `docs-fundacao-operacional/` como registro histórico do ciclo já consolidado.

## Motivação da nova fase

A abertura desta fase responde a uma necessidade técnica e estratégica.

Do ponto de vista técnico, a fundação operacional já permite avançar para temas que não devem ser tratados de forma improvisada:
- rastreamento experimental por tenant;
- versionamento de prompts, policies e configuração de RAG;
- avaliação reproduzível da qualidade do pipeline;
- comparação controlada entre estratégias de retrieval e provedores LLM;
- observabilidade de qualidade, latência e custo;
- detecção de degradação semântica da base vetorial;
- orquestração offline para ingestão, avaliação e reindexação.

Do ponto de vista estratégico, esta fase busca elevar o Chat Pref de um sistema funcional e demonstrável para uma plataforma de IA com maior maturidade técnica, adequada para explicação arquitetural, defesa técnica e evolução controlada sob critérios de engenharia.

## Objetivo da fase

O objetivo desta fase é estruturar a camada de **LLMOps, avaliação formal, governança e observabilidade avançada** do Chat Pref, transformando a base já existente em uma solução capaz de sustentar:

- rastreabilidade experimental por tenant;
- versionamento formal de prompts, policies e configuração de RAG;
- benchmark reproduzível para avaliação do pipeline;
- comparação entre estratégias de retrieval e modelos;
- observabilidade de qualidade, latência e custo;
- monitoramento de sinais de degradação semântica;
- separação explícita entre auditoria operacional e experiment tracking;
- documentação técnica consistente para implantação, operação e demonstração.

## Problema que esta fase busca resolver

A fundação operacional resolve a viabilidade do sistema, mas não resolve integralmente o problema de maturidade da engenharia de IA.

Sem esta nova fase, o projeto permanece exposto a limitações como:
- evolução de prompt e retrieval sem trilha experimental suficiente;
- comparação entre versões baseada em percepção e não em benchmark;
- dificuldade de explicar degradações de resposta por tenant;
- observabilidade insuficiente para correlacionar qualidade, custo e latência;
- ausência de uma camada formal de avaliação de RAG;
- documentação incompleta para sustentar governança e reprodutibilidade.

A Fase LLMOps existe para fechar esse espaço entre sistema funcional e sistema tecnicamente governável.

## Diretriz central

A diretriz central desta fase é consolidar o princípio de **GenAI com método**.

Na prática, isso significa substituir evolução baseada em tentativa isolada ou percepção subjetiva por evolução baseada em:
- experimento rastreável;
- benchmark reproduzível;
- comparação entre versões;
- evidência técnica;
- governança explícita de artefatos;
- segregação segura por tenant.

## Escopo

Esta fase cobre a evolução do projeto nas seguintes frentes:

- fundação de LLMOps e rastreabilidade experimental;
- versionamento de prompts, policies e parâmetros de RAG;
- construção de dataset de avaliação e benchmark reproduzível;
- avaliação formal do pipeline RAG;
- evolução para retrieval híbrido, query rewriting e reranking;
- observabilidade de qualidade, latência e custo;
- CI de GenAI com regressão e dry-run experimental;
- orquestração offline com Airflow;
- monitoramento de deriva semântica;
- comparação multi-LLM e fallback controlado;
- ampliação da camada de governança, explicabilidade e evidência técnica;
- consolidação documental para demonstração e defesa arquitetural.

## Fora de escopo

Esta fase não tem como objetivo:
- reabrir ou reescrever a documentação histórica da fundação operacional;
- declarar como implementado aquilo que ainda é apenas arquitetura-alvo;
- substituir auditoria operacional por experiment tracking;
- introduzir complexidade ferramental sem justificativa técnica e evidência de valor;
- expandir o sistema por volume de features sem consolidar antes a governança da camada de IA.

## Princípios de execução

A execução desta fase deve seguir os princípios abaixo:

- **tenant-awareness como requisito estrutural**  
  Nenhuma solução de tracking, avaliação ou observabilidade deve misturar dados de tenants distintos de forma insegura.

- **separação entre operação e experimento**  
  Auditoria de atendimento e rastreamento experimental devem coexistir, mas não se confundir.

- **estado atual distinto de arquitetura-alvo**  
  A documentação deve explicitar o que já está validado e o que permanece planejado.

- **evolução guiada por benchmark**  
  Mudanças em prompt, retrieval, modelo ou policy devem ser comparáveis e justificáveis.

- **instrumentação antes de otimização**  
  O projeto deve evitar sofisticar uma camada que ainda não esteja mensurada de forma suficiente.

## Relação com a fase anterior

A **Fundação Operacional** permanece como base do projeto.

Ela continua representando:
- o runtime validado;
- os contratos ativos do sistema;
- a trilha arquitetural já consolidada;
- o registro histórico da etapa em que a solução saiu do plano e se tornou executável.

A nova fase não substitui essa base. Ela a utiliza como fundação para uma camada superior de maturidade em IA.

## Critério de sucesso da fase

A fase será considerada bem-sucedida quando o projeto demonstrar, com evidência técnica e documental:

- capacidade de rastrear experimentos por tenant;
- versionamento formal de prompts, policies e configuração de retrieval;
- benchmark reproduzível para avaliação do pipeline;
- métricas formais de qualidade de RAG registradas por experimento;
- comparação estruturada entre estratégias de retrieval e modelos;
- observabilidade de latência, custo e qualidade;
- operação offline organizada para ingestão, avaliação e reindexação;
- critérios para monitorar sinais de degradação semântica;
- documentação coerente para implantação, operação, demonstração e defesa técnica.

## Artefatos principais desta fase

Os principais artefatos documentais desta fase são:

- `README.md`
- `CONTEXTO-LLMOps.md`
- `ARQUITETURA-LLMOps.md`
- `PLANEJAMENTO_LLMOps.md`
- ADRs em `adrs/`
- runbooks em `runbooks/`
- detalhamentos adicionais em `fases/`, quando necessário

## Referência de execução

A execução macro desta fase está detalhada em:

- `PLANEJAMENTO_LLMOps.md`

A arquitetura-alvo e a distinção entre estado atual e estado planejado devem ser mantidas em:

- `ARQUITETURA-LLMOps.md`

## Status

Fase em abertura formal.

Planejamento macro definido.  
Estrutura documental em consolidação.  
Próximo passo: formalização da arquitetura-alvo da fase.