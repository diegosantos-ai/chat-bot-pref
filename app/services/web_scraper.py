import logging
import requests
from bs4 import BeautifulSoup
from typing import Optional
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class WebScraper:
    BASE_URL = "https://santatereza.pr.gov.br"
    SEARCH_PATH = "/busca/"
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def _extract_search_results(self, soup: BeautifulSoup, fallback_url: str) -> list[str]:
        """Extrai resultados da busca no layout atual do portal."""
        results: list[str] = []

        # Layout oficial atual: div.pesquisa -> div.content -> a -> .panel-heading/.panel-body
        links = soup.select("div.pesquisa div.content > a")
        if not links:
            links = soup.select("div.pesquisa a")

        for link in links:
            title_tag = link.select_one(".panel-heading")
            excerpt_tag = link.select_one(".panel-body")

            title = (
                title_tag.get_text(" ", strip=True)
                if title_tag
                else link.get_text(" ", strip=True)
            )
            excerpt = excerpt_tag.get_text(" ", strip=True) if excerpt_tag else ""

            if not title:
                continue

            href = urljoin(self.BASE_URL, link.get("href") or fallback_url)
            if excerpt:
                results.append(f"**{title}**\n{excerpt}\n([Fonte]({href}))")
            else:
                results.append(f"**{title}**\n([Fonte]({href}))")

            if len(results) >= 3:
                break

        return results

    def search_site(self, query: str) -> Optional[str]:
        """
        Busca no site da prefeitura usando o endpoint oficial de pesquisa.
        """
        normalized_query = (query or "").strip()
        if not normalized_query:
            return None

        search_url = urljoin(self.BASE_URL, self.SEARCH_PATH)
        
        try:
            logger.info("Scraping busca: %s", search_url)
            response = requests.get(
                search_url,
                params={"q": normalized_query},
                headers=self.headers,
                timeout=10,
            )
            
            if response.status_code != 200:
                logger.warning(f"Erro ao acessar site: {response.status_code}")
                return None
                
            soup = BeautifulSoup(response.text, "html.parser")
            results = self._extract_search_results(soup, response.url)
            if results:
                return "\n\n".join(results)
            
            return None

        except Exception as e:
            logger.error(f"Erro no scraping: {e}")
            return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = WebScraper()
    print(scraper.search_site("IPTU 2025"))
