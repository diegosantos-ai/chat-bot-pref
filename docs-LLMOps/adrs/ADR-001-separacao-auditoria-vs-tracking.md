# ADR-001 — Separação entre Auditoria Operacional e Experiment Tracking

## Status
Aceito

## Contexto

O Chat Pref evolui de uma fundação operacional já estabelecida para uma nova fase orientada a LLMOps, avaliação formal, governança e observabilidade avançada.

Na base já existente, a trilha de auditoria cumpre papel operacional e institucional: registrar fatos do atendimento, contexto mínimo de execução, decisões de policy, eventos relevantes e evidências associadas ao fluxo transacional.

Com a abertura da fase de LLMOps, surge uma nova necessidade arquitetural: registrar execuções experimentais, comparações entre versões, métricas de benchmark, artifacts de avaliação e parâmetros técnicos de evolução do pipeline de IA.

Sem uma separação explícita, há risco de acoplamento indevido entre duas responsabilidades distintas:
- registrar o atendimento como fato operacional;
- registrar o experimento como fato técnico comparável.

Essa sobreposição comprometeria clareza arquitetural, manutenção, governança de dados e rastreabilidade por tenant.

## Decisão

A arquitetura do projeto passa a tratar **Auditoria Operacional** e **Experiment Tracking** como camadas distintas, com responsabilidades próprias, contratos independentes e finalidades complementares.

### Auditoria Operacional
A auditoria operacional permanece responsável por registrar fatos do atendimento em contexto transacional e institucional.

Ela deve responder perguntas como:
- qual tenant atendeu a requisição;
- qual foi o request processado;
- qual decisão de policy foi aplicada;
- se houve bloqueio, fallback ou resposta final;
- quais eventos operacionais relevantes ocorreram durante a execução.

### Experiment Tracking
O experiment tracking passa a ser responsável por registrar fatos técnicos comparáveis do ciclo de IA.

Ele deve responder perguntas como:
- qual versão de prompt foi utilizada;
- qual configuração de retrieval estava ativa;
- qual dataset de benchmark foi empregado;
- quais métricas foram produzidas por uma execução experimental;
- como uma versão se compara a outra;
- qual foi o custo, a latência e a qualidade associados ao experimento.

## Justificativa

A separação foi adotada pelos seguintes motivos:

1. **clareza de responsabilidade**  
   Auditoria e experimentação têm objetivos diferentes e não devem disputar o mesmo modelo mental nem o mesmo contrato de persistência.

2. **governança de dados**  
   O dado operacional do atendimento e o dado experimental possuem diferentes propósitos de retenção, leitura e análise.

3. **manutenção arquitetural**  
   Separar essas camadas reduz acoplamento e evita transformar a auditoria em depósito genérico de telemetria experimental.

4. **tenant-awareness**  
   A segregação por tenant deve existir em ambas as camadas, mas isso não exige fusão entre elas.

5. **evolução controlada**  
   O ciclo de experimentação pode crescer em volume, cardinalidade e granularidade sem degradar o desenho da camada operacional.

## Consequências

### Positivas
- melhor separação de responsabilidades;
- arquitetura mais compreensível;
- menor risco de acoplamento indevido;
- base mais sólida para adoção de MLflow;
- melhor sustentação para benchmark, comparação de versões e avaliação formal.

### Negativas / trade-offs
- necessidade de manter duas trilhas correlacionáveis;
- aumento inicial de disciplina documental e técnica;
- necessidade de definir contratos claros de correlação entre operação e experimento.

## Contratos transversais

Mesmo sendo camadas distintas, auditoria operacional e experiment tracking devem poder ser correlacionados por meio de contratos mínimos compartilhados, quando aplicável:

- `tenant_id`
- `request_id`
- `artifact_version`
- `run_id` experimental
- timestamp de execução
- identificadores de contexto relevantes

A correlação existe para análise. A fusão de responsabilidade não.

## Alternativas consideradas

### 1. Usar apenas a auditoria operacional para tudo
Rejeitada.

Motivo:
- mistura responsabilidades distintas;
- dificulta benchmark e comparação experimental;
- polui o modelo operacional com granularidade técnica excessiva.

### 2. Registrar experimentação apenas em logs
Rejeitada.

Motivo:
- não oferece estrutura suficiente para comparação formal;
- dificulta consulta, governança e rastreabilidade de versões;
- não sustenta adequadamente avaliação reproduzível.

### 3. Separar auditoria e tracking experimental
Aceita.

Motivo:
- preserva clareza arquitetural;
- reduz acoplamento;
- sustenta melhor a fase LLMOps.

## Impacto na arquitetura

A partir desta decisão:
- a camada de auditoria continua vinculada ao fluxo operacional do atendimento;
- a camada de experiment tracking passa a ser introduzida como componente próprio da fase LLMOps;
- benchmark, avaliação formal e comparação entre versões passam a se apoiar na trilha experimental;
- documentação, planejamento e implementação devem preservar essa separação.

## Impacto na implementação

Esta decisão implica:
- modelagem distinta para dados operacionais e dados experimentais;
- integração controlada entre `app/audit/` e a futura camada de tracking experimental;
- definição de contratos mínimos de correlação;
- revisão das fases e tasks para evitar confusão entre persistência operacional e experimentação.

## Relação com a fase atual

Esta ADR é fundacional para a Fase 1 de LLMOps.

Sem ela, o projeto corre risco de introduzir MLflow, benchmark e avaliação formal sobre uma base conceitualmente ambígua.

## Referências internas
- `docs-LLMOps/CONTEXTO-LLMOps.md`
- `docs-LLMOps/ARQUITETURA-LLMOps.md`
- `docs-LLMOps/PLANEJAMENTO_LLMOps.md`