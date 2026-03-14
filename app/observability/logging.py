from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from opentelemetry import trace

from app.observability.context import get_correlation_context
from app.settings import settings

LOGGER_NAME = "chat_pref"


def _normalize_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [_normalize_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _normalize_value(item) for key, item in value.items()}
    return str(value)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = build_log_payload(record)
        return json.dumps(payload, ensure_ascii=True)


def build_log_payload(record: logging.LogRecord) -> dict[str, Any]:
    correlation = get_correlation_context()
    span = trace.get_current_span()
    span_context = span.get_span_context()
    trace_id = ""
    span_id = ""
    if span_context.is_valid:
        trace_id = f"{span_context.trace_id:032x}"
        span_id = f"{span_context.span_id:016x}"

    structured_fields = getattr(record, "structured_fields", {})
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": record.levelname,
        "logger": record.name,
        "event_name": structured_fields.get("event_name", record.getMessage()),
        "request_id": structured_fields.get("request_id", correlation.request_id),
        "tenant_id": structured_fields.get("tenant_id", correlation.tenant_id),
        "session_id": structured_fields.get("session_id", correlation.session_id),
        "channel": structured_fields.get("channel", correlation.channel),
        "method": structured_fields.get("method", correlation.method),
        "path": structured_fields.get("path", correlation.path),
        "trace_id": trace_id,
        "span_id": span_id,
    }

    for key, value in structured_fields.items():
        if key not in payload:
            payload[key] = _normalize_value(value)

    return payload


def _append_log_file(payload: dict[str, Any]) -> None:
    tenant_id = str(payload.get("tenant_id", "")).strip() or "system"
    request_id = str(payload.get("request_id", "")).strip() or "orphan"
    logs_dir = Path(settings.DATA_DIR) / "logs" / tenant_id
    logs_dir.mkdir(parents=True, exist_ok=True)
    file_path = logs_dir / f"{request_id}.jsonl"
    with file_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True))
        handle.write("\n")


def configure_structured_logging() -> None:
    logger = logging.getLogger(LOGGER_NAME)
    if getattr(logger, "_chat_pref_configured", False):
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger._chat_pref_configured = True  # type: ignore[attr-defined]


def log_event(
    event_name: str,
    *,
    level: int = logging.INFO,
    **fields: Any,
) -> None:
    configure_structured_logging()
    logger = logging.getLogger(LOGGER_NAME)
    structured_fields = {"event_name": event_name}
    structured_fields.update({key: _normalize_value(value) for key, value in fields.items()})
    record = logging.LogRecord(
        name=LOGGER_NAME,
        level=level,
        pathname=__file__,
        lineno=0,
        msg=event_name,
        args=(),
        exc_info=None,
    )
    record.structured_fields = structured_fields
    _append_log_file(build_log_payload(record))
    logger.log(level, event_name, extra={"structured_fields": structured_fields})
