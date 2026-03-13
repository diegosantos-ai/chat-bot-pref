"""
Backup PostgreSQL (sem depender de psql/pg_dump)
===============================================

Gera um backup lógico em CSV (COPY) para todas as tabelas do schema public e
salva metadados (counts, tamanho, timestamp).

Uso:
  python scripts/backup_postgres.py
  python scripts/backup_postgres.py --out-dir artifacts/backups/postgres --gzip --verify
"""

from __future__ import annotations

import argparse
import asyncio
import gzip
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO

import asyncpg
from dotenv import load_dotenv


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _quote_ident(ident: str) -> str:
    return '"' + ident.replace('"', '""') + '"'


@dataclass
class TableBackupResult:
    table: str
    rows: int
    file: str
    bytes_written: int


async def _list_public_tables(conn: asyncpg.Connection) -> list[str]:
    rows = await conn.fetch(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema='public' AND table_type='BASE TABLE'
        ORDER BY table_name
        """
    )
    return [r["table_name"] for r in rows]


async def _row_count(conn: asyncpg.Connection, table: str) -> int:
    q = f"SELECT COUNT(*) FROM {_quote_ident(table)}"
    return int(await conn.fetchval(q))


def _open_output(path: Path, gzip_enabled: bool) -> BinaryIO:
    path.parent.mkdir(parents=True, exist_ok=True)
    if gzip_enabled:
        return gzip.open(path, "wb")
    return open(path, "wb")


async def _backup_table(
    conn: asyncpg.Connection,
    table: str,
    out_path: Path,
    gzip_enabled: bool,
) -> TableBackupResult:
    rows = await _row_count(conn, table)
    query = f"SELECT * FROM {_quote_ident(table)}"

    with _open_output(out_path, gzip_enabled) as f:
        await conn.copy_from_query(
            query,
            output=f,
            format="csv",
            header=True,
        )

    bytes_written = out_path.stat().st_size
    return TableBackupResult(
        table=table,
        rows=rows,
        file=str(out_path),
        bytes_written=bytes_written,
    )


async def _verify_counts(
    conn: asyncpg.Connection,
    results: list[TableBackupResult],
) -> tuple[bool, list[str]]:
    problems: list[str] = []
    for r in results:
        live = await _row_count(conn, r.table)
        if live != r.rows:
            problems.append(f"{r.table}: live={live} backup={r.rows}")
    return (len(problems) == 0), problems


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="artifacts/backups/postgres", help="Diretório base de saída")
    parser.add_argument("--gzip", action="store_true", help="Compactar CSVs com gzip (.csv.gz)")
    parser.add_argument("--verify", action="store_true", help="Reconta tabelas e compara com o backup")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    load_dotenv(root / ".env")
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        raise SystemExit("DATABASE_URL não definido no ambiente/.env")

    out_base = Path(args.out_dir)
    stamp = _utc_stamp()
    out_dir = out_base / stamp
    out_dir.mkdir(parents=True, exist_ok=True)

    conn = await asyncpg.connect(dsn=dsn)
    try:
        db_info = await conn.fetchrow("SELECT current_database() AS db, current_user AS usr")
        pg_ver = await conn.fetchval("SHOW server_version")
        pgcrypto = await conn.fetchval("SELECT exists(select 1 from pg_extension where extname='pgcrypto')")

        tables = await _list_public_tables(conn)
        if not tables:
            raise SystemExit("Nenhuma tabela encontrada no schema public.")

        results: list[TableBackupResult] = []
        for t in tables:
            suffix = ".csv.gz" if args.gzip else ".csv"
            out_path = out_dir / f"{t}{suffix}"
            res = await _backup_table(conn, t, out_path, args.gzip)
            results.append(res)

        meta = {
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "database": str(db_info["db"]),
            "user": str(db_info["usr"]),
            "postgres_version": str(pg_ver),
            "pgcrypto_installed": bool(pgcrypto),
            "tables": [
                {
                    "name": r.table,
                    "rows": r.rows,
                    "file": Path(r.file).name,
                    "bytes": r.bytes_written,
                }
                for r in results
            ],
        }
        (out_dir / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

        if args.verify:
            ok, problems = await _verify_counts(conn, results)
            (out_dir / "verify.txt").write_text(
                "OK\n" if ok else "FAIL\n" + "\n".join(problems) + "\n",
                encoding="utf-8",
            )
            if not ok:
                print("VERIFY_FAIL")
                for p in problems:
                    print("-", p)
                return 2

        print(f"Backup OK: {out_dir}")
        print(f"Tabelas: {len(results)}")
        return 0
    finally:
        await conn.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
