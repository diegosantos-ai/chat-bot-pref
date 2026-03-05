import asyncio
import logging
import sys
import os
import re
from dotenv import load_dotenv

# Adiciona o diretório raiz ao PYTHONPATH para os imports funcionarem
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.scraper.service import ScraperService

# Carrega as variáveis do .env
load_dotenv()

# Diminuindo o nível do logger do Playwright e outros para focar no output visual do teste
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

def clean_html(raw_html):
    """Limpa tags HTML para facilitar a busca do texto."""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, ' ', raw_html)
    return ' '.join(cleantext.split())

async def test_scraper():
    print("\n" + "="*60)
    print("🤖 TESTE INTERATIVO DE BUSCA NO SCRAPER")
    print("="*60)
    
    termo = input("Digite um termo para buscar na página (ex: INTERNACIONAL): ").strip()
    if not termo:
        print("Nenhum termo digitado. Encerrando o teste.")
        return

    print("\n[+] Inicializando ScraperService...")
    scraper = ScraperService()
    
    try:
        url = os.getenv("FALLBACK_TARGET_URL", "https://santatereza.pr.gov.br/noticias")
        print(f"[+] Fazendo preview da URL alvo: {url}")
        print("[+] Isso pode levar alguns segundos, aguarde...\n")
        
        result = await scraper.preview_url(url)
        
        if result.get("error"):
            print(f"❌ Erro reportado pelo Scraper: {result.get('error')}")
            return
            
        body_html = result.get('body_html', '')
        texto_limpo = clean_html(body_html)
        texto_limpo_lower = texto_limpo.lower()
        termo_lower = termo.lower()
        
        ocorrencias = texto_limpo_lower.count(termo_lower)
        
        print("="*60)
        print("📊 RESULTADO DA BUSCA DE SCRAPING")
        print("="*60)
        print(f"URL Alvo: {url}")
        print(f"Título da página: {result.get('title')}")
        print(f"Termo buscado: '{termo}'")
        
        if ocorrencias > 0:
            print(f"\n✅ SUCESSO! O termo '{termo}' foi encontrado {ocorrencias} vez(es)!")
            
            # Mostra o contexto da primeira ocorrência
            idx = texto_limpo_lower.find(termo_lower)
            inicio = max(0, idx - 60)
            fim = min(len(texto_limpo), idx + len(termo) + 60)
            contexto = texto_limpo[inicio:fim]
            print(f"\nContexto da primeira ocorrência:")
            print(f"\"...{contexto.strip()}...\"")
        else:
            print(f"\n❌ O termo '{termo}' NÃO foi encontrado na página atual.")
            print("Dica: Pode estar em outra página, subpágina, ou carregado dinamicamente via JS após este preview inicial.")
            
        print("="*60 + "\n")
            
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
    finally:
        print("[+] Fechando ScraperService...")
        await scraper.close()
        # Pausa para ajudar a fechar o Chrome/CDP no Windows graciosamente
        await asyncio.sleep(0.5)
        print("[+] Teste concluído com sucesso.")

if __name__ == "__main__":
    try:
        asyncio.run(test_scraper())
    except Exception as e:
        if "TargetClosedError" not in str(e):
            raise
