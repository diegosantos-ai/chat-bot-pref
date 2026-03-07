import asyncio
import os
import argparse
import re
from urllib.parse import urlparse, urlunparse

import asyncpg
from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
SCHEMA_PATH = os.path.join(ROOT, 'db', 'schema.sql')

# Adiciona raiz ao sys.path se necessário
if ROOT not in sys.path:  # noqa: F821
    sys.path.append(ROOT)  # noqa: F821

# Garante carregamento do .env da raiz
load_dotenv(os.path.join(ROOT, '.env'))

_SQL_SPLIT = re.compile(r";\s*(?=\n|$)")


def dsn_with_db(dsn: str, dbname: str) -> str:
    p = urlparse(dsn)
    new_path = f"/{dbname}"
    return urlunparse((p.scheme, p.netloc, new_path, '', '', ''))


def split_sql_statements(sql: str) -> list[str]:
    # remove comentários de linha e normaliza
    lines = []
    for line in sql.replace('\r\n', '\n').replace('\r', '\n').split('\n'):
        if line.strip().startswith('--'):
            continue
        lines.append(line)
    cleaned = '\n'.join(lines)
    parts = [p.strip() for p in _SQL_SPLIT.split(cleaned) if p.strip()]
    return parts


async def try_ensure_database(dsn: str, target_db: str) -> None:
    """Tenta criar o database conectando-se ao DB 'postgres'. Ignora erro se sem permissão."""
    try:
        admin_dsn = dsn_with_db(dsn, 'postgres')
        conn = await asyncpg.connect(dsn=admin_dsn)
    except Exception as e:
        print(f"[warn] Não foi possível conectar ao DB 'postgres' para criar '{target_db}': {e}")
        return
    try:
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", target_db)
        if not exists:
            # usa SQL simples — requer permissão de criação
            await conn.execute(f'CREATE DATABASE "{target_db}"')
            print(f"[ok] Database '{target_db}' criado")
        else:
            print(f"[ok] Database '{target_db}' já existe")
    except Exception as e:
        print(f"[warn] Não foi possível criar o database '{target_db}': {e}")
    finally:
        await conn.close()


async def apply_schema_and_list(dsn: str, target_db: str) -> None:
    db_dsn = dsn_with_db(dsn, target_db)
    conn = await asyncpg.connect(dsn=db_dsn)
    try:
        # Extensão pgcrypto
        try:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
            print("[ok] Extensão pgcrypto verificada/criada")
        except Exception as e:
            print(f"[warn] Não foi possível criar extensão pgcrypto: {e}")

        # Executa schema em statements separados
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            sql = f.read()
        stmts = split_sql_statements(sql)
        count = 0
        for stmt in stmts:
            await conn.execute(stmt)
            count += 1
        print(f"[ok] Schema aplicado — {count} statements")

        # Lista tabelas
        rows = await conn.fetch("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema='public' ORDER BY table_name
        """)
        print("Tabelas no schema public:")
        for r in rows:
            print(" -", r['table_name'])
    finally:
        await conn.close()


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--database-url', dest='database_url', default=None, help='DSN do PostgreSQL')
    args = parser.parse_args()

    load_dotenv(os.path.join(ROOT, '.env'))
    dsn = args.database_url or os.environ.get('DATABASE_URL')
    if not dsn:
        print('[erro] DATABASE_URL não definido. Use --database-url ou configure no .env')
        return 2

    parsed = urlparse(dsn)
    target_db = (parsed.path.lstrip('/') or 'pilot_atendimento')
    print(f"Usando servidor {parsed.hostname}:{parsed.port} — database '{target_db}'")

    # Tenta criar DB (opcional)
    # await try_ensure_database(dsn, target_db)
    # Aplica schema e lista tabelas
    await apply_schema_and_list(dsn, target_db)
    print('[ok] Concluído.')
    return 0


if __name__ == '__main__':
    asyncio.run(main())
