from fastapi import APIRouter

from app.settings import settings

router = APIRouter(tags=["Health"])


@router.get("/")
async def root() -> dict[str, str]:
    return {
        "message": "Chat Pref API ativa.",
        "env": settings.ENV,
        "version": settings.VERSION,
        "docs": "/docs",
    }


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy"}
