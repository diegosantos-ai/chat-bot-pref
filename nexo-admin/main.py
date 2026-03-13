"""
Nexo Admin — Standalone FastAPI application
Superadmin interface for managing tenants, contracts, RAG, jobs and system health.
Port: 8093:8000
Auth: X-Admin-Key header (set via ADMIN_API_KEY env var)
"""
import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from api.tenants import router as tenants_router
from api.contracts import router as contracts_router
from api.credentials import router as credentials_router
from api.rag import router as rag_router
from api.logs import router as logs_router
from api.health import router as health_router


# ---------- Settings ----------------------------------------------------------
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "nexo-admin-changeme")
DEBUG         = os.getenv("DEBUG", "false").lower() == "true"

# ---------- Lifespan ----------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield  # nothing to init for MVP

# ---------- App ---------------------------------------------------------------
app = FastAPI(
    title="Nexo Admin API",
    version="1.0.0",
    description="Superadmin interface for the Nexo Prefa SaaS platform",
    docs_url="/docs" if DEBUG else None,
    redoc_url=None,
    lifespan=lifespan,
)

# ---------- CORS --------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if DEBUG else [os.getenv("ADMIN_ORIGIN", "*")],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ---------- Auth Guard Middleware ---------------------------------------------
OPEN_PATHS = {"/", "/health", "/docs", "/openapi.json"}

@app.middleware("http")
async def admin_key_guard(request: Request, call_next):
    path = request.url.path
    # Pass through: static files, root, health check
    if (
        path.startswith("/static")
        or path in OPEN_PATHS
        or request.method == "OPTIONS"
        or DEBUG
    ):
        return await call_next(request)

    # Protect all /api/* routes
    if path.startswith("/api/"):
        key = request.headers.get("X-Admin-Key", "")
        if key != ADMIN_API_KEY:
            return JSONResponse({"detail": "Unauthorized — invalid admin key"}, status_code=401)

    return await call_next(request)


# ---------- Security Headers --------------------------------------------------
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "script-src 'self' 'unsafe-inline'; "
        "connect-src 'self'"
    )
    return response


# ---------- Routers -----------------------------------------------------------
app.include_router(tenants_router)
app.include_router(contracts_router)
app.include_router(credentials_router)
app.include_router(rag_router)
app.include_router(logs_router)
app.include_router(health_router)


# ---------- Health (open) -----------------------------------------------------
@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok", "service": "nexo-admin"}


# ---------- Static Files & SPA ------------------------------------------------
_static_dir = Path(__file__).parent / "static"
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

# Serve SPA shell for all non-API routes
@app.get("/{full_path:path}", include_in_schema=False)
async def spa_shell(full_path: str):
    index = _static_dir / "index.html"
    if index.exists():
        from fastapi.responses import FileResponse
        return FileResponse(str(index))
    return JSONResponse({"detail": "Admin UI not found"}, 404)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=DEBUG)
