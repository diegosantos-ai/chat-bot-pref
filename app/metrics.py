"""
Cliente StatsD/DogStatsD opcional para métricas rápidas.

Sem dependências externas: usa UDP simples. Ativado por env:
- METRICS_STATSD_ENABLED=true
- METRICS_STATSD_HOST=localhost
- METRICS_STATSD_PORT=8125
- METRICS_STATSD_PREFIX=terezia
"""

from __future__ import annotations

import socket
from typing import Optional

from app.settings import settings


class _NoopStatsd:
    def incr(self, *_args, **_kwargs) -> None:
        return

    def timing(self, *_args, **_kwargs) -> None:
        return


class StatsdClient:
    def __init__(self, host: str, port: int, prefix: str = ""):
        self.addr = (host, port)
        self.prefix = prefix.rstrip(".")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def _metric(self, name: str) -> str:
        if self.prefix:
            return f"{self.prefix}.{name}"
        return name

    def incr(self, name: str, value: int = 1, sample_rate: float = 1.0) -> None:
        metric = self._metric(name)
        parts = [f"{metric}:{value}|c"]
        if sample_rate != 1.0:
            parts.append(f"|@{sample_rate}")
        self.sock.sendto("".join(parts).encode("utf-8"), self.addr)

    def timing(self, name: str, ms: float) -> None:
        metric = self._metric(name)
        payload = f"{metric}:{ms:.2f}|ms"
        self.sock.sendto(payload.encode("utf-8"), self.addr)


def get_statsd_client() -> Optional[StatsdClient]:
    if not settings.METRICS_STATSD_ENABLED:
        return None
    try:
        return StatsdClient(
            host=settings.METRICS_STATSD_HOST,
            port=settings.METRICS_STATSD_PORT,
            prefix=settings.METRICS_STATSD_PREFIX,
        )
    except Exception:
        return None


statsd = get_statsd_client() or _NoopStatsd()

