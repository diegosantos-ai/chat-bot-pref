#!/usr/bin/env bash
set -euo pipefail
# Run a retrieval query against the default retriever
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$ROOT_DIR/.venv/bin/python"
QUERY=${1:-"qual o horário de funcionamento?"}

if [ ! -x "$PYTHON" ]; then
  echo "ERROR: python venv not found at $PYTHON" >&2
  exit 1
fi

SUDO_CMD=""
if [ "$(id -un)" != "pilot" ]; then
  SUDO_CMD="sudo -u pilot"
fi

echo "Query: $QUERY"
$SUDO_CMD "$PYTHON" -m app.rag.retriever "$QUERY"
