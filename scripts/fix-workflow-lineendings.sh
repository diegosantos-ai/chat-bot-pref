#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "Repo root: $REPO_ROOT"

# Create virtualenv if missing
if [ ! -d "$REPO_ROOT/.venv" ]; then
  echo "Criando virtualenv em $REPO_ROOT/.venv"
  python3 -m venv "$REPO_ROOT/.venv"
fi

# shellcheck source=/dev/null
source "$REPO_ROOT/.venv/bin/activate"

python -m pip install --upgrade pip
pip install --upgrade pre-commit || true

WORKFLOWS_DIR="$REPO_ROOT/.github/workflows"
echo "Normalizando finais de linha em $WORKFLOWS_DIR"
if [ -d "$WORKFLOWS_DIR" ]; then
  if command -v dos2unix >/dev/null 2>&1; then
    find "$WORKFLOWS_DIR" -type f -name '*.yml' -print0 | xargs -0 dos2unix
  else
    find "$WORKFLOWS_DIR" -type f -name '*.yml' -print0 | xargs -0 -I{} sed -i 's/\r$//' {}
  fi
else
  echo "Diretório $WORKFLOWS_DIR não encontrado"
fi

echo "Executando lint via Makefile"
make -C "$REPO_ROOT" lint

echo "Adicionando e commitando alterações (sem push)"
find "$WORKFLOWS_DIR" -type f -name '*.yml' -print0 | xargs -0 git add || true
if git diff --staged --quiet; then
  echo "Nenhuma mudança para commitar"
else
  git commit -m "fix: normalize line endings for workflows (yamllint)"
  echo "Commit criado. Faça push manualmente quando pronto."
fi

echo "Pronto."
