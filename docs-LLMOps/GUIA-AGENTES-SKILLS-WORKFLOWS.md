# Guia Pratico: Agentes, Skills e Workflows

Este guia explica como usar os recursos que estao instalados e disponiveis para o Copilot neste repositorio.

## Objetivo

Usar a camada de governanca ativa do projeto para:

- reduzir ambiguidade na execucao das tasks;
- escolher o especialista certo para cada tipo de mudanca;
- manter coerencia entre runtime ativo, LLMOps e documentacao.

## Camadas Disponiveis

No estado atual do projeto, a camada ativa esta em:

- `.github/agents/`
- `.ai/skills/`
- `.ai/workflows/`
- `.codex/skills/`

## Agentes Disponiveis (`.github/agents/`)

Use esses agentes quando quiser direcionar explicitamente o foco da task.

1. `backend-architect.agent.md`
- Quando usar: FastAPI, endpoints, contratos HTTP, `tenant_id`, `request_id`, `tenant_context`, `tenant_resolver`.

2. `rag-ml.agent.md`
- Quando usar: ingest, retrieval, colecoes por tenant, qualidade RAG e validacao de base documental.

3. `devops-platform.agent.md`
- Quando usar: Docker, Compose, CI, Terraform, AWS, scripts operacionais e deploy.

4. `qa-validation.agent.md`
- Quando usar: estrategia de teste, validacao funcional, risco residual e evidencia de regressao.

5. `docs-operator.agent.md`
- Quando usar: README, docs tecnicas, governanca e alinhamento entre codigo e documentacao.

## Skills de Projeto (`.ai/skills/`)

Esses arquivos funcionam como checklists operacionais reutilizaveis.

1. `deploy-aws-ec2.md`
- Foco: deploy minimo em AWS EC2 com Terraform.

2. `prepare-demo-evidence.md`
- Foco: consolidar evidencias tecnicas de demo/fase.

3. `validate-rag-demo.md`
- Foco: validar ingest/retrieval tenant-aware e falha segura no RAG.

4. `validate-runtime.md`
- Foco: checar startup e fluxo principal apos mudancas de runtime.

5. `validate-tenant-flow.md`
- Foco: garantir entrada, propagacao e consumo correto de `tenant_id`.

## Workflows de Projeto (`.ai/workflows/`)

Workflows sao roteiros de execucao ponta a ponta para tipos comuns de task.

1. `deploy-aws.md`
- Uso: preparar ou revisar deploy minimo em AWS.

2. `ingest-demo.md`
- Uso: executar ingest do tenant demonstrativo e validar retrieval.

3. `refatoracao-fase.md`
- Uso: workflow padrao para task orientada por fases.

4. `validacao-demo.md`
- Uso: validar cenarios funcionais da demonstracao (normal, guardrail, fallback).

## Skill Packs do Codex (`.codex/skills/`)

Esses skills sao a camada especializada por dominio dentro do repositorio.

1. `chat-pref-phase-workflow`
- Papel: skill de entrada para enquadrar ciclo/fase/task/criterio de aceite.

2. `chat-pref-backend-architect`
- Papel: mudancas de backend e contratos HTTP com tenant/request correlacionados.

3. `chat-pref-rag-ml`
- Papel: mudancas em RAG, ingest, retrieval e avaliacao ligada a LLMOps.

4. `chat-pref-devops-platform`
- Papel: stack operacional, Docker/CI/deploy/infra.

5. `chat-pref-qa-validation`
- Papel: validar o minimo necessario e declarar risco residual.

6. `chat-pref-docs-operator`
- Papel: manter documentacao fiel ao estado real do projeto.

## Skills Extras Disponiveis na Sessao

Alem dos arquivos do repositorio, esta sessao tambem expoe skills da extensao/ambiente:

1. `agent-customization`
- Criar/ajustar `copilot-instructions`, `.agent.md`, `.prompt.md`, `.instructions.md`, `SKILL.md`.

2. `summarize-github-issue-pr-notification`
- Resumir issue/PR/notificacao do GitHub.

3. `suggest-fix-issue`
- Sugerir plano de correcao para issue.

4. `form-github-search-query`
- Montar query correta de busca no GitHub.

5. `show-github-search-result`
- Exibir resultados de busca GitHub em tabela amigavel.

## Como Pedir para o Copilot

Use prompts objetivos com 4 blocos:

1. Contexto
- fase/ciclo + arquivo(s) alvo.

2. Especialista
- diga qual agente/skill quer priorizar.

3. Restricoes
- ex.: manter contrato de `tenant_id`, nao mexer em X, mudanca minima.

4. Validacao
- comandos/checks que precisam rodar no final.

Exemplo:

```text
Use o agente backend-architect.
Task: ajustar POST /api/chat para preservar X-Request-ID em todos os logs.
Restricoes: manter tenant_id obrigatorio; nao alterar endpoints nao relacionados.
Validacao: pytest tests -q e curl em /health e /api/chat.
```

## Fluxo Recomendado de Uso

1. Comece por `chat-pref-phase-workflow` para enquadrar a task.
2. Selecione 1 especialista principal (`backend`, `rag`, `devops`, `qa`, `docs`).
3. Aplique 1-2 skills `.ai/skills/` como checklist.
4. Se a task for multi-etapa, siga 1 workflow `.ai/workflows/`.
5. Feche com: arquivos alterados, validacao executada, status atual, proximo passo.

## Erros Comuns e Como Evitar

1. Pedir task ampla sem fase/escopo.
- Solucao: sempre citar fase e criterio de aceite.

2. Misturar operacao ativa com stack-alvo futura.
- Solucao: diferenciar runtime validado vs arquitetura-alvo de LLMOps.

3. Validar pouco ou validar demais.
- Solucao: usar `qa-validation` e executar somente checks aderentes a task.

4. Ignorar contratos transversais.
- Solucao: explicitar sempre `tenant_id` e, quando aplicavel, `request_id`.

## Template Rapido (Copiar e Adaptar)

```text
Fase/ciclo: [Fundacao Operacional | Fase 1 LLMOps]
Agente principal: [backend-architect | rag-ml | devops-platform | qa-validation | docs-operator]
Skill(s) de apoio: [nome1, nome2]
Workflow (se houver): [nome]
Task: [objetivo em 1-2 linhas]
Restricoes: [lista curta]
Validacao esperada: [comandos/checks]
Saida: arquivos alterados + validacao + status + proximo passo
```

## Referencias

- `AGENTS.md`
- `README.md`
- `.github/copilot-instructions.md`
- `.github/agents/`
- `.ai/skills/`
- `.ai/workflows/`
- `.codex/skills/`
