"""
RAG ETL Job — Nexo Basis Governador SaaS
=========================================
Job agendado de ingestão multi-tenant.

Para cada tenant ativo no banco que tenha uma `rag_base_path` configurada,
executa `ingest_base()` na collection ChromaDB isolada `{tenant_id}_knowledge_base`.

Execução:
    # Manual
    python scripts/rag_etl_job.py

    # Com forçar re-ingestão
    python scripts/rag_etl_job.py --force

    # Apenas um tenant
    python scripts/rag_etl_job.py --tenant prefeitura_nova_esperanca

    # Como cronjob (crontab -e):
    # 0 2 * * * /app/venv/bin/python /app/scripts/rag_etl_job.py >> /var/log/rag_etl.log 2>&1
"""

import asyncio
import argparse
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Garante que o root do projeto está no PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncpg

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("rag_etl_job")


# ──────────────────────────────────────────────────────────────
# Busca de tenants ativos no banco
# ──────────────────────────────────────────────────────────────

async def fetch_active_tenants(pool: asyncpg.Pool, only_tenant: str | None = None) -> list[dict]:
    """
    Retorna lista de tenants ativos que possuem rag_base_path configurada.

    Cada item: {tenant_id, bot_name, rag_base_path}
    """
    base_query = """
        SELECT tenant_id, bot_name, rag_base_path
        FROM tenants
        WHERE is_active = TRUE
          AND rag_base_path IS NOT NULL
          AND rag_base_path <> ''
    """
    if only_tenant:
        rows = await pool.fetch(base_query + " AND tenant_id = $1", only_tenant)
    else:
        rows = await pool.fetch(base_query)

    return [dict(r) for r in rows]


# ──────────────────────────────────────────────────────────────
# Ingestão por tenant
# ──────────────────────────────────────────────────────────────

def run_ingest_for_tenant(tenant_id: str, base_path: str, force: bool) -> dict:
    """
    Executa a ingestão de um tenant na collection isolada `{tenant_id}_knowledge_base`.

    Args:
        tenant_id: ID do tenant.
        base_path: Caminho local da base de conhecimento (pasta com manifest.json).
        force: Se True, re-ingere mesmo sem mudanças de hash.

    Returns:
        dict com stats da ingestão.
    """
    from app.rag.ingest import get_chroma_client, ingest_document, load_manifest
    from app.rag.embeddings import get_collection_name, resolve_embedding_model, get_embedding_function
    from app.settings import settings

    collection_name = f"{tenant_id}_knowledge_base"
    provider = settings.EMBEDDING_PROVIDER

    logger.info("[%s] Iniciando ingestão → collection: %s", tenant_id, collection_name)

    base = Path(base_path)
    if not base.exists():
        logger.error("[%s] Base não encontrada: %s", tenant_id, base)
        return {"tenant_id": tenant_id, "error": "base_path not found", "chunks": 0}

    try:
        manifest = load_manifest(base)
    except FileNotFoundError as e:
        logger.error("[%s] %s", tenant_id, e)
        return {"tenant_id": tenant_id, "error": str(e), "chunks": 0}

    client = get_chroma_client()
    embedding_fn = get_embedding_function(provider)
    collection_kwargs = {
        "name": collection_name,
        "metadata": {
            "tenant_id": tenant_id,
            "hnsw:space": "cosine",
            "embedding_provider": provider,
        },
    }
    if embedding_fn:
        collection_kwargs["embedding_function"] = embedding_fn

    client.get_or_create_collection(**collection_kwargs)

    items_path = base / "items"
    documents = manifest.get("documents") or manifest.get("items", [])
    total_chunks = 0

    for doc_info in documents:
        doc_file = items_path / doc_info["file"]
        chunks = ingest_document(
            file_path=doc_file,
            doc_id=doc_info["id"],
            title=doc_info["title"],
            tags=doc_info.get("tags", []),
            collection_name=collection_name,
            force=force,
            embedding_provider=provider,
        )
        total_chunks += chunks

    logger.info("[%s] ✅ %d chunks ingeridos/atualizados", tenant_id, total_chunks)
    return {"tenant_id": tenant_id, "collection": collection_name, "chunks": total_chunks}


# ──────────────────────────────────────────────────────────────
# Orquestrador principal
# ──────────────────────────────────────────────────────────────

async def run_etl(force: bool = False, only_tenant: str | None = None) -> None:
    """Job principal: itera sobre tenants ativos e executa ingestão."""
    from app.settings import settings

    logger.info("=" * 60)
    logger.info("RAG ETL Job  —  %s", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"))
    logger.info("Modo: %s | Tenant: %s", "FORCE" if force else "INCREMENTAL", only_tenant or "TODOS")
    logger.info("=" * 60)

    pool = await asyncpg.create_pool(
        dsn=settings.DATABASE_URL,
        min_size=1,
        max_size=5,
    )

    try:
        tenants = await fetch_active_tenants(pool, only_tenant=only_tenant)

        if not tenants:
            logger.warning("Nenhum tenant ativo com rag_base_path encontrado.")
            return

        logger.info("Tenants a processar: %d", len(tenants))
        results = []

        for tenant in tenants:
            tid = tenant["tenant_id"]
            base_path = tenant["rag_base_path"]
            bot_name = tenant["bot_name"]

            logger.info("─" * 50)
            logger.info("Tenant: %s (%s)", bot_name, tid)
            logger.info("Base:   %s", base_path)

            result = run_ingest_for_tenant(tid, base_path, force=force)
            results.append(result)

        # Resumo final
        logger.info("=" * 60)
        logger.info("RESUMO FINAL")
        logger.info("=" * 60)
        total = sum(r.get("chunks", 0) for r in results)
        errors = [r for r in results if "error" in r]
        logger.info("Tenants processados: %d", len(results))
        logger.info("Erros:              %d", len(errors))
        logger.info("Chunks totais:      %d", total)
        if errors:
            for e in errors:
                logger.error("  ❌ %s: %s", e["tenant_id"], e["error"])

    finally:
        await pool.close()


# ──────────────────────────────────────────────────────────────
# Entrypoint CLI
# ──────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="RAG ETL Job — ingere bases de conhecimento de todos os tenants ativos."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reprocessa todos os documentos mesmo sem mudanças de hash.",
    )
    parser.add_argument(
        "--tenant",
        metavar="TENANT_ID",
        default=None,
        help="Processa apenas um tenant específico.",
    )
    args = parser.parse_args()

    asyncio.run(run_etl(force=args.force, only_tenant=args.tenant))


if __name__ == "__main__":
    main()
