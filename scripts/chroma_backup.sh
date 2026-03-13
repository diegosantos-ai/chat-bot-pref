#!/usr/bin/env bash
set -euo pipefail
# Backup chroma_data directory to artifacts/backups/chroma/<timestamp>.tar.gz
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHROMA_DIR=${1:-$ROOT_DIR/chroma_data}
OUT_DIR=${2:-$ROOT_DIR/artifacts/backups/chroma}

mkdir -p "$OUT_DIR"
TS=$(date +%Y%m%d_%H%M%S)
OUT_FILE="$OUT_DIR/chroma_backup_$TS.tar.gz"

echo "Backing up $CHROMA_DIR -> $OUT_FILE"
tar -czf "$OUT_FILE" -C "$(dirname "$CHROMA_DIR")" "$(basename "$CHROMA_DIR")"
echo "Backup complete: $OUT_FILE"
