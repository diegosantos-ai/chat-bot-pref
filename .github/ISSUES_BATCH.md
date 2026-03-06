<!--
Arquivo gerado: ISSUES_BATCH.md
Uso: copie o bloco 'Título' para o campo de título do Issue e cole o conteúdo 'Descrição' no campo de descrição.
Sugestão: adicione labels (ex: `task`, `infra`, `observability`, `security`) e milestone `TerezIA - Deploy`.
-->

# Issues em lote — TerezIA (descrições prontas)

Cada bloco abaixo contém um *Título* e uma *Descrição* (com checklist/critérios) prontos para colar na criação de uma issue no GitHub.

---

## 1) Título
Validar infraestrutura e variáveis de ambiente

### Descrição
- Objetivo: garantir que a infraestrutura e segredos estejam prontos e seguros para o deploy.
- Passos:
  - Conferir servidores, permissões de acesso e ambientes (prod/homolog/dev).
  - Validar tokens e segredos (Meta, OpenAI, DATABASE_URL, Page Access Token).
  - Documentar acessos e armazenar segredos em Secrets Manager/variáveis de ambiente seguras.

### Critérios de aceitação
- [ ] Acesso SSH/API validado para todos os servidores necessários
- [ ] Tokens e secrets armazenados em local seguro (secrets manager ou GitHub Secrets)
- [ ] Checklist de segurança registrado em `docs/` e revisado

### Sugestões
Labels: `infra`, `security`, `task`
Milestone: `TerezIA - Deploy`

Start: 2026-01-17
Due: 2026-01-23

---

## 2) Título
Executar deploy do backend (FastAPI)

### Descrição
- Objetivo: disponibilizar a API em ambiente alvo com health-checks e rollback.
- Passos:
  - Preparar imagem/container Docker (ou processo equivalente) para deploy.
  - Configurar variáveis de ambiente, health endpoint e logs.
  - Validar deploy e processos de rollback.

### Critérios de aceitação
- [ ] Serviço responde em `/health`
- [ ] Logs de startup e erros acessíveis
- [ ] Rollback testado com sucesso

### Sugestões
Labels: `deploy`, `infra`, `task`
Milestone: `TerezIA - Deploy`

Start: 2026-01-17
Due: 2026-01-23

---

## 3) Título
Subir serviços auxiliares (ChromaDB, PostgreSQL)

### Descrição
- Objetivo: provisionar e validar as dependências (ChromaDB e PostgreSQL).
- Passos:
  - Provisionar instâncias/containers para ChromaDB e PostgreSQL.
  - Aplicar schema `db/schema.sql` e validar tabelas `audit_events`, `rag_queries`.
  - Configurar backups e extensão `pgcrypto`.

### Critérios de aceitação
- [ ] Schema aplicado sem erros
- [ ] Backups agendados e testados
- [ ] Conexões validadas a partir da API

### Sugestões
Labels: `infra`, `db`, `task`

Start: 2026-01-17
Due: 2026-01-23

---

## 4) Título
Integrar observabilidade (logs, métricas, dashboards)

### Descrição
- Objetivo: expor métricas e criar dashboards operacionais.
- Passos:
  - Configurar logs estruturados (JSON) e exportadores (Prometheus/StatsD).
  - Criar views no DB com `analytics/v1/views.sql`.
  - Montar dashboard inicial (Grafana/Metabase) com KPIs (latência p95, fallback rate, erros).

### Critérios de aceitação
- [ ] Métricas p95 e latência disponíveis no dashboard
- [ ] Fallback rate e erros por canal monitorados
- [ ] Alertas configurados para picos críticos

### Sugestões
Labels: `observability`, `monitoring`, `task`

Start: 2026-01-17
Due: 2026-01-23

---

## 5) Título
Testar guardrails e protocolos de crise (Policy Guard)

### Descrição
- Objetivo: garantir respostas estáticas e bloqueios seguros para entradas de crise.
- Passos:
  - Executar casos de teste para inputs de crise (suicídio, violência doméstica).
  - Validar se o `PolicyGuard` retorna prompts estáticos aprovados.
  - Verificar que não há vazamento de PII em respostas públicas.

### Critérios de aceitação
- [ ] Casos de crise retornam o script estático correto
- [ ] Não há vazamento de PII em respostas públicas
- [ ] Testes automatizados para gatilhos de crise criados e verdes

### Sugestões
Labels: `security`, `policy`, `test`

Start: 2026-01-17
Due: 2026-01-23

---

## 6) Título
Realizar smoke tests em produção

### Descrição
- Objetivo: validar fluxos principais no ambiente de produção.
- Testes a executar (exemplos):
  - Perguntas institucionais: telefone da prefeitura, horários, documentos.
  - Fluxos de redirecionamento: agendamento, parcelamento de dívida.
  - Casos de crise e comentário público com PII (simulação controlada).

### Critérios de aceitação
- [ ] Fluxos principais retornam respostas corretas
- [ ] Redirecionamentos apontam para canais humanos corretos
- [ ] Auditoria criada para cada teste (linhas em `audit_events`)

### Sugestões
Labels: `smoke-test`, `qa`, `task`

Start: 2026-01-17
Due: 2026-01-23

---

## 7) Título
Documentar procedimentos de operação e contingência (runbook)

### Descrição
- Objetivo: criar um runbook com passos de deploy, rollback e resposta a incidentes.
- Passos:
  - Escrever runbook em `docs/runbook.md` com passos claros.
  - Incluir contatos de escalonamento, rotinas de backup e testes de restauração.

### Critérios de aceitação
- [ ] Runbook disponível em `docs/`
- [ ] Contatos e passos validados por responsável
- [ ] Procedimento de restauração documentado e testado

### Sugestões
Labels: `docs`, `ops`, `task`

Start: 2026-01-17
Due: 2026-01-23

---

## 8) Título
Treinar equipe de atendimento e definir escalonamento

### Descrição
- Objetivo: capacitar equipe para usar dashboards e interpretar alertas.
- Passos:
  - Preparar material de treinamento e checklist de operação.
  - Realizar sessão(s) de treinamento com equipe responsável.

### Critérios de aceitação
- [ ] Sessão de treinamento realizada
- [ ] Responsáveis e horários documentados no Project
- [ ] Material de apoio disponível em `docs/`

### Sugestões
Labels: `ops`, `training`, `task`

Start: 2026-01-17
Due: 2026-01-23

---

## 9) Título
Criar automações e labels para o GitHub Project

### Descrição
- Objetivo: padronizar labels, milestones e automações (mover cards ao fechar issues).
- Itens sugeridos:
  - Labels: `infra`, `bug`, `feature`, `task`, `observability`, `security`, `smoke-test`, `docs`
  - Milestones: `TerezIA - Deploy`, `TerezIA - Observability`.
  - Automatização: mover card para `Done` ao fechar a issue relacionada.

### Critérios de aceitação
- [ ] Labels criadas no repositório
- [ ] Milestones definidas
- [ ] Automação de Project configurada (issues → colunas)

---

## Como usar este arquivo
1. Abra a criação de uma nova issue no GitHub.
2. Cole o *Título* no campo de título.
3. Cole o bloco *Descrição* no campo de descrição.
4. Adicione labels e milestone sugeridos.
5. Clique em `Create` (ou marque `Create more` para inserir várias issues seguidas).

----
Arquivo gerado automaticamente por assistente — ajuste textos conforme necessidade.
