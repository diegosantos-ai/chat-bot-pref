# Chat Pref  
### Plataforma de Atendimento Municipal com IA, RAG, Arquitetura Tenant-Aware e Evolução em LLMOps

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Auditoria%20%26%20Dados-4169E1?logo=postgresql&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-RAG-7B61FF)
![Docker](https://img.shields.io/badge/Docker-Execu%C3%A7%C3%A3o%20Local-2496ED?logo=docker&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-Canal%20de%20Demo-26A5E4?logo=telegram&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-CI%2FCD-2088FF?logo=githubactions&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-Infra%20as%20Code-844FBA?logo=terraform&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-Deploy%20Target-FF9900?logo=amazonaws&logoColor=white)
![MLflow](https://img.shields.io/badge/MLflow-Experiment%20Tracking-0194E2)
![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-Tracing%20%26%20Observability-6E43FF)
![Airflow](https://img.shields.io/badge/Airflow-Orquestra%C3%A7%C3%A3o%20Offline-017CEE?logo=apacheairflow&logoColor=white)

> Plataforma de atendimento digital para prefeituras, projetada para combinar **IA aplicada**, **recuperação semântica com RAG**, **guardrails**, **auditoria**, **observabilidade** e **arquitetura tenant-aware**, evoluindo agora para uma nova fase de **LLMOps, avaliação formal, governança e rastreabilidade experimental**.

---

## Visão Geral

O **Chat Pref** é uma plataforma de atendimento institucional com IA, construída para servir como base de um assistente virtual para prefeituras.

O projeto foi estruturado para demonstrar, de forma prática:

- backend modular com **FastAPI**
- arquitetura **tenant-aware**
- pipeline de atendimento com **composição generativa mínima**, **RAG tenant-aware** e **guardrails rastreáveis**
- **auditoria** e **rastreabilidade**
- execução local reproduzível com **Docker**
- demonstração funcional com **tenant fictício**
- canal real de operação via **Telegram**, com webhook HTTPS ativo no ambiente remoto demonstrativo
- evolução para **CI/CD** e **deploy em AWS com Terraform**

Com a consolidação da **Fundação Operacional**, o projeto entra agora em uma nova etapa: a construção da camada de **LLMOps, avaliação formal, governança e observabilidade avançada**.

O foco atual deixa de ser apenas a sustentação de uma base funcional e passa a ser a evolução para uma plataforma de IA mais **rastreável, avaliável, governável e tecnicamente demonstrável**.

O objetivo desta nova etapa continua o mesmo em essência: provar **GenAI com método**, agora com uma camada explícita de experimentação, benchmark, versionamento e governança técnica.

---

## Objetivo Principal

Construir e refatorar uma plataforma de atendimento municipal com IA que demonstre, de forma prática:

- arquitetura backend organizada
- uso responsável de IA com escopo controlado
- recuperação semântica com RAG
- isolamento por tenant
- rastreabilidade e auditoria
- observabilidade mínima útil
- operação reproduzível
- maturidade de engenharia para evolução com CI/CD e infraestrutura como código

---

## Case do Projeto

Este projeto nasceu como um sistema de atendimento institucional com foco em prefeitura, inicialmente orientado a um único contexto operacional.

Com a evolução da arquitetura, o objetivo passou a ser:

- eliminar legado mono-tenant
- consolidar o uso explícito de `tenant_id`
- remover hardcodes e dependências históricas
- resetar a base RAG para uma estrutura limpa
- criar um **tenant fictício demonstrativo**
- operar o sistema em um canal real de conversa
- gerar evidências técnicas de funcionamento

O case final busca demonstrar uma plataforma de IA aplicada ao setor público com:

- backend modular
- RAG funcional
- guardrails
- auditoria
- tenant-aware
- demonstração operacional real

---

## Escopo Atual

### Incluído
- API backend em FastAPI
- pipeline de processamento tenant-aware com composição generativa mínima, RAG validado e guardrails rastreáveis
- arquitetura multi-tenant em consolidação
- auditoria mínima operacional e evidências de validação
- Docker e ambiente local reproduzível
- tenant fictício demonstrativo
- canal demonstrativo via Telegram com reutilização do fluxo principal e webhook HTTPS ativo no ambiente remoto
- geração de evidências de funcionamento
- workflow de CI versionado com quality gates mínimos
- deploy mínimo em AWS validado com Terraform e proxy HTTPS público

### Não incluído neste momento
- produto enterprise finalizado
- billing/metering comercial
- múltiplos tenants em produção simultânea
- autenticação complexa de usuários finais
- painel administrativo completo por tenant
- benchmark acadêmico avançado de modelos
- arquitetura distribuída complexa em nuvem

---

## Tecnologias Utilizadas

Na branch de desenvolvimento, esta seção mantém a **stack-alvo do projeto**.

A base já validada da **Fundação Operacional** permanece documentada em:

- `docs-fundacao-operacional/`

A documentação da nova fase de evolução, focada em **LLMOps, avaliação e governança**, passa a ser mantida em:

- `docs-LLMOps/`

### Backend
- Python 3.11+
- FastAPI
- Pydantic
- Uvicorn
- PostgreSQL

### IA / RAG
- Google Gemini
- ChromaDB
- Retrieval-Augmented Generation
- query expansion
- guardrails por política

### Persistência e Infra
- PostgreSQL
- Redis
- Docker
- Docker Compose

### Operação e Observabilidade
- Prometheus
- Grafana
- Loki
- OpenTelemetry
- logs estruturados
- auditoria de pipeline

### Automação, Entrega e LLMOps
- GitHub Actions
- Terraform
- AWS
- MLflow
- avaliação formal de RAG
- scripts operacionais em Python e Bash
- Airflow como orquestrador offline da fase LLMOps

---

## Arquitetura da Solução

A arquitetura do projeto foi estruturada para suportar um fluxo de atendimento institucional com IA, separando responsabilidades entre entrada HTTP, orquestração, recuperação semântica, políticas de segurança, persistência e operação.

>> Esta seção resume a arquitetura-alvo do projeto. A base já validada da Fundação Operacional está documentada em `docs-fundacao-operacional/`, enquanto a arquitetura-alvo da nova fase de LLMOps está sendo consolidada em `docs-LLMOps/ARQUITETURA-LLMOps.md`.

### Componentes principais

| Componente | Função |
|---|---|
| `app/main.py` | inicialização da aplicação FastAPI |
| `app/api/` | endpoints HTTP e webhooks |
| `app/orchestrator/service.py` | coordenação do pipeline principal |
| `app/classifier/service.py` | classificação de intenção |
| `app/policy_guard/service.py` | guardrails e validações |
| `app/rag/retriever.py` | recuperação semântica |
| `app/rag/composer.py` | geração de resposta contextual |
| `app/audit/` | auditoria e rastreabilidade |
| `app/tenant_context.py` | contexto assíncrono de tenant |
| `app/tenant_resolver.py` | resolução de tenant |
| `admin-panel/` | interface administrativa |
| `db/` | schema e migrations |
| `logging/`, `dashboards/`, `grafana/` | observabilidade |

---

## Fluxo do Atendimento

O fluxo abaixo representa a direcao do pipeline completo do case. Na base ativa atual, o runtime validado opera um nucleo menor com chat, resolucao de tenant, retrieval por tenant e auditoria minima.

### Fluxo resumido
1. A aplicação recebe uma mensagem via endpoint interno ou canal externo.
2. O sistema resolve ou injeta o contexto de `tenant_id`.
3. A mensagem é normalizada, classificada e avaliada pelo `policy_guard`.
4. Se permitida, a consulta segue para retrieval RAG e composição da resposta.
5. A resposta é validada, registrada em auditoria e devolvida ao canal.
6. Logs, métricas e evidências podem ser coletados para análise operacional.

### Etapas principais do pipeline
- normalização de texto
- análise de formalidade e sentimento
- classificação de intent
- policy PRE
- query expansion
- retrieval
- composição via LLM
- policy POST
- resposta final
- auditoria e métricas

---

## Estrutura Atual do Projeto

```text
chat-bot-pref/
├── app/
│   ├── api/
│   ├── audit/
│   ├── channels/
│   ├── classifier/
│   ├── contracts/
│   ├── integrations/
│   ├── nlp/
│   ├── orchestrator/
│   ├── policy_guard/
│   ├── prompts/
│   ├── rag/
│   ├── repositories/
│   ├── services/
│   ├── main.py
│   ├── settings.py
│   ├── tenant_context.py
│   └── tenant_resolver.py
├── admin-panel/
├── db/
│   ├── migrations/
│   └── schema.sql
├── docs-fundacao-operacional/
├── docs-LLMOps/
├── dashboards/
├── logging/
├── grafana/
├── scripts/
├── tests/
├── docker-compose.yml
├── docker-compose.local.yml
├── Dockerfile
├── AGENTS.md
├── tenants/
└── artifacts/
```

---
``
## Responsabilidade dos Diretórios e Arquivos

### Backend

* `app/`: núcleo da aplicação
* `app/api/`: endpoints e entradas do sistema
* `app/orchestrator/`: pipeline principal
* `app/rag/`: recuperação e composição contextual
* `app/policy_guard/`: proteção e limites do comportamento
* `app/audit/`: eventos e trilha de decisão
* `app/services/`: serviços auxiliares

### Dados e Banco

* `db/`: modelagem relacional e migrations
* `data/`: bases e artefatos de apoio, quando aplicável

### Operação

* `logging/`, `dashboards/`, `grafana/`: observabilidade
* `scripts/`: utilitários, setup, validação e operação

### Documentação

#### Fundação Operacional
- `docs-fundacao-operacional/`: documentação histórica e validada da fundação operacional do projeto
- `docs-fundacao-operacional/contexto.md`: estado consolidado da base anterior
- `docs-fundacao-operacional/arquitetura.md`: arquitetura real da fundação operacional
- `docs-fundacao-operacional/planejamento_fases.md`: fases concluídas do ciclo operacional
- `docs-fundacao-operacional/guardrail_rastreavel.md`: eixo transversal de correlação e guardrails
- `docs-fundacao-operacional/genai_com_metodo.md`: definição operacional do requisito do case
- `docs-fundacao-operacional/evidencias_case.md`: matriz curta de `claim -> evidencia -> artefato`
- `docs-fundacao-operacional/diario_bordo.md`: narrativa técnica da construção e das validações principais

#### Nova fase — LLMOps
- `docs-LLMOps/README.md`: visão geral da nova fase
- `docs-LLMOps/CONTEXTO-LLMOps.md`: motivação, objetivo e critérios da fase
- `docs-LLMOps/ARQUITETURA-LLMOps.md`: arquitetura-alvo da camada de LLMOps
- `docs-LLMOps/PLANEJAMENTO_LLMOps.md`: planejamento macro da nova fase
- `docs-LLMOps/adrs/`: decisões arquiteturais da fase
- `docs-LLMOps/runbooks/`: preparação de ambiente, avaliação de RAG e operação offline

#### Governança
- `AGENTS.md`: governança de agentes e regras operacionais

---

## Status Atual do Projeto

O projeto possui uma **Fundação Operacional concluída e validada**, que sustenta o runtime principal do case e a demonstração funcional já comprovada.

Na branch de desenvolvimento, este README passa a cumprir dois papéis:

1. resumir a base já validada da fundação operacional;
2. posicionar a nova fase de evolução do projeto, focada em **LLMOps, avaliação formal, governança e observabilidade avançada**.

**Base consolidada:** Fundação Operacional concluída e validada localmente, na CI e no deploy remoto.  
**Nova fase em andamento:** Fase 1 — GenAI com Método: LLMOps, Avaliação e Governança.  
**Eixo transversal já consolidado:** Guardrail Rastreável distribuído entre as fases finais da fundação operacional.

### Já existe

* backend funcional em FastAPI
* contrato explícito de `tenant_id` no chat e no webhook mínimo
* `request_id` propagado no chat e no webhook via `X-Request-ID`
* persistência local e auditoria versionada `audit.v1` por tenant
* RAG tenant-aware com ingest limpa por tenant
* composição generativa mínima com adaptador LLM isolado
* prompts e política textual versionados
* `policy_pre` e `policy_post` com `reason_codes`
* integração Telegram com reutilização do fluxo principal, `dry_run` reproduzível localmente e webhook HTTPS ativo no ambiente remoto demonstrativo
* logs estruturados correlacionados por `request_id`
* métricas mínimas expostas em `/metrics`
* traces OpenTelemetry persistidos por `request_id`
* documentação técnica alinhada ao runtime mínimo
* tenant fictício demonstrativo versionado
* base documental fictícia do tenant demonstrativo com 14 documentos e 11 retrieval checks controlados
* ambiente local reproduzível com Docker e smoke tests
* workflow de CI versionado com quality gates, build Docker e smoke reduzido
* deploy mínimo em AWS provisionado com Terraform, smoke remoto aprovado e proxy HTTPS público estável por `sslip.io`

### Em evolução na nova fase

* rastreabilidade experimental por tenant
* versionamento formal de prompts, policies e configurações de RAG
* benchmark reproduzível por tenant
* avaliação formal de RAG
* comparação entre estratégias de retrieval e modelos
* observabilidade ampliada de qualidade, latência e custo
* orquestração offline com Airflow
* monitoramento de deriva semântica
* documentação viva da camada de LLMOps

### Limites declarados do estado atual

* `LLM_PROVIDER=mock` continua sendo o baseline reproduzível da base operacional
* a camada de LLMOps está em implantação e ainda não deve ser tratada como plenamente ativa no runtime
* o Telegram público do ambiente remoto depende de secrets externos não versionados
* o deploy remoto validado usa `sslip.io`, sem domínio próprio, rotação de secrets ou CD completo

### Limites declarados do recorte final

* `LLM_PROVIDER=mock` continua sendo o baseline reproduzível do projeto
* o Telegram público do ambiente remoto depende de secrets externos não versionados
* o deploy remoto validado usa `sslip.io`, sem domínio próprio, rotação de secrets ou CD completo

### Evoluções opcionais após o fechamento do case

* endurecer a operação remota com domínio próprio, rotação de secrets e CD quando isso fizer sentido
* validar um provedor LLM externo real como caminho reproduzível adicional
* expandir a operação remota sem perder o corte mínimo e explicável do projeto

---

## Planejamento Macro por Fases

O projeto passa a ser organizado em dois ciclos complementares:

### Ciclo 0 — Fundação Operacional

#### Bloco A — Refatoração estrutural
* Fase 1 — Diagnóstico e inventário do legado
* Fase 2 — Sanitização funcional do runtime
* Fase 3 — Consolidação do contrato multi-tenant
* Fase 4 — Reset da base RAG e reingestão limpa
* Fase 5 — Containerização e ambiente local reproduzível
* Fase 6 — Validação estrutural da base refatorada

#### Bloco B — Demonstração funcional
* Fase 7 — Construção do tenant demonstrativo fictício
* Fase 8 — Construção da base documental fictícia e ingest limpa
* Fase 9 — Operacionalização do chat via Telegram
* Fase 10 — Composição generativa, guardrails e evidências
* Fase 11 — Observabilidade aplicada e fechamento técnico do case

#### Bloco C — Engenharia de entrega
* Fase 12 — Automação de qualidade com GitHub Actions
* Fase 13 — Infraestrutura como código e deploy em AWS
* Fase 14 — Alinhamento final entre arquitetura, operação e documentação

### Ciclo 1 — LLMOps, Avaliação e Governança

#### Bloco D — Maturidade de IA
* Fase 1 — Fundação de LLMOps e rastreabilidade experimental
* Fase 2 — Versionamento de prompts, policies e configuração de RAG
* Fase 3 — Dataset de avaliação e benchmark reproduzível
* Fase 4 — Avaliação formal de RAG com métricas de qualidade
* Fase 5 — Retrieval híbrido, query rewriting e reranking
* Fase 6 — Observabilidade de qualidade, latência e custo por tenant
* Fase 7 — CI de GenAI com regressão de prompt e dry-run experimental
* Fase 8 — Orquestração offline com Airflow
* Fase 9 — Deriva semântica e saúde da base vetorial
* Fase 10 — Multi-LLM, fallback e avaliação comparativa de provedores
* Fase 11 — Governança, explicabilidade e evidência de decisão
* Fase 12 — Alinhamento final com a vaga e material de demonstração
---

## Critério de Aceite do Projeto

O projeto será considerado bem-sucedido quando for possível demonstrar, com evidências reais:

### Fundação Operacional
* backend operacional
* tenant demonstrativo funcional
* RAG respondendo com base documental própria
* guardrails e fallback funcionando
* logs, auditoria e métricas disponíveis
* execução local reproduzível com Docker
* pipeline de qualidade automatizada com GitHub Actions
* deploy mínimo em AWS provisionado com Terraform
* documentação coerente com a realidade do sistema

### Nova fase de LLMOps
* rastreamento experimental por tenant
* versionamento formal de prompts, policies e configuração de retrieval
* benchmark reproduzível por tenant
* métricas formais de qualidade de RAG registradas por experimento
* comparação estruturada entre estratégias de retrieval e modelos
* observabilidade de latência, custo e qualidade
* operação offline organizada para ingestão, avaliação e reindexação
* critérios para monitorar sinais de degradação semântica
* documentação coerente para implantação, operação, demonstração e defesa técnica

---

## Fluxo Operacional Recomendado

Toda mudança importante deve seguir esta lógica:

**entender → planejar → isolar → implementar → validar → registrar → encerrar**

### Antes de alterar

* revisar a documentação do ciclo correspondente
* localizar a fase e a task no planejamento apropriado
* validar o estado atual do repositório
* definir a forma de validação
* confirmar se a mudança pertence à fundação operacional ou à fase de LLMOps

### Durante a alteração

* manter mudanças pequenas e rastreáveis
* evitar refatorações laterais não planejadas
* tratar `tenant_id` como contrato explícito
* não esconder erro estrutural com fallback silencioso
* preservar a separação entre operação, experimento e orquestração offline

### Depois da alteração

* validar tecnicamente
* revisar o diff
* registrar evidência
* atualizar a documentação correspondente, quando necessário

### Referências de navegação

* Fundação Operacional: `docs-fundacao-operacional/`
* Nova fase: `docs-LLMOps/`

---

## Execução Local com Docker

O projeto deve operar localmente de forma reproduzível com Docker e Docker Compose.

### Objetivo do ambiente local

Permitir:

* subir backend e dependências principais
* testar endpoints críticos
* validar fluxo de tenant
* executar ingest
* operar tenant fictício demonstrativo
* testar o canal Telegram

### Resultado esperado

Comandos simples devem ser suficientes para:

* iniciar a aplicação
* verificar `/health`
* validar `/api/chat`
* observar logs e métricas
* reproduzir o fluxo de demonstração

> O detalhamento do ambiente local deve refletir o estado real do `Dockerfile` e do `docker-compose` vigente.

Na fase atual, o bootstrap mínimo validado do backend está descrito em [docs/bootstrap_local.md](docs/bootstrap_local.md).

A documentação da fundação operacional permanece em `docs-fundacao-operacional/`, enquanto a evolução de ambiente para a fase de LLMOps passa a ser documentada em `docs-LLMOps/runbooks/`.

---

## Tenant Fictício Demonstrativo

O projeto será demonstrado com **uma prefeitura fictícia**, criada exclusivamente para evidenciar a plataforma.

### Objetivo do tenant fictício

* demonstrar isolamento por tenant
* operar uma base RAG própria
* evitar uso de dados reais
* permitir cenários de validação controlados
* sustentar a narrativa técnica do case

### Características esperadas

* identidade institucional neutra
* escopo estritamente informativo
* documentos fictícios plausíveis
* configuração isolada
* disclaimers e limites claros

---

## Canal de Demonstração via Telegram

O Telegram será usado como **canal de demonstração operacional** do núcleo da plataforma.

### Por que Telegram

* integração mais simples
* testes rápidos
* conversa real com o backend
* boa evidência de funcionamento ponta a ponta

### Papel no projeto

O Telegram não representa o produto final obrigatório.
Ele funciona como **canal demonstrativo** para validar:

* entrada de mensagem
* resolução de tenant
* pipeline de atendimento
* retrieval
* resposta
* auditoria
* logs e evidências

Na branch atual, esse canal já possui dois modos de operação validados:

* **local reproduzível** em `dry_run`, sem depender de token real
* **ambiente remoto demonstrativo** em `api`, com webhook HTTPS ativo sobre a URL pública provisionada na AWS

---

## Observabilidade, Auditoria e Evidências

O projeto oferece visibilidade mínima sobre o fluxo do atendimento já validado na Fundação Operacional e passa a evoluir, na nova fase, para uma camada mais formal de tracking experimental e avaliação.

Na base ativa já validada, a evidência operacional inclui:
- auditoria versionada `audit.v1`
- `PolicyDecision`
- `reason_codes`
- logs estruturados
- métricas expostas em `/metrics`
- traces correlacionados por `request_id`

Na nova fase, o projeto passa a estruturar também:
- experiment tracking por tenant
- benchmark reproduzível
- avaliação formal de RAG
- comparação entre versões
- leitura de deriva semântica

Para leitura humana mais direta do case e da nova fase, use também:

* `docs-fundacao-operacional/`
* `docs-LLMOps/`

### Evidências esperadas

* logs estruturados
* eventos de auditoria
* métricas básicas expostas
* trilha request → policy_pre → retrieval → compose → policy_post → resposta
* benchmark por tenant
* métricas experimentais comparáveis
* artifacts de avaliação
* matriz de cenários validados

### Valor desta camada

A observabilidade não existe apenas para operação; ela também serve para:

* provar funcionamento
* gerar material de portfólio
* sustentar explicação técnica em entrevista
* aumentar confiança no comportamento do sistema
* apoiar evolução de IA com método

---

## CI/CD e Próximos Passos de Infraestrutura

Após a estabilização da demonstração funcional, o projeto evolui para uma trilha de entrega mais madura.

### GitHub Actions

A branch atual ja possui workflow de CI versionado em `.github/workflows/ci.yml`, cobrindo:

* lint minimo do runtime
* `pytest`
* validacao de `docker compose config`
* build Docker
* varredura de termos proibidos e residuos historicos
* smoke `prod` reduzido com upload de artefato

No corte atual, esse workflow nao exige secrets novos. Os secrets `DEPLOY_WEBHOOK_URL` e `DEPLOY_WEBHOOK_TOKEN` continuam restritos ao workflow manual de deploy.

### AWS + Terraform

Na branch atual, a Fase 13 já validou um corte mínimo e explicável em AWS `us-east-1`, com:

* VPC dedicada mínima
* subnet pública
* Security Group na porta `8000`
* perfil IAM com SSM
* EC2 única
* Elastic IP
* proxy HTTPS público com Caddy e hostname `sslip.io` derivado do IP
* bootstrap via `user_data` + `docker compose`
* smoke remoto aprovado em `GET /`, `GET /health`, `GET /metrics` e `POST /api/chat`

O recorte continua enxuto de propósito: entrega real, baixo custo e operação explicável antes de domínio próprio, ECS ou backend remoto de Terraform.

---

## Próximos Passos

### Fundação já consolidada
* preservar a base validada da fundação operacional como referência estável do runtime
* manter a coerência entre operação local, CI e deploy remoto

### Nova fase — LLMOps
* preparar ambiente base, ambiente dev e ambiente offline conforme o planejamento
* introduzir experiment tracking com segregação por tenant
* formalizar benchmark reproduzível e avaliação de RAG
* versionar prompts, policies e configurações críticas
* ampliar observabilidade para qualidade, custo e latência
* introduzir orquestração offline de ingestão, benchmark e reindexação
* consolidar material técnico de demonstração orientado à vaga-alvo

### Evolução opcional de infraestrutura
* endurecer a operação remota com domínio próprio, rotação de secrets e CD
* manter o Telegram público ativo sobre a URL estável do ambiente remoto
* preservar os contratos de `request_id`, `tenant_id` e observabilidade no ambiente em nuvem

---

## Autor

**Diego Santos**
Engenharia de Dados, Automação, Backend e IA Aplicada

Projeto desenvolvido como case técnico de arquitetura, refatoração, operação e demonstração de uma plataforma de atendimento municipal com IA.

```
```
