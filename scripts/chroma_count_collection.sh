#!/usr/bin/env bash
set -euo pipefail
# Count chunks in a Chroma collection
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$ROOT_DIR/.venv/bin/python"
COLLECTION=${1:-default_knowledge_base}

if [ ! -x "$PYTHON" ]; then
  echo "ERROR: python venv not found at $PYTHON" >&2
  exit 1
fi

SUDO_CMD=""
if [ "$(id -un)" != "pilot" ]; then
  SUDO_CMD="sudo -u pilot"
fi

echo "Counting collection '$COLLECTION'"
$SUDO_CMD "$PYTHON" - <<PY
from app.rag.ingest import get_chroma_client
client = get_chroma_client()
col = client.get_collection("$COLLECTION")
print(col.count())
PY
