# Arquitetura do Projeto

## 1. Visão geral

A arquitetura deste projeto foi estruturada para suportar uma plataforma de atendimento digital com IA aplicada ao setor público, com foco em processamento de mensagens, integração com canais externos, recuperação de contexto via RAG, auditoria operacional e evolução para um modelo multi-tenant.

A solução utiliza um backend principal em FastAPI, componentes de classificação e policy guard, um pipeline de recuperação semântica com ChromaDB, persistência relacional com PostgreSQL, integrações com canais Meta e componentes auxiliares de administração, ingestão e observabilidade.

A separação entre camadas foi pensada para permitir:

* isolamento progressivo de responsabilidades
* rastreabilidade do fluxo de decisão
* evolução do projeto por etapas
* refatoração controlada do legado mono-tenant para uma arquitetura multi-tenant mais consistente

---

## 2. Objetivo arquitetural

A arquitetura precisa suportar um fluxo de atendimento institucional baseado em IA, com capacidade de:

* receber mensagens de diferentes canais
* classificar intenção e aplicar guardrails antes da geração de resposta
* recuperar contexto a partir de uma base de conhecimento
* gerar respostas informativas com escopo controlado
* registrar auditoria e métricas do processamento
* evoluir para isolamento por tenant em dados, configuração e base semântica

Além de funcionar, a arquitetura também precisa provar:

* capacidade de composição entre backend, RAG, integração externa e observabilidade
* preocupação com governança, compliance e rastreabilidade
* maturidade de refatoração de um sistema funcional para um modelo mais robusto

As principais decisões arquiteturais buscaram simplicidade operacional, clareza de módulos e separação de papéis, evitando transformar o projeto em uma colcha de retalhos ainda mais caótica do que o inevitável em sistemas que cresceram por iteração acelerada.

---

## 3. Componentes principais

| Componente                            | Função                         | Responsabilidade                                                                |
| ------------------------------------- | ------------------------------ | ------------------------------------------------------------------------------- |
| `app/main.py`                         | Bootstrap da aplicação         | Inicialização do FastAPI, middlewares, rotas, scheduler e instrumentação        |
| `app/api/`                            | Camada de entrada HTTP         | Expor endpoints de chat, webhook, analytics, deploy, admin e painel             |
| `app/orchestrator/service.py`         | Orquestração principal         | Coordenar classificação, policy guard, RAG, fallback e geração de resposta      |
| `app/classifier/service.py`           | Classificação de intenção      | Detectar intent por regex e LLM                                                 |
| `app/policy_guard/service.py`         | Guardrails                     | Aplicar regras de segurança, bloqueio, redirecionamento e validação de resposta |
| `app/rag/retriever.py`                | Recuperação semântica          | Buscar chunks relevantes no ChromaDB com base no tenant ativo                   |
| `app/rag/composer.py`                 | Geração de resposta contextual | Montar contexto e chamar o modelo LLM                                           |
| `app/audit/`                          | Auditoria                      | Registrar eventos de processamento e rastreabilidade                            |
| `app/tenant_context.py`               | Contexto de tenant             | Propagar `tenant_id` no fluxo assíncrono                                        |
| `app/tenant_resolver.py`              | Resolução de tenant            | Resolver tenant a partir de contexto externo, como `page_id`                    |
| `app/channels/`                       | Integração com canais          | Adaptar payloads externos e enviar mensagens de saída                           |
| `db/`                                 | Persistência relacional        | Schema, migrations e suporte a RLS                                              |
| `admin-panel/`                        | Interface administrativa       | Operação e configuração auxiliar da plataforma                                  |
| `logging/`, `dashboards/`, `grafana/` | Observabilidade                | Coleta, visualização e suporte operacional                                      |

---

## 4. Fluxo geral da solução

### Fluxo resumido

1. A aplicação recebe mensagens via endpoint interno (`/api/chat`) ou webhook externo (`/webhook/meta`).
2. O fluxo resolve ou deveria resolver explicitamente o contexto de tenant.
3. A mensagem é normalizada, classificada e submetida ao `policy_guard`.
4. Se permitida, a consulta segue para recuperação RAG e composição da resposta.
5. A resposta passa por validação posterior, auditoria, métricas e envio/retorno.
6. Os eventos do sistema podem ser acompanhados por logs, métricas e dashboards operacionais.

### Fluxo detalhado atual

1. **Entrada**

   * `chat.py` recebe requisições diretas
   * `webhook.py` recebe eventos da Meta
2. **Resolução de contexto**

   * no webhook, há tentativa de resolver `page_id -> tenant_id`
   * no chat direto, esse contrato ainda precisa ser consolidado
3. **Pipeline**

   * normalização NLP
   * detecção de formalidade e sentimento
   * classificação de intent
   * avaliação `policy_pre`
4. **RAG**

   * expansão de query
   * retrieval semântico
   * composição da resposta com LLM
   * avaliação `policy_post`
5. **Saída**

   * resposta HTTP ou envio via canal Meta
6. **Rastreabilidade**

   * auditoria
   * analytics
   * métricas Prometheus
   * logging estruturado

---

## 5. Estrutura física / lógica

### Diretórios principais

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
├── docker-compose.yml
├── docker-compose.local.yml
└── README.md
```

### Papéis dos diretórios

* `app/`: núcleo da aplicação backend
* `app/api/`: camada HTTP e pontos de entrada
* `app/orchestrator/`: coordenação do fluxo principal
* `app/rag/`: recuperação semântica, embeddings e composição
* `app/channels/`: integração com canais externos
* `app/audit/`: persistência de auditoria
* `app/services/`: serviços auxiliares
* `db/`: modelagem e evolução do banco relacional
* `admin-panel/`: interface operacional
* `docs/`: documentação técnica e operacional
* `logging/`, `dashboards/`, `grafana/`: componentes de observabilidade
* `scripts/`: automações e utilitários de manutenção

---

## 6. Camadas da arquitetura

### Camada 1 — Entrada e interface

**Responsabilidade:**
Receber requisições HTTP, validar payloads, expor endpoints administrativos e integrar eventos externos ao backend.

**Principais arquivos:**

* `app/main.py`
* `app/api/chat.py`
* `app/api/webhook.py`
* `app/api/admin.py`
* `app/api/analytics.py`
* `app/api/deploy.py`
* `admin-panel/`

**Cuidados:**

* contratos de entrada precisam ser consistentes
* o fluxo de tenant ainda precisa ser explicitado melhor no chat direto
* validações de segurança não podem depender apenas da camada HTTP

---

### Camada 2 — Orquestração e regras de negócio

**Responsabilidade:**
Controlar o fluxo de decisão, aplicar políticas, classificar mensagens, acionar RAG, tratar fallback e coordenar a resposta final.

**Principais arquivos:**

* `app/orchestrator/service.py`
* `app/classifier/service.py`
* `app/policy_guard/service.py`
* `app/nlp/*`
* `app/prompts/*`

**Cuidados:**

* evitar acoplamento excessivo dentro do orchestrator
* impedir duplicação de retrieval ou decisões divergentes
* manter rastreabilidade entre classificação, política, recuperação e resposta

---

### Camada 3 — Recuperação, persistência e contexto

**Responsabilidade:**
Resolver tenant, acessar armazenamento semântico e relacional, registrar auditoria e sustentar o contexto de execução.

**Principais arquivos:**

* `app/rag/retriever.py`
* `app/rag/composer.py`
* `app/tenant_context.py`
* `app/tenant_resolver.py`
* `app/audit/repository.py`
* `db/schema.sql`
* `db/migrations/*`

**Cuidados:**

* o multi-tenant precisa ser consistente ponta a ponta
* não pode haver fallback silencioso para tenant/base default
* RLS, collection por tenant e contexto assíncrono precisam permanecer alinhados

---

### Camada 4 — Integrações e operação

**Responsabilidade:**
Conectar o sistema a serviços externos, administrar envio de mensagens, observabilidade, deploy e manutenção operacional.

**Principais arquivos:**

* `app/channels/meta_adapter.py`
* `app/channels/meta_sender.py`
* `app/services/*`
* `docker-compose.yml`
* `logging/*`
* `dashboards/*`
* `grafana/*`

**Cuidados:**

* evitar hardcodes de domínio, path e credencial
* manter a operação desacoplada da identidade histórica do projeto
* garantir que scripts e configuração reflitam a arquitetura atual

---

## 7. Decisões arquiteturais

### Decisão 1 — Adotar FastAPI como núcleo da aplicação

**Contexto:**
O projeto precisava de uma API clara, modular e adequada a integrações HTTP e webhook.

**Decisão tomada:**
Utilizar FastAPI como camada central do backend.

**Motivo:**
Boa produtividade, organização por routers, integração natural com tipagem e modelos de dados.

**Impacto:**
Facilitou a organização do backend e a expansão de endpoints.

**Risco:**
Se a lógica de negócio crescer demais nos endpoints ou no orchestrator, a aplicação pode se tornar difícil de manter.

---

### Decisão 2 — Centralizar o fluxo de decisão no `OrchestratorService`

**Contexto:**
Era necessário coordenar classificação, política, RAG, fallback e resposta em um fluxo único.

**Decisão tomada:**
Criar um orquestrador principal para o pipeline.

**Motivo:**
Concentrar o fluxo e manter uma trilha de execução mais visível.

**Impacto:**
Facilitou o entendimento do pipeline fim a fim.

**Risco:**
O orchestrator pode se tornar um ponto de acoplamento excessivo se continuar acumulando responsabilidades.

---

### Decisão 3 — Evoluir o projeto para multi-tenant com `tenant_context` + RLS + collection por tenant

**Contexto:**
O projeto começou orientado a um único cliente e passou a exigir isolamento para múltiplos tenants.

**Decisão tomada:**
Adotar `contextvars` para contexto de tenant, RLS no PostgreSQL e collections separadas no ChromaDB.

**Motivo:**
Permitir isolamento lógico e físico coerente com o modelo white-label.

**Impacto:**
Criou uma base técnica mais sólida para o futuro multi-tenant.

**Risco:**
A migração ainda está incompleta em todos os fluxos, especialmente onde o tenant não entra de forma explícita.

---

### Decisão 4 — Usar policy guard em fases PRE e POST

**Contexto:**
Era necessário impedir respostas inadequadas e controlar riscos em contexto institucional.

**Decisão tomada:**
Aplicar validação antes e depois da geração de resposta.

**Motivo:**
Reduzir risco de conteúdo impróprio, clínico, ofensivo ou fora de escopo.

**Impacto:**
Melhorou governança e previsibilidade do comportamento.

**Risco:**
Regras excessivamente acopladas ou heurísticas frágeis podem gerar falsos positivos ou silenciosamente bloquear casos legítimos.

---

### Decisão 5 — Separar retriever e composer no RAG

**Contexto:**
A recuperação semântica e a geração de resposta têm responsabilidades distintas.

**Decisão tomada:**
Manter módulos separados para retrieval e composição.

**Motivo:**
Facilitar manutenção, teste e evolução independente.

**Impacto:**
A estrutura ficou mais organizada para raciocínio modular.

**Risco:**
Sem contrato bem definido, pode haver duplicação de trabalho entre orquestração e composição.

---

## 8. Configurações críticas

| Arquivo / área                | Motivo de criticidade                             | Risco de alteração incorreta                                        |
| ----------------------------- | ------------------------------------------------- | ------------------------------------------------------------------- |
| `app/settings.py`             | Centraliza configuração do backend                | ambiente inconsistente, defaults perigosos, falhas de inicialização |
| `app/main.py`                 | Define bootstrap, middlewares e routers           | quebra global da aplicação                                          |
| `app/api/webhook.py`          | Entrada de eventos externos e resolução de tenant | processamento incorreto, segurança frágil, tenant errado            |
| `app/orchestrator/service.py` | Pipeline principal de decisão                     | regressão funcional ampla                                           |
| `app/rag/retriever.py`        | Resolve collection e retrieval contextual         | vazamento lógico entre tenants ou falha de resposta                 |
| `app/audit/repository.py`     | Registra trilha de auditoria                      | perda de rastreabilidade e inconsistência em RLS                    |
| `docker-compose.yml`          | Define ambiente de execução local/operacional     | falhas de subida e integração entre serviços                        |
| `.env`                        | Armazena segredos e parâmetros sensíveis          | vazamento de credenciais e comportamento imprevisível               |
| `admin_config.json`           | Afeta parâmetros efetivos do RAG                  | divergência entre ambiente e comportamento real                     |

---

## 9. Estratégia de execução e validação

A arquitetura é validada por execução incremental, inspeção dos fluxos principais, subida da aplicação e verificação dos componentes críticos.

### Validações esperadas

* a aplicação sobe sem dependências legadas indevidas
* endpoints principais continuam acessíveis
* webhook processa eventos com tenant resolvido corretamente
* retrieval usa collection compatível com o tenant ativo
* logs e métricas continuam disponíveis após refatorações
* documentação e estrutura permanecem coerentes com o código real

### Comandos de apoio

* `git status`
* `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
* `pytest`
* `grep -Rni "pilot-atendimento\|santa tereza\|BA-RAG-PILOTO\|terezia" .`
* comandos de subida do compose e validação dos serviços auxiliares

---

## 10. Integrações externas

| Integração                  | Tipo                 | Finalidade                                                   |
| --------------------------- | -------------------- | ------------------------------------------------------------ |
| Meta Graph API              | API externa          | Receber eventos e enviar mensagens para Instagram/Facebook   |
| Google Gemini               | API externa          | Classificação e geração de resposta                          |
| ChromaDB                    | serviço de vetor     | Armazenar e recuperar base semântica                         |
| PostgreSQL                  | banco relacional     | Persistência transacional, auditoria e suporte a RLS         |
| Redis                       | cache/infra auxiliar | suporte operacional e futura expansão                        |
| SMTP                        | serviço externo      | notificações e fallback operacional                          |
| Google Drive                | serviço externo      | ingestão e sincronização de conteúdo em cenários específicos |
| Prometheus / Grafana / Loki | observabilidade      | métricas, logs e visualização operacional                    |

---

## 11. Segurança e cuidados operacionais

### Onde existem secrets

* `.env`
* credenciais de Meta
* chaves de API de LLM
* credenciais de banco, Redis, SMTP e AWS
* arquivos auxiliares de credenciais locais, quando existirem

### Como variáveis sensíveis são tratadas

* prioritariamente via ambiente
* com suporte opcional a AWS Secrets Manager
* sem hardcode direto no código de runtime

### O que não deve ir para Git

* `.env`
* credenciais de serviço
* chaves privadas
* bases sensíveis
* artefatos gerados com dados reais
* ambientes `venv` e `.venv`
* arquivos locais de sessão, cookies ou dumps operacionais

### O que precisa ser protegido

* segredos de integração
* dados de tenants
* trilhas de auditoria
* configuração operacional efetiva
* scripts que possam expor paths, domínios ou estruturas internas

---

## 12. Limitações atuais

* a arquitetura multi-tenant ainda não está consolidada de forma uniforme em todos os fluxos
* parte do projeto ainda carrega resíduos de legado mono-tenant
* existem sinais de acoplamento excessivo no orchestrator
* a estratégia de avaliação formal do RAG ainda não está madura
* painel, scripts e backend ainda precisam convergir para um contrato de configuração mais limpo
* parte da documentação ainda precisa ser ajustada ao estado real do código

---

## 13. Evoluções previstas

* tornar `tenant_id` um contrato explícito ponta a ponta na arquitetura
* desacoplar ainda mais orquestração, recuperação e composição de resposta
* consolidar ingest e administração tenant-aware
* ampliar avaliação de RAG com métricas formais e datasets controlados
* fortalecer observabilidade aplicada ao pipeline de IA
* evoluir a plataforma para um case mais robusto de backend + IA + governança para contexto público


