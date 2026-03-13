# Chat Pref  
### Plataforma de Atendimento Municipal com IA, RAG e Arquitetura Tenant-Aware

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Auditoria%20%26%20Dados-4169E1?logo=postgresql&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-RAG-7B61FF)
![Docker](https://img.shields.io/badge/Docker-Execu%C3%A7%C3%A3o%20Local-2496ED?logo=docker&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-Canal%20de%20Demo-26A5E4?logo=telegram&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-CI%2FCD-2088FF?logo=githubactions&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-Infra%20as%20Code-844FBA?logo=terraform&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-Deploy%20Target-FF9900?logo=amazonaws&logoColor=white)

> Plataforma de atendimento digital para prefeituras, projetada para combinar **IA aplicada**, **recuperação semântica com RAG**, **guardrails**, **auditoria**, **observabilidade** e **isolamento por tenant**.

---

## Visão Geral

O **Chat Pref** é uma plataforma de atendimento institucional com IA, construída para servir como base de um assistente virtual para prefeituras.

O projeto foi estruturado para demonstrar, de forma prática:

- backend modular com **FastAPI**
- arquitetura **tenant-aware**
- pipeline de atendimento com **classificação, policy guard e RAG**
- **auditoria** e **rastreabilidade**
- execução local reproduzível com **Docker**
- demonstração funcional com **tenant fictício**
- canal real de operação via **Telegram**
- evolução para **CI/CD** e **deploy em AWS com Terraform**

O foco atual é transformar uma base funcional, mas heterogênea, em uma plataforma **coerente, demonstrável e tecnicamente defensável**.

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
- pipeline de processamento com classificação, policy guard e RAG
- arquitetura multi-tenant em consolidação
- auditoria e métricas operacionais
- Docker e ambiente local reproduzível
- tenant fictício demonstrativo
- canal de demonstração via Telegram
- geração de evidências de funcionamento
- preparação para CI/CD com GitHub Actions
- preparação para deploy em AWS com Terraform

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

### Backend
- Python 3.11+
- FastAPI
- Pydantic
- Uvicorn
- asyncpg

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
- logs estruturados
- auditoria de pipeline

### Automação e Entrega
- GitHub Actions
- Terraform
- AWS
- scripts operacionais em Python e Bash

---

## Arquitetura da Solução

A arquitetura do projeto foi estruturada para suportar um fluxo de atendimento institucional com IA, separando responsabilidades entre entrada HTTP, orquestração, recuperação semântica, políticas de segurança, persistência e operação.

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
├── docs/
├── dashboards/
├── logging/
├── grafana/
├── scripts/
├── tests/
├── docker-compose.yml
├── docker-compose.local.yml
├── Dockerfile
├── AGENTS.md
├── contexto.md
├── arquitetura.md
└── planejamento-trello.md
````

---

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

* `contexto.md`: estado atual do projeto
* `arquitetura.md`: arquitetura real
* `planejamento-trello.md`: fases, tasks e execução
* `AGENTS.md`: governança de agentes e regras operacionais

---

## Status Atual do Projeto

O projeto está em **refatoração estrutural com foco em demonstração funcional**.

Na branch de desenvolvimento, este README mantém a **stack-alvo do projeto** e sinaliza o estágio atual das fases.

**Fase ativa na branch:** Fase 9 — Operacionalização do chat via Telegram.
**Status da fase na branch:** iniciada na branch de trabalho.

### Já existe

* backend funcional em FastAPI
* pipeline com classificação, policy guard e RAG
* integração inicial com canais externos
* auditoria e métricas
* documentação técnica relevante
* base de observabilidade e suporte operacional
* tenant fictício demonstrativo versionado
* base documental fictícia do tenant demonstrativo

### Em andamento

* saneamento do legado mono-tenant
* consolidação do contrato de `tenant_id`
* reset da base RAG
* base documental fictícia expandida para o tenant demonstrativo
* canal real de demonstração via Telegram

### Próxima direção

* CI com GitHub Actions
* deploy mínimo em AWS com Terraform
* fechamento do case com evidências de operação

---

## Planejamento Macro por Fases

O projeto está organizado em blocos contínuos:

### Bloco A — Refatoração estrutural

* Fase 1 — Diagnóstico e inventário do legado
* Fase 2 — Sanitização funcional do runtime
* Fase 3 — Consolidação do contrato multi-tenant
* Fase 4 — Reset da base RAG e reingestão limpa
* Fase 5 — Containerização e ambiente local reproduzível
* Fase 6 — Validação estrutural da base refatorada

### Bloco B — Demonstração funcional

* Fase 7 — Construção do tenant demonstrativo fictício
* Fase 8 — Construção da base documental fictícia e ingest limpa
* Fase 9 — Operacionalização do chat via Telegram
* Fase 10 — Validação funcional, guardrails e evidências
* Fase 11 — Observabilidade aplicada e fechamento técnico do case

### Bloco C — Engenharia de entrega

* Fase 12 — Automação de qualidade com GitHub Actions
* Fase 13 — Infraestrutura como código e deploy em AWS
* Fase 14 — Alinhamento final entre arquitetura, operação e documentação

---

## Critério de Aceite do Projeto

O projeto será considerado bem-sucedido quando for possível demonstrar, com evidências reais:

* backend operacional
* tenant demonstrativo funcional
* RAG respondendo com base documental própria
* guardrails e fallback funcionando
* logs, auditoria e métricas disponíveis
* execução local reproduzível com Docker
* pipeline de qualidade automatizada com GitHub Actions
* deploy mínimo em AWS provisionado com Terraform
* documentação coerente com a realidade do sistema

---

## Fluxo Operacional Recomendado

Toda mudança importante deve seguir esta lógica:

**entender → planejar → isolar → implementar → validar → registrar → encerrar**

### Antes de alterar

* revisar `contexto.md`
* revisar `arquitetura.md`
* localizar a fase e task no planejamento
* validar o estado atual do repositório
* definir a forma de validação

### Durante a alteração

* manter mudanças pequenas e rastreáveis
* evitar refatorações laterais não planejadas
* tratar `tenant_id` como contrato explícito
* não esconder erro estrutural com fallback silencioso

### Depois da alteração

* validar tecnicamente
* revisar o diff
* registrar evidência
* atualizar documentação correspondente, quando necessário

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

---

## Observabilidade, Auditoria e Evidências

O projeto deve oferecer visibilidade mínima sobre o fluxo do atendimento.

### Evidências esperadas

* logs estruturados
* eventos de auditoria
* métricas básicas expostas
* trilha request → classificação → retrieval → resposta
* prints e registros da demonstração
* matriz de cenários validados

### Valor desta camada

A observabilidade não existe apenas para operação; ela também serve para:

* provar funcionamento
* gerar material de portfólio
* sustentar explicação técnica em entrevista
* aumentar confiança no comportamento do sistema

---

## CI/CD e Próximos Passos de Infraestrutura

Após a estabilização da demonstração funcional, o projeto evolui para uma trilha de entrega mais madura.

### GitHub Actions

A pipeline deve automatizar, no mínimo:

* lint
* testes
* validações críticas
* build Docker
* varredura de termos proibidos e resíduos históricos

### AWS + Terraform

A proposta é provisionar uma infraestrutura mínima e explicável, com foco em:

* reprodutibilidade
* baixo custo
* deploy simples
* operação clara

A recomendação atual é privilegiar uma arquitetura enxuta, suficiente para demonstrar entrega real sem inflar a complexidade do case.

---

## Próximos Passos

### Curto prazo

* concluir a refatoração estrutural
* consolidar Docker e ambiente local
* estabilizar `tenant_id` nos fluxos críticos
* resetar e reingestar a base RAG

### Médio prazo

* criar tenant fictício
* carregar base documental de demonstração
* colocar o chat para operar via Telegram
* executar cenários de validação e gerar evidências

### Próximo nível

* automatizar qualidade com GitHub Actions
* publicar demonstração em AWS com Terraform
* consolidar o case final para portfólio e entrevista

---

## Autor

**Diego Santos**
Engenharia de Dados, Automação, Backend e IA Aplicada

Projeto desenvolvido como case técnico de arquitetura, refatoração, operação e demonstração de uma plataforma de atendimento municipal com IA.

```
```
