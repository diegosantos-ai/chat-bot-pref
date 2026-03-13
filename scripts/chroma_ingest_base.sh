#!/usr/bin/env bash
set -euo pipefail
# Ingest a RAG base into Chroma
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$ROOT_DIR/.venv/bin/python"
BASE_PATH=${1:-base/BA-RAG-PILOTO-2026.01.v1}
FORCE_FLAG=${2:-}

if [ ! -x "$PYTHON" ]; then
  echo "ERROR: python venv not found at $PYTHON" >&2
  exit 1
fi

SUDO_CMD=""
if [ "$(id -un)" != "pilot" ]; then
  SUDO_CMD="sudo -u pilot"
fi

echo "Ingesting base: $BASE_PATH (force=$FORCE_FLAG)"
$SUDO_CMD "$PYTHON" - <<PY
from app.rag.ingest import ingest_base
from pathlib import Path
res = ingest_base(Path('$BASE_PATH'), force=${FORCE_FLAG:+True})
import json
print(json.dumps(res, indent=2, ensure_ascii=False))
PY
