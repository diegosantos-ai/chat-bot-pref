from __future__ import annotations

import logging
from time import perf_counter
from uuid import uuid4

from opentelemetry.trace import Status, StatusCode
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.observability.context import reset_correlation_context, set_correlation_context
from app.observability.logging import log_event
from app.observability.tracing import annotate_current_span, get_tracer


class RequestObservabilityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.tracer = get_tracer(__name__)

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(request.headers.get("X-Request-ID", "")).strip() or str(uuid4())
        request.state.request_id = request_id
        token = set_correlation_context(
            request_id=request_id,
            channel="http",
            method=request.method,
            path=request.url.path,
        )
        started_at = perf_counter()
        try:
            with self.tracer.start_as_current_span("http.request") as span:
                annotate_current_span(
                    request_id=request_id,
                    channel="http",
                    method=request.method,
                    path=request.url.path,
                )
                log_event(
                    "http.request.started",
                    method=request.method,
                    path=request.url.path,
                    request_id=request_id,
                )
                try:
                    response = await call_next(request)
                except Exception as exc:
                    span.record_exception(exc)
                    span.set_status(Status(StatusCode.ERROR))
                    annotate_current_span(status_code=500)
                    log_event(
                        "http.request.failed",
                        level=logging.ERROR,
                        request_id=request_id,
                        method=request.method,
                        path=request.url.path,
                        status_code=500,
                        detail=str(exc),
                    )
                    raise

                duration_ms = round((perf_counter() - started_at) * 1000, 2)
                annotate_current_span(status_code=response.status_code, duration_ms=duration_ms)
                response.headers.setdefault("X-Request-ID", request_id)
                log_event(
                    "http.request.completed",
                    request_id=request_id,
                    method=request.method,
                    path=request.url.path,
                    status_code=response.status_code,
                    duration_ms=duration_ms,
                )
                return response
        finally:
            reset_correlation_context(token)
