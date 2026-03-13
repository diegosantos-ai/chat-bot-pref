import asyncio
import logging
import sys
import os
import re
from dotenv import load_dotenv

# Adiciona o diretório raiz ao PYTHONPATH para os imports funcionarem
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.scraper.service import ScraperService
from google import genai

# Carrega as variáveis do .env
load_dotenv()

# Diminuindo o nível do logger do Playwright
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

def clean_html(raw_html):
    """Limpa tags HTML para reduzir o tamanho do texto."""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, ' ', raw_html)
    return ' '.join(cleantext.split())

async def test_scraper_ai():
    print("\n" + "="*60)
    print("🤖 TESTE DE QA COM SCRAPING E IA (GEMINI)")
    print("="*60)
    
    # URL padrão baseada na notícia mencionada pelo usuário
    default_url = "https://santatereza.pr.gov.br/noticiasView/1883_2o-ENCONTRO-DE-MULHERES-DIA-INTERNACIONAL-DA-MULHER-.html"
    
    url = input(f"Digite a URL da página (ou aperte Enter para usar a padrão):\n[{default_url}]:\n> ").strip()
    if not url:
        url = default_url

    pergunta = input("\nDigite sua pergunta sobre o conteúdo da página:\n(ex: 'quando vai ser o 2º ENCONTRO DE MULHERES?'):\n> ").strip()
    
    if not pergunta:
        print("Nenhuma pergunta digitada. Encerrando o teste.")
        return

    print("\n[+] Inicializando ScraperService...")
    scraper = ScraperService()
    
    try:
        print("[+] Fazendo scraping da página...")
        print("[+] Isso pode levar alguns segundos, aguarde...\n")
        
        result = await scraper.preview_url(url)
        
        if result.get("error"):
            print(f"❌ Erro reportado pelo Scraper: {result.get('error')}")
            return
            
        body_html = result.get('body_html', '')
        texto_limpo = clean_html(body_html)
        
        print("[+] Enviando contexto da página para análise da IA (Gemini)...")
        
        # Obter a Key e Modelo do .env
        api_key = os.getenv("GEMINI_API_KEY")
        model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        
        if not api_key:
            print("❌ ERRO: GEMINI_API_KEY não encontrada no arquivo .env!")
            return
            
        # Iniciar o client do GenAI
        client = genai.Client(api_key=api_key)
        
        # Criar o prompt combinando contexto e pergunta
        contexto_resumido = texto_limpo[:80000] # Limite de segurança
        
        prompt = f"""Você é um assistente útil e preciso. 
Baseado EXCLUSIVAMENTE no texto da página da web a seguir, responda a pergunta do usuário.
Se a resposta não estiver no texto, diga que não encontrou a informação.

--- TEXTO DA PÁGINA ---
Título: {result.get('title', 'Sem título')}
Conteúdo:
{contexto_resumido}
--- FIM DO TEXTO ---

Pergunta do usuário: {pergunta}
"""
        
        response = client.models.generate_content(
            model=model,
            contents=prompt,
        )
        
        print("="*60)
        print("🎯 RESPOSTA DA IA")
        print("="*60)
        print(response.text)
        print("="*60 + "\n")
            
    except Exception as e:
        print(f"❌ Erro durante o teste com IA: {e}")
    finally:
        print("[+] Fechando ambiente de scraping...")
        await scraper.close()
        await asyncio.sleep(0.5)
        print("[+] Teste de IA concluído.")

if __name__ == "__main__":
    try:
        asyncio.run(test_scraper_ai())
    except Exception as e:
        if "TargetClosedError" not in str(e):
            raise
