---
name: chat-pref-docs-operator
description: Usar no repositorio Chat Pref quando a tarefa tocar `README.md`, `AGENTS.md`, `docs-fundacao-operacional/`, `docs-LLMOps/`, `.github/`, `.ai/` ou qualquer texto de arquitetura, operacao, tenant, deploy, CI/CD, demo, benchmark, tracking ou governanca. Acionar para alinhar estado atual, arquitetura-alvo e evidencias sem marketing nem promessa indevida.
---

# Chat Pref Docs Operator

Manter a documentacao e a governanca alinhadas ao estado real do projeto, preservando a separacao entre Fundacao Operacional validada e Fase 1 de LLMOps.

## Ler antes de editar

- `AGENTS.md`
- `README.md`
- `docs-fundacao-operacional/contexto.md`
- `docs-fundacao-operacional/arquitetura.md`
- `docs-fundacao-operacional/planejamento_fases.md`
- `docs-LLMOps/README.md`
- `docs-LLMOps/CONTEXTO-LLMOps.md`
- `docs-LLMOps/ARQUITETURA-LLMOps.md`
- `docs-LLMOps/PLANEJAMENTO-LLMOps.md`
- `.github/agents/docs-operator.agent.md`
- `.ai/workflows/refatoracao-fase.md`

## Workflow

1. Identificar se a mudanca descreve estado atual, contrato consolidado ou arquitetura futura.
2. Atualizar somente os documentos impactados pela mudanca real.
3. Manter `tenant_id` e `request_id` como contratos explicitos quando o texto tocar fluxos criticos.
4. Cruzar o texto com codigo, runtime e evidencias antes de concluir.
5. Fechar com narrativa curta, verificavel e sem marketing.

## Guardrails

- Nao prometer comportamento nao validado.
- Nao tratar stack-alvo de LLMOps como runtime ativo.
- Preservar `AGENTS.md` enxuto e governavel.
- Manter `.codex/skills/`, `.github/agents/` e `.ai/` coerentes entre si quando a governanca for alterada.

## Validacao sugerida

- Leitura cruzada dos documentos afetados
- Busca por endpoints, contratos e nomes de fase com `rg`
- Conferencia de coerencia entre texto, runtime e artefatos de evidencia
