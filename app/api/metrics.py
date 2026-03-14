from fastapi import APIRouter, Response

from app.observability.metrics import render_metrics

router = APIRouter(tags=["Observability"])


@router.get("/metrics")
async def metrics() -> Response:
    body, media_type = render_metrics()
    return Response(content=body, media_type=media_type)
