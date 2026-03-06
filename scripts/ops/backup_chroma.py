"""
Backup ChromaDB (diretório de persistência)
===========================================

O projeto usa ChromaDB como PersistentClient (arquivos em CHROMA_PERSIST_DIR).
Este script gera um zip do diretório e salva metadados.

Uso:
  python scripts/backup_chroma.py
  python scripts/backup_chroma.py --out-dir artifacts/backups/chroma
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.settings import settings


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _zip_dir(src_dir: Path, out_zip: Path) -> tuple[int, int]:
    files = 0
    total_bytes = 0
    out_zip.parent.mkdir(parents=True, exist_ok=True)

    with ZipFile(out_zip, "w", compression=ZIP_DEFLATED, compresslevel=6) as zf:
        for path in src_dir.rglob("*"):
            if path.is_dir():
                continue
            rel = path.relative_to(src_dir)
            zf.write(path, arcname=str(rel))
            files += 1
            total_bytes += path.stat().st_size
    return files, total_bytes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="artifacts/backups/chroma", help="Diretório base de saída")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")

    src_dir = Path(settings.CHROMA_PERSIST_DIR).resolve()
    if not src_dir.exists():
        raise SystemExit(f"Diretório ChromaDB não encontrado: {src_dir}")

    out_base = Path(args.out_dir)
    stamp = _utc_stamp()
    out_dir = out_base / stamp
    out_dir.mkdir(parents=True, exist_ok=True)

    out_zip = out_dir / "chroma_data.zip"
    files, total_bytes = _zip_dir(src_dir, out_zip)

    meta = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "chroma_persist_dir": str(src_dir),
        "files": files,
        "total_bytes": total_bytes,
        "zip_bytes": out_zip.stat().st_size,
        "rag_collection_name": settings.RAG_COLLECTION_NAME,
    }
    (out_dir / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Backup OK: {out_zip}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
