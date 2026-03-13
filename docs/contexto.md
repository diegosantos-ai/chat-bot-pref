# Contexto do Projeto

## 1. Identificação

* **Projeto:** Chat Pref — Plataforma multi-tenant de atendimento digital para prefeituras
* **Repositório:** `/media/diegosantos/TOSHIBA EXT/Projetos/Desenvolvendo/chat-bot-pref`
* **Responsável:** Diego Santos
* **Área:** Engenharia de Software / IA Aplicada / RAG / DevOps / Observabilidade / Automação
* **Status atual:** em andamento
* **Fase atual:** Refatoração estrutural para arquitetura multi-tenant consistente
* **Task atual:** Sanitizar legado mono-tenant, remover hardcodes e preparar base limpa para evolução do núcleo tenant-aware

---

## 2. Objetivo do projeto

Este projeto existe para demonstrar a capacidade de projetar, operar e refatorar uma plataforma de atendimento digital com IA aplicada ao setor público, baseada em FastAPI, RAG, integrações com canais Meta, observabilidade, auditoria e isolamento multi-tenant.

O projeto resolve um problema real de atendimento informativo para prefeituras, com foco em segurança, rastreabilidade, governança e capacidade de expansão para múltiplos clientes com isolamento de contexto, dados e base de conhecimento.

No portfólio, ele demonstra capacidade em:

* arquitetura de backend orientada a serviços
* integração entre API, RAG, auditoria e canais externos
* refatoração de legado para arquitetura mais robusta
* preocupação com operação, observabilidade e compliance
* construção de soluções de IA aplicadas a contexto público

---

## 3. Problema que o projeto ataca

O projeto ataca a necessidade de oferecer atendimento digital automatizado e informativo para cidadãos, preservando clareza institucional, controle de risco e separação de dados entre diferentes prefeituras.

### Dor técnica e operacional

* atendimento repetitivo e de baixo valor operacional ainda depende de humanos
* bases de conhecimento precisam ser consultadas de forma contextual
* respostas precisam ser rastreáveis e seguras
* o sistema precisa evoluir de um modelo inicialmente mono-tenant para uma estrutura multi-tenant real
* o legado contém resíduos de implementação inicial, hardcodes e inconsistências de arquitetura

### Habilidade que o projeto prova

* desenho e refatoração de arquitetura backend com IA aplicada
* construção de pipelines com classificação, guardrails e recuperação semântica
* operação de serviços integrados com observabilidade e auditoria
* transição de um protótipo funcional para um sistema mais maduro e defensável tecnicamente

### Contexto real de uso

Esse tipo de solução é aplicável em:

* atendimento digital municipal
* assistentes institucionais com escopo controlado
* plataformas white-label de atendimento público
* produtos com RAG, compliance e trilha de decisão auditável

---

## 4. Escopo

### Incluído

* API backend em FastAPI
* pipeline de processamento de mensagens com classificação, guardrails e RAG
* integração com webhook Meta para Instagram/Facebook
* auditoria e métricas operacionais
* arquitetura orientada a multi-tenant
* painel/admin e utilitários de ingest/configuração
* observabilidade e documentação operacional
* refatoração estrutural para eliminação de legado mono-tenant

### Não incluído neste momento

* produto final comercial pronto para produção em larga escala
* onboarding automatizado completo de novos tenants
* billing/metering comercial
* painel de gestão totalmente maduro por tenant
* suíte completa de avaliação automatizada de RAG com benchmark formal
* governança enterprise completa de identidade e acesso

---

## 5. Estado atual

O projeto já possui uma base funcional relevante, mas ainda passa por uma refatoração importante para eliminar acoplamentos legados e consolidar a arquitetura multi-tenant.

### Já concluído

* estrutura principal do backend
* rotas FastAPI para chat, webhook, analytics, deploy e admin
* integração inicial com canais Meta
* pipeline de classificação, policy guard e RAG
* componentes de auditoria, métricas e observabilidade
* documentação operacional relevante
* compose e artefatos de infraestrutura para ambiente local/VPS
* base inicial de suporte a multi-tenant no banco e no RAG

### Está funcionando

* subida do projeto como aplicação backend modular
* endpoint de health
* fluxo geral de processamento via orchestrator
* componentes centrais de RAG, classificação e policy guard
* estrutura de auditoria e logs
* organização geral do repositório e documentação técnica

### Ainda pendente

* consolidar tenant resolution ponta a ponta em todos os fluxos
* remover defaults e resíduos de base mono-tenant
* limpar paths, nomes e referências históricas do projeto original
* revisar scripts operacionais e ingest para operação tenant-aware
* alinhar backend, painel admin e utilitários à mesma fonte de configuração
* fortalecer critérios de avaliação e validação do RAG

### Em validação

* sanitização do legado técnico e textual
* substituição de hardcodes por configuração explícita
* revisão da coerência arquitetural entre README, código e operação real
* reestruturação do fluxo para uso explícito de `tenant_id`

### Bloqueado

* evolução confiável do produto enquanto permanecerem acoplamentos legados e defaults implícitos
* demonstração mais madura do case para contexto profissional enquanto o projeto ainda carregar inconsistências de identidade e arquitetura

---

## 6. Histórico resumido por fase

### Fase 1 — Protótipo funcional inicial

* **Objetivo:** estruturar uma aplicação inicial de atendimento automatizado com backend e fluxo de mensagens
* **Entregas:** API básica, primeiros endpoints, fluxo inicial de resposta
* **Validação:** aplicação subindo e respondendo cenários básicos
* **Status:** concluída

### Fase 2 — Integração com canais e expansão funcional

* **Objetivo:** integrar canais externos e organizar o fluxo de atendimento
* **Entregas:** webhook Meta, adaptação de payloads, envio de respostas
* **Validação:** recebimento e processamento de eventos externos
* **Status:** concluída

### Fase 3 — Evolução para RAG, guardrails e auditoria

* **Objetivo:** aumentar qualidade de resposta, segurança e rastreabilidade
* **Entregas:** retriever, composer, policy guard, eventos de auditoria, analytics
* **Validação:** pipeline completo de classificação + política + recuperação + resposta
* **Status:** concluída com ajustes pendentes

### Fase 4 — Infraestrutura, operação e observabilidade

* **Objetivo:** tornar o projeto operável em ambiente mais realista
* **Entregas:** dockerização, compose, logging, dashboards, documentação operacional
* **Validação:** serviços subindo, logs e métricas expostos
* **Status:** concluída parcialmente

### Fase 5 — Migração arquitetural para multi-tenant

* **Objetivo:** transformar o projeto em base white-label com isolamento de dados e contexto
* **Entregas:** `tenant_context`, `tenant_resolver`, estrutura RLS, collections por tenant
* **Validação:** tenant resolvido e aplicado em partes do fluxo
* **Status:** em andamento

### Fase 6 — Refatoração e saneamento do legado

* **Objetivo:** remover hardcodes, identidades antigas, bases legadas e defaults perigosos
* **Entregas:** limpeza estrutural, neutralização de configuração, reset de base e revisão de operação
* **Validação:** ausência de resíduos históricos e funcionamento com configuração limpa
* **Status:** em andamento

---

## 7. Stack e componentes principais

* **Linguagens:** Python, SQL, Bash, YAML, TypeScript
* **Ferramentas:** FastAPI, Docker, Docker Compose, asyncpg, ChromaDB, Git, Prometheus, Grafana, Loki, Playwright
* **Serviços:** API backend, painel admin, PostgreSQL, Redis, ChromaDB, componentes de logging/monitoramento
* **Cloud / ambiente:** local e VPS Linux, com integração a serviços compartilhados de infraestrutura

---

## 8. Estrutura operacional

O projeto está organizado como um monorepo funcional com backend principal, painel administrativo, scripts operacionais, componentes de banco, documentação e artefatos auxiliares.

* **Branch principal:** a confirmar na retomada operacional
* **Estratégia de branches:** branch principal estável + branches de refatoração/feature
* **Diretórios principais:**

  * `app/` — backend principal
  * `app/api/` — rotas e endpoints
  * `app/rag/` — recuperação, embeddings e composição
  * `app/orchestrator/` — pipeline principal
  * `app/audit/` — auditoria
  * `db/` — schema e migrations
  * `admin-panel/` — frontend administrativo
  * `docs/` — documentação técnica e operacional
  * `logging/`, `dashboards/`, `grafana/` — observabilidade
  * `scripts/` — utilitários e automações
* **Arquivos sensíveis:**

  * `.env`
  * credenciais de serviços
  * segredos de Meta/API/SMTP/AWS
* **Arquivos críticos de configuração:**

  * `app/settings.py`
  * `docker-compose.yml`
  * `docker-compose.local.yml`
  * `admin_config.json`
  * arquivos de logging e dashboards
* **Documentos de apoio:**

  * `README.md`
  * `GUIA_INFRA.md`
  * `INFRASTRUCTURE_CHECKLIST.md`
  * `docs/runbook.md`
  * documentos de migração e observabilidade

---

## 9. Pré-requisitos para retomada

* [ ] Estar na branch correta de refatoração
* [ ] Validar `git status`
* [ ] Revisar a fase atual de saneamento/refatoração
* [ ] Revisar a task atual antes de alterar código
* [ ] Confirmar critério de aceite da etapa corrente
* [ ] Validar o comportamento real dos arquivos críticos antes de modificar qualquer fluxo
* [ ] Confirmar que não há segredos sendo expostos em arquivos versionados
* [ ] Confirmar que a mudança proposta não reintroduz defaults mono-tenant

---

## 10. Critério de sucesso atual

O próximo ciclo será considerado concluído quando:

* o projeto deixar de depender de paths, nomes, bases e identidades legadas
* os fluxos críticos passarem a operar com configuração explícita e sem defaults históricos perigosos
* o uso de `tenant_id` estiver claramente encaminhado como contrato arquitetural do sistema
* os componentes centrais do backend permanecerem funcionando após a sanitização
* backend, painel e scripts principais estiverem alinhados à nova base limpa

---

## 11. Riscos operacionais

### Risco 1 — Quebrar runtime ao remover hardcodes

* **Impacto:** endpoints, scripts ou rotinas de deploy podem parar de funcionar
* **Como identificar:** falhas em inicialização, paths inválidos, erros em scripts e serviços
* **Como reduzir:** revisar cada acoplamento antes da substituição e validar por bloco funcional

### Risco 2 — Multi-tenant incompleto ou inconsistente

* **Impacto:** fluxo operar com tenant implícito, errado ou ausente
* **Como identificar:** falhas em retrieval, uso de collection default, comportamento divergente entre webhook e chat
* **Como reduzir:** explicitar entrada de `tenant_id`, revisar `tenant_context` e remover defaults silenciosos

### Risco 3 — Limpeza cosmética sem correção estrutural

* **Impacto:** projeto parecer mais limpo, mas continuar arquiteturalmente frágil
* **Como identificar:** documentação neutra, porém código ainda preso ao legado
* **Como reduzir:** priorizar runtime, configuração e fluxo de tenant antes da sanitização textual ampla

### Risco 4 — Reintrodução de resíduos históricos

* **Impacto:** termos, paths ou bases antigas voltarem por scripts auxiliares ou artefatos esquecidos
* **Como identificar:** busca global retornando termos proibidos
* **Como reduzir:** criar verificação recorrente e reforçar `.gitignore`

### Risco 5 — Divergência entre código, docs e operação real

* **Impacto:** baixa confiança no projeto e dificuldade de manutenção/apresentação
* **Como identificar:** README e arquitetura afirmando comportamentos não refletidos no código
* **Como reduzir:** atualizar documentação apenas com base em comportamento validado

---

## 12. Bloqueios atuais

* presença de resíduos mono-tenant e identidades antigas no código e nos scripts
* ausência de padronização definitiva para entrada e propagação de `tenant_id`
* acoplamentos implícitos entre backend, admin e utilitários de ingest
* documentação ainda parcialmente desalinhada com o estado real da aplicação
* necessidade de limpar o projeto sem quebrar o fluxo já existente

---

## 13. Próximo passo objetivo

Concluir a limpeza funcional do runtime, removendo hardcodes de paths, bases e identidades legadas dos componentes críticos, e definir um contrato explícito para entrada e propagação de `tenant_id` nos fluxos principais do sistema.

---

## 14. Forma de validação

### Comandos

* `git status`
* `grep -Rni "pilot-atendimento\|santa tereza\|BA-RAG-PILOTO\|terezia" .`
* `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
* `pytest`
* comandos específicos de subida/validação do painel e dos serviços Docker

### Evidências esperadas

* ausência de termos proibidos no repositório funcional
* aplicação inicializando sem depender de paths legados
* endpoints principais respondendo após a limpeza
* fluxo de tenant mais explícito e menos dependente de defaults implícitos
* diff final coerente com a estratégia de refatoração

---

## 15. Observações de continuidade

* o projeto nasceu como primeiro sistema maior e acumulou estilos diferentes de implementação ao longo do tempo
* parte relevante do trabalho atual é transformar um sistema funcional porém heterogêneo em uma arquitetura coerente e defensável
* a prioridade atual não é adicionar features, mas consolidar estrutura, clareza e consistência operacional
* a limpeza deve começar pelo que afeta runtime, tenant e configuração, não por estética documental
* o projeto tem alto valor de portfólio por combinar backend, IA aplicada, setor público, guardrails, auditoria e refatoração arquitetural
* toda documentação futura deve refletir o estado real do código e não o estado desejado