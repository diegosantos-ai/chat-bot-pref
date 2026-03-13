#!/usr/bin/env bash
set -euo pipefail
# List Chroma collections for the project
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$ROOT_DIR/.venv/bin/python"

if [ ! -x "$PYTHON" ]; then
  echo "ERROR: python venv not found at $PYTHON" >&2
  exit 1
fi

SUDO_CMD=""
if [ "$(id -un)" != "pilot" ]; then
  SUDO_CMD="sudo -u pilot"
fi

echo "Listing collections using Python at: $PYTHON (as: ${SUDO_CMD:-$(id -un)})"
$SUDO_CMD "$PYTHON" - <<'PY'
from app.rag.ingest import list_collections
import json
print(json.dumps(list_collections(), indent=2, ensure_ascii=False))
PY
