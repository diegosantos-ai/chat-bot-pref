from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExportResult, SpanExporter

from app.observability.context import get_correlation_context
from app.settings import settings

_TRACING_CONFIGURED = False


def _stringify(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return json.dumps(value, ensure_ascii=True)


class FileSpanExporter(SpanExporter):
    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        for span in spans:
            attributes = {str(key): _stringify(value) for key, value in span.attributes.items()}
            tenant_id = attributes.get("tenant_id", "system") or "system"
            request_id = attributes.get("request_id", "orphan") or "orphan"

            trace_dir = Path(settings.DATA_DIR) / "traces" / tenant_id
            trace_dir.mkdir(parents=True, exist_ok=True)
            file_path = trace_dir / f"{request_id}.jsonl"

            payload = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "name": span.name,
                "trace_id": f"{span.context.trace_id:032x}",
                "span_id": f"{span.context.span_id:016x}",
                "parent_span_id": f"{span.parent.span_id:016x}" if span.parent is not None else "",
                "request_id": request_id,
                "tenant_id": tenant_id,
                "session_id": attributes.get("session_id", ""),
                "channel": attributes.get("channel", ""),
                "status_code": span.status.status_code.name,
                "attributes": attributes,
            }

            with file_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, ensure_ascii=True))
                handle.write("\n")

        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        return None


def configure_tracing() -> None:
    global _TRACING_CONFIGURED
    if _TRACING_CONFIGURED:
        return

    provider = TracerProvider(
        resource=Resource.create(
            {
                "service.name": settings.APP_NAME,
                "service.version": settings.VERSION,
                "deployment.environment": settings.ENV,
            }
        )
    )
    provider.add_span_processor(SimpleSpanProcessor(FileSpanExporter()))
    trace.set_tracer_provider(provider)
    _TRACING_CONFIGURED = True


def get_tracer(name: str):
    configure_tracing()
    return trace.get_tracer(name)


def annotate_current_span(**attributes: object) -> None:
    span = trace.get_current_span()
    if not span.is_recording():
        return

    correlation = get_correlation_context()
    merged_attributes = {
        "request_id": correlation.request_id,
        "tenant_id": correlation.tenant_id,
        "session_id": correlation.session_id,
        "channel": correlation.channel,
        "method": correlation.method,
        "path": correlation.path,
    }
    merged_attributes.update(attributes)

    for key, value in merged_attributes.items():
        if value is None:
            continue
        normalized = _stringify(value)
        if normalized == "":
            continue
        span.set_attribute(key, normalized)
