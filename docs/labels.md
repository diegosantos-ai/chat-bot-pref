# Labels recomendadas — {bot_name}

Este arquivo descreve as labels sugeridas para o repositório e como usá-las no GitHub Project.

## Labels principais (nome — cor HEX — uso)

- `bug` — #d73a4a — Bug funcional que precisa correção.
- `enhancement` (feature) — #a2eeef — Nova funcionalidade ou melhoria.
- `task` — #0e8a16 — Tarefa operacional geral.
- `infra` — #5319e7 — Infraestrutura, deploy, cloud.
- `db` — #8e6ad8 — Banco de dados, migrations, backups.  
- `observability` — #1d76db — Métricas, dashboards e alertas.
- `security` — #fbca04 — Segurança, LGPD, PII e políticas.
- `docs` — #0075ca — Documentação e runbooks.
- `test` / `qa` — #d4c5f9 — Testes, smoke tests, E2E.
- `performance` — #0052cc — Latência e otimizações.
- `blocked` — #b60205 — Impedido por dependência externa.
- `needs-review` — #ffd3b6 — Pronto para revisão/QA.
- `priority:high` — #b60205 — Alta prioridade urgente.
- `help wanted` — #008672 — Precisa de ajuda externa.

## Labels opcionais

- `smoke-test` — #0e8a16 — Testes rápidos em produção.
- `policy` — #a2eeef — Alterações no `PolicyGuard` e protocolos sensíveis.
- `chore` — #c2e0c6 — Manutenção sem funcionalidade nova.

## Recomendações de uso

- Use uma label de propósito (ex: `infra`, `db`, `observability`) sempre que possível.
- Combine com uma label de prioridade (`priority:high`) quando necessário.
- Evite criar muitas labels parecidas — mantenha a lista enxuta (10–14 labels).

## Milestones sugeridas

- `{bot_name} - Deploy`
- `{bot_name} - Observability`

## Automações sugeridas (Projects)

- Mover card para `In Progress` quando a issue for atribuída.
- Mover card para `Done` quando a issue for fechada.

## Criar labels (UI) — passo rápido

1. Vá em `Settings` → `Labels` no repositório.
2. Clique em `New label`, insira o nome, cor (hex) e descrição curta.
3. Repita para cada label da lista acima.

## Criar labels via GitHub CLI (exemplo)

Se preferir criar via `gh` CLI, use o comando:

```bash
gh label create "bug" --color d73a4a --description "Bug funcional que precisa correção"
gh label create "infra" --color 5319e7 --description "Infraestrutura / deploy"
```

Repita para as demais labels substituindo nome, cor e descrição.

---
Guia gerado automaticamente — ajuste cores e textos conforme preferência do time.
