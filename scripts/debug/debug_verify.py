import httpx
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega var do .env para comparar
load_dotenv(Path(__file__).resolve().parent.parent / '.env')
EXPECTED_TOKEN = os.getenv("META_WEBHOOK_VERIFY_TOKEN")
APP_PORT = os.getenv("APP_PORT", "8000")

async def test_verify():
    url = "https://cristiano-dasyurine-agonizingly.ngrok-free.dev/webhook/meta"
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": EXPECTED_TOKEN,
        "hub.challenge": "CHALLENGE_ACCEPTED"
    }
    
    print(f"Testando URL: {url}")
    print(f"Token esperado (env): {EXPECTED_TOKEN}")
    print(f"Enviando params: {params}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200 and response.text == params["hub.challenge"]:
            print("✅ SUCESSO LOGICO: O endpoint respondeu corretamente!")
        else:
            print("❌ FALHA LOGICA: O endpoint rejeitou ou respondeu errado.")
            
    except Exception as e:
        print(f"❌ ERRO DE CONEXÃO: {e}")
        print(f"Verifique se o servidor uvicorn está rodando na porta {APP_PORT}.")

if __name__ == "__main__":
    asyncio.run(test_verify())
