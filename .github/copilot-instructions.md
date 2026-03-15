# Copilot Instructions

## Fonte de verdade

Leia nesta ordem:

1. `AGENTS.md`
2. `README.md`

### Se a task tocar a Fundação Operacional
Leia também:

3. `docs-fundacao-operacional/contexto.md`
4. `docs-fundacao-operacional/arquitetura.md`
5. `docs-fundacao-operacional/planejamento_fases.md`

### Se a task tocar a Fase 1 — LLMOps, Avaliação e Governança
Leia também:

6. `docs-LLMOps/README.md`
7. `docs-LLMOps/CONTEXTO-LLMOps.md`
8. `docs-LLMOps/ARQUITETURA-LLMOps.md`
9. `docs-LLMOps/PLANEJAMENTO_LLMOps.md`

### Se a task tocar decisões arquiteturais da fase LLMOps
Considere também:

10. `docs-LLMOps/adrs/`

### Se a task tocar setup, benchmark, avaliação formal ou operação offline
Considere também:

11. `docs-LLMOps/runbooks/`

### Se a task tocar as fases finais da Fundação Operacional
Leia também:

12. `docs-fundacao-operacional/guardrail_rastreavel.md`
13. `docs-fundacao-operacional/genai_com_metodo.md`

### Se a task tocar validação de resposta e cenários da Fundação Operacional
Consulte também:

14. `docs-fundacao-operacional/matriz_cenarios_validacao.md`
15. `docs-fundacao-operacional/rubrica_qualidade_resposta.md`

### Se a task tocar infraestrutura, evidências ou narrativa técnica da Fundação Operacional
Consulte também:

16. `docs-fundacao-operacional/fase_13_aws_deploy.md`
17. `docs-fundacao-operacional/evidencias_case.md`
18. `docs-fundacao-operacional/diario_bordo.md`

Use `.codex/skills/`, `.github/agents/`, `.ai/skills/` e `.ai/workflows/` como camada ativa de governanca.

---

## Estrutura atual do projeto

O projeto está organizado em dois ciclos complementares:

### Fundação Operacional
Representa a base funcional já validada do sistema, incluindo runtime principal, contratos ativos, observabilidade mínima, auditoria, CI e deploy remoto demonstrativo.

### Fase 1 — LLMOps, Avaliação e Governança
Representa a nova etapa de evolução do projeto, com foco em:

- rastreabilidade experimental por tenant;
- versionamento formal de prompts, policies e configurações de RAG;
- benchmark reproduzível;
- avaliação formal de RAG;
- observabilidade de qualidade, latência e custo;
- orquestração offline;
- deriva semântica;
- governança e explicabilidade técnica.

---

## Estado atual do projeto

O runtime ativo atual corresponde à **Fundação Operacional**: uma base funcional já validada, incluindo chat direto, webhook, RAG, guardrails, auditoria, observabilidade, CI e deploy remoto demonstrativo.

### Escopo implementado
- FastAPI mínimo
- `GET /`
- `GET /health`
- `POST /api/chat`
- `POST /api/webhook`
- `POST /api/telegram/webhook`
- `GET /api/rag/status`
- `POST /api/rag/documents`
- `POST /api/rag/ingest`
- `POST /api/rag/query`
- `POST /api/rag/reset`
- `tenant_id` explícito no chat direto
- `X-Request-ID` propagado no chat e no webhook
- contexto de tenant por request
- persistência local por tenant
- auditoria `audit.v1` por tenant
- RAG tenant-aware com ingest limpa
- composição generativa mínima com `LLM_PROVIDER=mock`
- prompts e política textual versionados
- `policy_pre` e `policy_post` com `PolicyDecision`
- logs estruturados correlacionados por `request_id`
- `/metrics`
- traces com OpenTelemetry persistidos por `request_id`
- tenant demonstrativo e base documental fictícia
- integração Telegram com entrega `dry_run` local e webhook HTTPS ativo no ambiente remoto demonstrativo
- Docker funcional
- smoke tests e retrieval checks
- workflow de CI versionado em `.github/workflows/ci.yml`
- deploy remoto mínimo validado em AWS com Terraform, EC2 única e smoke remoto
- endpoint HTTPS público estável no ambiente remoto demonstrativo

### Não assuma como ativos no runtime atual
- experiment tracking plenamente integrado ao runtime
- benchmark reproduzível já operando como contrato ativo
- avaliação formal de RAG já consolidada
- Airflow operando como camada offline ativa
- monitoramento de deriva semântica em produção
- multi-LLM validado como caminho padrão reproduzível
- bot Telegram como parte do bootstrap reproduzível sem secrets externos
- painel/admin no caminho crítico
- deploy remoto endurecido com domínio próprio, secrets gerenciados e CD completo

---

## Guardrails de alteração

- mantenha mudanças mínimas e ligadas a uma fase/task
- não trate arquitetura futura como se já estivesse implementada
- não reintroduza arquivos, termos ou estruturas históricas removidas
- `tenant_id` é contrato explícito, não detalhe opcional
- preserve o contrato mínimo de `request_id` nos fluxos que já o expõem
- não versione `.env` real nem segredos
- se a alteração impactar arquitetura, tenant, RAG, guardrails, Docker, benchmark, tracking, Airflow ou operação, atualize a documentação correspondente
- preserve a separação entre:
  - operação;
  - experimentação;
  - benchmark;
  - orquestração offline
- não confunda auditoria operacional com experiment tracking
- na Fase 1, não trate stack-alvo de LLMOps como runtime ativo sem validação correspondente

---

## Áreas ativas principais

### Runtime principal
- `app/main.py`
- `app/settings.py`
- `app/api/`
- `app/contracts/`
- `app/services/`
- `app/storage/`
- `app/tenant_context.py`
- `app/tenant_resolver.py`
- `scripts/`
- `tenants/`
- `tests/`
- `docker-compose.yml`
- `docker-compose.local.yml`

### Documentação
- `README.md`
- `docs-fundacao-operacional/`
- `docs-LLMOps/`

### Governança
- `.github/`
- `.ai/`

---

## Áreas fora do caminho crítico atual

Diretórios como `admin-api/`, `admin-panel/`, `db/`, `panel/`, `logging/`, `dashboards/`, `grafana/` e afins não devem ser assumidos como parte do runtime mínimo validado sem confirmação explícita da task.

Da mesma forma, componentes da nova fase, como tracking experimental, benchmark operacionalizado, Airflow e deriva semântica, não devem ser tratados como ativos apenas por já estarem documentados.

---

## Regras específicas da nova fase

### Tenant-awareness
- `tenant_id` deve permanecer explícito nos fluxos críticos
- ausência de tenant deve gerar erro controlado
- contexto, persistência, auditoria, benchmark e tracking devem respeitar segregação por tenant

### Auditoria vs. experimentação
- auditoria operacional registra fatos do atendimento
- experiment tracking registra comparação técnica entre versões, métricas e artifacts
- essas camadas devem ser correlacionáveis, mas não fundidas

### Versionamento
- prompts, policies e configurações críticas devem ser tratados como artefatos versionáveis
- nenhum resultado experimental relevante deve existir sem vínculo a versões explícitas

### Benchmark
- benchmark deve ser tratado como contrato de avaliação
- quando aplicável, o recorte por tenant deve ser preservado
- não promova mudanças relevantes por percepção isolada

### Orquestração offline
- Airflow deve ser tratado como camada offline separada do backend principal
- não mover responsabilidade do request path para jobs offline por conveniência

---

## Validação mínima recomendada

Use apenas validações coerentes com a task.

### Runtime principal
- `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
- `.venv/bin/python scripts/lint_runtime.py`
- `.venv/bin/python scripts/check_runtime_residues.py`
- `.venv/bin/python -m pytest tests -q`
- `docker build -t chat-pref-ci -f Dockerfile .`
- `docker compose -f docker-compose.yml config`
- `docker compose -f docker-compose.yml up -d --build`
- `curl http://localhost:8000/`
- `curl http://localhost:8000/health`
- `curl -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" -d '{"tenant_id":"prefeitura-demo","message":"Teste"}'`
- `curl -X POST http://localhost:8000/api/webhook -H "Content-Type: application/json" -d '{"tenant_id":"prefeitura-demo","message":"Teste"}'`
- `curl "http://localhost:8000/api/rag/status?tenant_id=prefeitura-demo"`
- `.venv/bin/python scripts/smoke_tests.py --env prod --runtime-mode reuse --tenant-id prefeitura-vila-serena --tenant-manifest tenants/prefeitura-vila-serena/tenant.json --phase-report fase11`

### Fase LLMOps
Quando aplicável:
- validação do ambiente base e dev
- validação de imports das dependências da fase
- validação de benchmark
- validação de tracking experimental
- validação de versionamento de artefatos
- validação de ambiente offline
- validação de correlação entre contexto operacional e execução experimental

---

## Forma de trabalho

- explique o bloco antes de mudanças maiores
- faça o menor corte que produza valor real
- valide imediatamente depois
- diferencie explicitamente:
  - o que já existe no runtime;
  - o que é contrato consolidado;
  - o que é arquitetura-alvo da fase LLMOps;
  - o que é apenas stack-alvo

Feche cada tarefa informando:
- arquivos alterados
- validação executada
- status atual
- próximo passo
