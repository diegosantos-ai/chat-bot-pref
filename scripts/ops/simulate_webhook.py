import asyncio
import hmac
import hashlib
import json
import os
import sys
from datetime import datetime

# Ajuste de path e ambiente
from pathlib import Path
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    import httpx
    from dotenv import load_dotenv
except ImportError:
    print("Erro: Instale httpx e python-dotenv (pip install httpx python-dotenv)")
    sys.exit(1)

# Carrega ambiente
load_dotenv(ROOT_DIR / ".env")

APP_SECRET = os.getenv("META_APP_SECRET", "test_secret")
APP_HOST = os.getenv("APP_HOST", "localhost")
APP_PORT = os.getenv("APP_PORT", "8000")
BASE_URL = f"http://{APP_HOST}:{APP_PORT}/webhook/meta"

def generate_signature(payload_bytes: bytes) -> str:
    """Gera assinatura X-Hub-Signature-256"""
    signature = hmac.new(
        key=APP_SECRET.encode('utf-8'),
        msg=payload_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"

async def simulate_event(scenario_name: str, payload: dict):
    print(f"\n--- Simulando: {scenario_name} ---")
    
    payload_json = json.dumps(payload)
    payload_bytes = payload_json.encode('utf-8')
    signature = generate_signature(payload_bytes)
    
    headers = {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": signature
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(BASE_URL, content=payload_bytes, headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Resposta: {response.text}")
            
            if response.status_code == 200:
                print("✅ Sucesso!")
            else:
                print("❌ Falha!")
                
        except Exception as e:
            print(f"Erro de conexão: {e}")
            print("Certifique-se que o servidor está rodando (uvicorn app.main:app)")

async def main():
    # 1. Simulação: Mensagem de Texto (Messenger)
    msg_event = {
        "object": "page",
        "entry": [{
            "id": "123456789",
            "time": int(datetime.now().timestamp() * 1000),
            "messaging": [{
                "sender": {"id": "user_123"},
                "recipient": {"id": "page_123"},
                "timestamp": int(datetime.now().timestamp() * 1000),
                "message": {
                    "mid": "mid.123456",
                    "text": "Qual o horário de funcionamento da prefeitura?"
                }
            }]
        }]
    }
    
    # 2. Simulação: Comentário Público (Instagram/Facebook)
    comment_event = {
        "object": "instagram",
        "entry": [{
            "id": "insta_123",
            "time": int(datetime.now().timestamp()),
            "changes": [{
                "field": "comments",
                "value": {
                    "id": "comment_999",
                    "text": "Ótimo serviço!",
                    "message": "Ótimo serviço! Parabéns.", # Variação dependendo da API
                    "from": {"id": "user_456", "username": "cidadao_exemplar"},
                    "item": "comment",
                    "post_id": "post_777",
                    "comment_id": "comment_999",
                    "created_time": int(datetime.now().timestamp())
                }
            }]
        }]
    }

    await simulate_event("Mensagem Messenger (Dúvida)", msg_event)
    await simulate_event("Comentário Instagram (Elogio)", comment_event)

if __name__ == "__main__":
    asyncio.run(main())
