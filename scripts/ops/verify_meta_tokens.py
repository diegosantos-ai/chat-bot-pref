"""
Verifica tokens Meta (Facebook/Instagram)
========================================

Este script valida se as variáveis do `.env` existem e se o token consegue
acessar o Graph API.

Uso:
  python scripts/verify_meta_tokens.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv


def verify_meta_tokens() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    # Ajuste de ambiente
    SCRIPT_DIR = Path(__file__).resolve().parent
    ROOT_DIR = SCRIPT_DIR.parent.parent
    load_dotenv(ROOT_DIR / ".env")

    app_secret = os.getenv("META_APP_SECRET")
    access_token = os.getenv("META_ACCESS_TOKEN")
    page_id = os.getenv("META_PAGE_ID")
    verify_token = os.getenv("META_WEBHOOK_VERIFY_TOKEN")
    api_version = os.getenv("META_API_VERSION", "v19.0")

    missing: list[str] = []
    if not app_secret:
        missing.append("META_APP_SECRET")
    if not access_token:
        missing.append("META_ACCESS_TOKEN")
    if not page_id:
        missing.append("META_PAGE_ID")
    if not verify_token:
        missing.append("META_WEBHOOK_VERIFY_TOKEN")

    print("Iniciando verificacao dos tokens Meta...\n")
    if missing:
        print(f"ERRO: variaveis faltando no .env: {', '.join(missing)}")
        return 2

    print("OK: variaveis encontradas no .env.")

    url_me = f"https://graph.facebook.com/{api_version}/me"
    params = {"access_token": access_token, "fields": "id,name"}

    print(f"Validando token em {url_me} ...")
    with httpx.Client(timeout=15.0) as client:
        resp = client.get(url_me, params=params)

    if resp.status_code != 200:
        print(f"ERRO: falha ao validar token (status={resp.status_code})")
        print(resp.text)
        return 3

    data = resp.json()
    api_id = str(data.get("id"))
    name = data.get("name")
    print(f"OK: token valido. Conectado como: {name} (id={api_id})")

    # Orientação: token pode ser de usuário (me/accounts funciona)
    url_accounts = f"https://graph.facebook.com/{api_version}/me/accounts"
    with httpx.Client(timeout=15.0) as client:
        acc = client.get(url_accounts, params={"access_token": access_token})

    if acc.status_code == 200:
        pages = acc.json().get("data", [])
        if pages:
            print("ATENCAO: META_ACCESS_TOKEN parece ser User Token (me/accounts disponivel).")
            page_ids = [str(p.get("id")) for p in pages if p.get("id")]
            if str(page_id) in page_ids:
                print("OK: META_PAGE_ID aparece em /me/accounts.")
            else:
                print(f"ATENCAO: META_PAGE_ID={page_id} nao aparece em /me/accounts.")
                if len(pages) == 1:
                    print(f"Sugestao: use META_PAGE_ID={pages[0].get('id')} (pagina: {pages[0].get('name')})")
            print("Dica: para enviar mensagens no Messenger, use o Page Access Token (access_token da pagina).")
            return 0

    # Se me/accounts não funciona, assumimos page token.
    if api_id == str(page_id):
        print("OK: META_PAGE_ID confere com o id retornado por /me.")
        return 0

    print(f"ATENCAO: META_PAGE_ID={page_id} difere do id retornado por /me ({api_id}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(verify_meta_tokens())

