"""Shared DB helper for nexo-admin API routers."""
import os
import asyncpg
from contextlib import asynccontextmanager

_DATABASE_URL = os.getenv("DATABASE_URL", "")

@asynccontextmanager
async def get_db():
    """Context manager to provide a DB connection."""
    conn = await asyncpg.connect(_DATABASE_URL)
    try:
        yield conn
    finally:
        await conn.close()

# Alias for backward compatibility if needed, though get_db is expected now
async def get_conn():
    return await asyncpg.connect(_DATABASE_URL)
