#!/usr/bin/env bash
set -euo pipefail

# Script para criar labels no repositório via GitHub CLI (`gh`).
# Uso: export GITHUB_REPO=owner/repo
#      gh auth login (configure sua CLI)
#      GITHUB_REPO=seuusuario/seurepo ./scripts/create_labels.sh

if [ -z "${GITHUB_REPO:-}" ]; then
  echo "Defina a variável de ambiente GITHUB_REPO=owner/repo antes de executar"
  exit 1
fi

echo "Criando labels em ${GITHUB_REPO}..."

gh label create "bug" --color d73a4a --description "Bug funcional que precisa correção" --repo "$GITHUB_REPO" || true
gh label create "enhancement" --color a2eeef --description "Nova funcionalidade / melhoria" --repo "$GITHUB_REPO" || true
gh label create "task" --color 0e8a16 --description "Tarefa operacional geral" --repo "$GITHUB_REPO" || true
gh label create "infra" --color 5319e7 --description "Infraestrutura / deploy / cloud" --repo "$GITHUB_REPO" || true
gh label create "db" --color 8e6ad8 --description "Banco de dados / migrations / backup" --repo "$GITHUB_REPO" || true
gh label create "observability" --color 1d76db --description "Métricas, dashboards e alertas" --repo "$GITHUB_REPO" || true
gh label create "security" --color fbca04 --description "Segurança, LGPD, PII e políticas" --repo "$GITHUB_REPO" || true
gh label create "docs" --color 0075ca --description "Documentação e runbooks" --repo "$GITHUB_REPO" || true
gh label create "test" --color d4c5f9 --description "Testes, smoke tests, E2E" --repo "$GITHUB_REPO" || true
gh label create "performance" --color 0052cc --description "Latência e otimizações" --repo "$GITHUB_REPO" || true
gh label create "blocked" --color b60205 --description "Impeditivo / dependência externa" --repo "$GITHUB_REPO" || true
gh label create "needs-review" --color ffd3b6 --description "Pronto para revisão / QA" --repo "$GITHUB_REPO" || true
gh label create "priority:high" --color b60205 --description "Alta prioridade / urgente" --repo "$GITHUB_REPO" || true
gh label create "help wanted" --color 008672 --description "Precisa de ajuda externa" --repo "$GITHUB_REPO" || true
gh label create "smoke-test" --color 0e8a16 --description "Teste rápido em produção" --repo "$GITHUB_REPO" || true
gh label create "policy" --color a2eeef --description "Mudanças em PolicyGuard e protocolos" --repo "$GITHUB_REPO" || true
gh label create "chore" --color c2e0c6 --description "Manutenção sem entrega funcional" --repo "$GITHUB_REPO" || true

echo "Concluído. Revise as labels em: https://github.com/${GITHUB_REPO}/labels"
