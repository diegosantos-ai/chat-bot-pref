"""Admin API — RAG ETL, Document Upload & Job History."""
import os
import asyncio
import subprocess
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from fastapi.responses import JSONResponse
from api import get_conn

router = APIRouter(prefix="/api/admin/rag", tags=["RAG"])

UPLOAD_BASE = Path("uploads")
ETL_SCRIPT  = Path(__file__).parent.parent.parent / "scripts" / "rag_etl_job.py"

# In-memory ETL state (per process — fine for MVP, single-instance)
_etl_state: dict = {}  # tenant_id → {"status": ..., "log": [...]}


def _get_or_init(tenant_id: str) -> dict:
    if tenant_id not in _etl_state:
        _etl_state[tenant_id] = {"status": "IDLE", "log": []}
    return _etl_state[tenant_id]


@router.get("/status")
async def etl_status(tenant_id: str = "all"):
    return _get_or_init(tenant_id)


@router.post("/trigger")
async def trigger_etl(tenant_id: str = "all"):
    state = _get_or_init(tenant_id)
    if state["status"] == "RUNNING":
        return {"ok": False, "message": "ETL já em execução para este tenant"}

    state["status"] = "RUNNING"
    state["log"]    = ["[INFO] Iniciando ETL..."]

    async def run():
        try:
            script = str(ETL_SCRIPT) if ETL_SCRIPT.exists() else None
            if script:
                args = ["python", script]
                if tenant_id != "all":
                    args += ["--tenant", tenant_id]
                proc = await asyncio.create_subprocess_exec(
                    *args,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                )
                async for line in proc.stdout:
                    state["log"].append(line.decode().rstrip())
                await proc.wait()
                state["status"] = "DONE" if proc.returncode == 0 else "ERROR"
            else:
                # Log dummy job and persist to rag_job_log
                await asyncio.sleep(2)
                state["log"].append("[INFO] Script ETL não encontrado — simulando execução")
                state["log"].append("[DONE] ETL concluído sem erros (modo demo)")
                state["status"] = "DONE"

            # Persist to rag_job_log
            conn = await get_conn()
            try:
                await conn.execute(
                    """INSERT INTO rag_job_log (tenant_id, status, log_output)
                       VALUES ($1, $2, $3)""",
                    tenant_id, state["status"], "\n".join(state["log"]),
                )
            except Exception:
                pass  # Table may not exist yet
            finally:
                await conn.close()

        except Exception as e:
            state["log"].append(f"[ERROR] {e}")
            state["status"] = "ERROR"

    asyncio.create_task(run())
    return {"ok": True, "message": "ETL iniciado"}


@router.post("/upload/{tenant_id}")
async def upload_doc(tenant_id: str, file: UploadFile = File(...)):
    allowed = {".pdf", ".txt", ".md", ".docx"}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed:
        raise HTTPException(400, f"Tipo não permitido: {ext}. Use {allowed}")

    dest_dir = UPLOAD_BASE / tenant_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / file.filename

    content = await file.read()
    dest.write_bytes(content)

    return {"ok": True, "filename": file.filename, "size": len(content)}


@router.get("/docs/{tenant_id}")
async def list_docs(tenant_id: str):
    doc_dir = UPLOAD_BASE / tenant_id
    if not doc_dir.exists():
        return {"docs": []}
    docs = [
        {"filename": f.name, "size": f.stat().st_size, "modified": f.stat().st_mtime}
        for f in sorted(doc_dir.iterdir(), key=lambda x: -x.stat().st_mtime)
        if f.is_file()
    ]
    return {"docs": docs}


@router.delete("/docs/{tenant_id}/{filename}")
async def delete_doc(tenant_id: str, filename: str):
    doc = UPLOAD_BASE / tenant_id / filename
    if not doc.exists():
        raise HTTPException(404, "Document not found")
    doc.unlink()
    return {"ok": True}


@router.get("/jobs")
async def list_jobs(
    tenant_id: str = None,
    limit: int = Query(50, le=200),
):
    conn = await get_conn()
    try:
        q = "SELECT * FROM rag_job_log"
        args = []
        if tenant_id:
            q += " WHERE tenant_id = $1"
            args.append(tenant_id)
        q += f" ORDER BY started_at DESC LIMIT {limit}"
        rows = await conn.fetch(q, *args)
        return {"jobs": [dict(r) for r in rows]}
    except Exception as e:
        return {"jobs": [], "warning": str(e)}
    finally:
        await conn.close()
