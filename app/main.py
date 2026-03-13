# Reload trigger
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import _rate_limit_exceeded_handler
from app.extensions import limiter as shared_limiter
from slowapi.errors import RateLimitExceeded
from app.settings import settings
from app.logging_config import configure_logging
from app.api.chat import router as chat_router
from app.api.webhook import router as webhook_router
from app.api.analytics import router as analytics_router
from app.api.deploy import router as deploy_router
from app.api.admin import router as admin_router
from app.api.panel import router as panel_router
from app.services.scheduler import scheduler

# Configura logging estruturado
configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    scheduler.start()
    yield
    # Shutdown
    scheduler.shutdown()


# Rate Limiting
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="API multi-tenant de atendimento digital com RAG, auditoria e guardrails.",
    lifespan=lifespan,
)

# Attach limiter and exception handler directly. This is simpler and avoids
# invoking slowapi's `slowapi_startup` which references a global `app` in this
# packaging and can raise at startup.
app.state.limiter = shared_limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configurado para produção (não mais permissivo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Hub-Signature"],
)

# Trusted Host Middleware (proteção contra Host header injection)
# Dominio do cliente é gerido via env var ALLOWED_HOSTS — sem hard-code de pilot
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)


# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    # CSP relaxed to allow Google Fonts for the panel UI
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "script-src 'self' 'unsafe-inline'; "
        "connect-src 'self'"
    )
    if not settings.DEBUG:
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
    return response


# Registra rotas
app.include_router(chat_router)
app.include_router(webhook_router)
app.include_router(analytics_router)
app.include_router(deploy_router)
app.include_router(admin_router)
app.include_router(panel_router)

# Serve panel static files at /panel when present
_panel_dir = Path(__file__).parent.parent / "panel"
if _panel_dir.exists():
    app.mount("/panel", StaticFiles(directory=str(_panel_dir), html=True), name="panel")

# Instrumentação Prometheus
Instrumentator().instrument(app).expose(app)


@app.get("/", tags=["Health"])
@shared_limiter.limit("60/minute")  # Mais permissivo para health check
async def root(request: Request, response: Response):
    return {
        "message": "Chat Pref API esta rodando.",
        "env": settings.ENV,
        "version": settings.VERSION,
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=True
    )
