from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.rag import router as rag_router
from app.api.webhook import router as webhook_router
from app.settings import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Nucleo minimo do Chat Pref para reconstruir a plataforma sobre uma base limpa.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(rag_router)
app.include_router(webhook_router)
