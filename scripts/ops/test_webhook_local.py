
import os
import sys
from pathlib import Path
import hmac
import hashlib
import json
import httpx
import asyncio
from dotenv import load_dotenv

# Ajuste de path e ambiente
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Carrega variáveis
load_dotenv(ROOT_DIR / ".env")

APP_SECRET = os.getenv("META_APP_SECRET")
VERIFY_TOKEN = os.getenv("META_WEBHOOK_VERIFY_TOKEN")
PAGE_ID = os.getenv("META_PAGE_ID")
APP_HOST = os.getenv("APP_HOST", "localhost")
APP_PORT = os.getenv("APP_PORT", "8000")
API_URL = f"http://{APP_HOST}:{APP_PORT}/webhook/meta"

def generate_signature(payload_body):
    """Gera a assinatura X-Hub-Signature-256"""
    return "sha256=" + hmac.new(
        key=APP_SECRET.encode('utf-8'),
        msg=payload_body,
        digestmod=hashlib.sha256
    ).hexdigest()

async def test_webhook_post():
    print(f"🚀 Testando Webhook POST em {API_URL}...")
    
    # Payload simulando uma mensagem de texto "Olá"
    payload = {
        "object": "page",
        "entry": [
            {
                "id": PAGE_ID,
                "time": 1705244400000,
                "messaging": [
                    {
                        "sender": {"id": "123456789"},  # Fake User ID
                        "recipient": {"id": PAGE_ID},
                        "timestamp": 1705244400000,
                        "message": {
                            "mid": "mid.123456789:abcde",
                            "text": "Olá TerezIA, isso é um teste local!"
                        }
                    }
                ]
            }
        ]
    }
    
    body = json.dumps(payload).encode('utf-8')
    signature = generate_signature(body)
    
    headers = {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": signature
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(API_URL, content=body, headers=headers)
            
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Webhook aceitou a mensagem com sucesso!")
        else:
            print("❌ Webhook rejeitou a mensagem.")

    except Exception as e:
        print(f"❌ Erro de conexão (O servidor está rodando?): {str(e)}")

if __name__ == "__main__":
    if not APP_SECRET:
        print("❌ META_APP_SECRET não encontrado no .env")
        exit(1)
        
    asyncio.run(test_webhook_post())
