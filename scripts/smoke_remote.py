#!/usr/bin/env python3
"""Smoke minimo para validar um runtime remoto ja publicado."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import httpx


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke minimo para ambiente remoto do Chat Pref.")
    parser.add_argument("--base-url", required=True, help="URL base do ambiente remoto, ex.: http://1.2.3.4:8000")
    parser.add_argument("--tenant-id", default="prefeitura-vila-serena")
    parser.add_argument("--request-id", default="fase13-remote-smoke")
    parser.add_argument(
        "--message",
        default="Qual o horario da sala de vacinacao da UBS?",
    )
    parser.add_argument("--json-out", default="")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    results: dict[str, object] = {
        "base_url": base_url,
        "tenant_id": args.tenant_id,
        "request_id": args.request_id,
    }

    with httpx.Client(base_url=base_url, timeout=30.0) as client:
        root = client.get("/")
        root.raise_for_status()
        results["root"] = root.json()

        health = client.get("/health")
        health.raise_for_status()
        health_payload = health.json()
        ensure(health_payload.get("status") == "healthy", "Healthcheck remoto nao retornou healthy.")
        results["health"] = health_payload

        metrics = client.get("/metrics")
        metrics.raise_for_status()
        metrics_text = metrics.text
        required_metrics = [
            "chatpref_chat_requests_total",
            "chatpref_policy_decisions_total",
            "chatpref_retrieval_total",
            "chatpref_llm_compositions_total",
            "chatpref_llm_compose_latency_seconds",
        ]
        for metric_name in required_metrics:
            ensure(metric_name in metrics_text, f"Metrica ausente em /metrics: {metric_name}")
        results["metrics_checked"] = required_metrics

        response = client.post(
            "/api/chat",
            json={"tenant_id": args.tenant_id, "message": args.message},
            headers={"X-Request-ID": args.request_id},
        )
        response.raise_for_status()
        payload = response.json()
        ensure(payload.get("request_id") == args.request_id, "request_id nao foi preservado na resposta.")
        lowered_message = str(payload.get("message", "")).lower()
        ensure("sala de vacinacao" in lowered_message or "8h as 16h" in lowered_message, "Resposta remota nao trouxe o contexto esperado do tenant demonstrativo.")
        results["chat"] = payload

    if args.json_out:
        output_path = Path(args.json_out)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
