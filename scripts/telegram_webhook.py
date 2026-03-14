#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

import httpx


def _api_url(bot_token: str, method: str, base_url: str) -> str:
    return f"{base_url.rstrip('/')}/bot{bot_token}/{method}"


def _request(bot_token: str, method: str, payload: dict[str, Any], base_url: str) -> dict[str, Any]:
    response = httpx.post(_api_url(bot_token, method, base_url), json=payload, timeout=20.0)
    response.raise_for_status()
    body = response.json()
    if not body.get("ok"):
        raise RuntimeError(str(body.get("description", "Telegram retornou erro.")))
    return body


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Utilitario para configurar o webhook do Telegram.")
    parser.add_argument("action", choices=["me", "set", "info", "delete"])
    parser.add_argument("--bot-token", default=os.getenv("TELEGRAM_BOT_TOKEN", ""))
    parser.add_argument("--base-url", default=os.getenv("TELEGRAM_API_BASE_URL", "https://api.telegram.org"))
    parser.add_argument("--webhook-url", default="")
    parser.add_argument("--secret-token", default=os.getenv("TELEGRAM_WEBHOOK_SECRET", ""))
    parser.add_argument("--drop-pending-updates", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    bot_token = args.bot_token.strip()
    if not bot_token:
        print("TELEGRAM_BOT_TOKEN obrigatorio.", file=sys.stderr)
        return 1

    if args.action == "me":
        payload: dict[str, Any] = {}
        result = _request(bot_token, "getMe", payload, args.base_url)
    elif args.action == "info":
        payload = {}
        result = _request(bot_token, "getWebhookInfo", payload, args.base_url)
    elif args.action == "delete":
        payload = {"drop_pending_updates": args.drop_pending_updates}
        result = _request(bot_token, "deleteWebhook", payload, args.base_url)
    else:
        webhook_url = args.webhook_url.strip()
        if not webhook_url:
            print("--webhook-url obrigatorio para action=set.", file=sys.stderr)
            return 1
        payload = {
            "url": webhook_url,
            "drop_pending_updates": args.drop_pending_updates,
        }
        if args.secret_token.strip():
            payload["secret_token"] = args.secret_token.strip()
        result = _request(bot_token, "setWebhook", payload, args.base_url)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
