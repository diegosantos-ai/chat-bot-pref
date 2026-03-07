import asyncio
import os
import argparse
import re
import asyncpg
from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
VIEWS_PATH = os.path.join(ROOT, 'analytics', 'v1', 'views.sql')

# Adiciona raiz ao sys.path se necessário
if ROOT not in sys.path:  # noqa: F821
    sys.path.append(ROOT)  # noqa: F821

# Garante carregamento do .env da raiz
load_dotenv(os.path.join(ROOT, '.env'))

# Simplistic split by semicolon at end of line/statement
_SQL_SPLIT = re.compile(r";\s*(?=\n|$)")

def split_sql_statements(sql: str) -> list[str]:
    lines = []
    for line in sql.replace('\r\n', '\n').replace('\r', '\n').split('\n'):
        # simple comment removal
        if line.strip().startswith('--'):
            continue
        lines.append(line)
    cleaned = '\n'.join(lines)
    parts = [p.strip() for p in _SQL_SPLIT.split(cleaned) if p.strip()]
    return parts

async def apply_views(dsn: str) -> None:
    print(f"Connecting to {dsn}...")
    conn = await asyncpg.connect(dsn=dsn)
    try:
        with open(VIEWS_PATH, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        stmts = split_sql_statements(sql)
        count = 0
        for stmt in stmts:
            print(f"Executing statement {count+1}...")
            # print(stmt[:100] + "...") 
            await conn.execute(stmt)
            count += 1
        print(f"[ok] Views applied — {count} statements executed successfully.")
    except Exception as e:
        print(f"[error] Failed to apply views: {e}")
    finally:
        await conn.close()

async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--database-url', dest='database_url', default=None, help='DSN do PostgreSQL')
    args = parser.parse_args()

    load_dotenv(os.path.join(ROOT, '.env'))
    dsn = args.database_url or os.environ.get('DATABASE_URL')
    if not dsn:
        # Fallback default from settings.py if not in env
        dsn = "postgresql://localhost:5432/pilot_atendimento"
        print(f'[info] DATABASE_URL not found, using default: {dsn}')
        
    await apply_views(dsn)
    return 0

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
