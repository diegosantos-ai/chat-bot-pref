"""
Configuração de logging estruturado (JSON) para a {bot_name}.

Este módulo centraliza a configuração de logs:
- Formato JSON simples, seguro para ingestão por agregadores.
- Nível configurável via settings.

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
    """Formatter básico que serializa o registro em JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Campos extras conhecidos
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        if record.stack_info:
            payload["stack"] = self.formatStack(record.stack_info)

        # Extras arbitrários adicionados via logger.exception(..., extra={...})
        for key, value in record.__dict__.items():
            if key.startswith("_"):
                continue
            if key in payload:
                continue
            # ignora campos padrão do LogRecord
            if key in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
            }:
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

