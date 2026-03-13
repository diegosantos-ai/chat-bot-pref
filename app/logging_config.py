"""
Configuração de logging estruturado (JSON) — Nexo Basis Governador SaaS
=========================================================================
Formato JSON com `tenant_id` injetado automaticamente via contextvars.
Compativel com Loki/Grafana para dashboards filtrados por tenant.

Uso:
    from app.logging_config import configure_logging
    configure_logging()
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict

from app.settings import settings


class JsonFormatter(logging.Formatter):
    """Formata logs como JSON estruturado com tenant_id injetado automaticamente."""

    # Campos internos do LogRecord que nunca devem aparecer no JSON
    _SKIP = {
        "name", "msg", "args", "levelname", "levelno",
        "pathname", "filename", "module", "exc_info", "exc_text",
        "stack_info", "lineno", "funcName", "created", "msecs",
        "relativeCreated", "thread", "threadName", "processName", "process",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level":     record.levelname,
            "logger":    record.name,
            "message":   record.getMessage(),
        }

        # ── tenant_id via contextvars (9.1) ──────────────────────────────────
        try:
            from app import tenant_context
            tid = tenant_context.get_tenant()
            if tid:
                payload["tenant_id"] = tid
        except Exception:
            pass  # nunca deve quebrar o logger
        # ─────────────────────────────────────────────────────────────────────

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        if record.stack_info:
            payload["stack"] = self.formatStack(record.stack_info)

        for key, value in record.__dict__.items():
            if key.startswith("_") or key in payload or key in self._SKIP:
                continue
            try:
                json.dumps(value)
                payload[key] = value
            except Exception:
                payload[key] = str(value)

        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> None:
    """Configura logging global com formato JSON."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    handlers = [logging.StreamHandler(sys.stdout)]
    formatter: logging.Formatter
    if settings.LOG_JSON:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s [%(name)s] %(message)s",
            "%Y-%m-%dT%H:%M:%S%z",
        )
    for h in handlers:
        h.setFormatter(formatter)

    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        force=True,  # sobrescreve configs prévias do uvicorn
    )

