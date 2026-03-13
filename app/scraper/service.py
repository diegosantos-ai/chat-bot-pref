"""
Serviço de Scraping com Playwright
===================================
Suporta workflow de múltiplos nós para scraping hierárquico.
"""

import logging
from typing import Any, Optional
from urllib.parse import urljoin
from dataclasses import dataclass, field
from playwright.async_api import async_playwright, Browser, ElementHandle

logger = logging.getLogger(__name__)


@dataclass
class FieldConfig:
    """Configuração de um campo a ser extraído."""

    name: str
    selector: str
    field_type: str = "text"  # text, html, attribute, image
    attribute: Optional[str] = None  # para tipo attribute


@dataclass
class PaginationConfig:
    """Configuração de paginação."""

    enabled: bool = False
    type: str = "none"  # none, next_button, page_param, infinite_scroll
    next_button_selector: Optional[str] = None
    page_param_name: str = "pag"  # parametro ?pag=2
    max_pages: int = 5
    stop_when_empty: bool = True  # para quando nao achou mais itens


@dataclass
class NodeConfig:
    """Configuração de um nó do workflow."""

    id: str
    label: str
    url: Optional[str] = None  # URL relativa ou absoluta
    list_selector: Optional[str] = None  # Seletor da lista de itens
    item_selector: Optional[str] = None  # Seletor de cada item
    fields: list[FieldConfig] = field(default_factory=list)
    follow_links: bool = False
    link_selector: Optional[str] = None
    link_base_url: Optional[str] = None  # URL base para resolver links relativos
    next_node_id: Optional[str] = None  # ID do nó seguinte
    pagination: Optional[PaginationConfig] = None


@dataclass
class WorkflowConfig:
    """Configuração completa do workflow."""

    nodes: list[NodeConfig]
    start_node_id: str


@dataclass
class ScrapedItem:
    """Item extraído de uma página."""

    data: dict[str, Any]
    detail_data: Optional[dict[str, Any]] = None  # Dados da página de detalhe


@dataclass
class ScrapResult:
    """Resultado do scraping."""

    success: bool
    items: list[ScrapedItem]
    error: Optional[str] = None
    nodes_executed: list[str] = field(default_factory=list)


class ScraperService:
    """Serviço de scraping com Playwright."""

    def __init__(self):
        self._browser: Optional[Browser] = None
        self._playwright = None

    async def _get_browser(self) -> Browser:
        """Obtém ou cria o browser."""
        if self._browser is None or not self._browser.is_connected():
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
        return self._browser

    async def close(self):
        """Fecha o browser."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def preview_url(
        self,
        url: str,
        list_selector: Optional[str] = None,
        item_selector: Optional[str] = None,
        limit: int = 5,
    ) -> dict[str, Any]:
        """
        Faz preview de uma URL e retorna elementos encontrados.
        Útil para o usuário descobrir os selectors corretos.
        """
        browser = await self._get_browser()
        page = await browser.new_page()

        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)

            result = {
                "url": url,
                "title": await page.title(),
                "html_preview": "",
                "elements": [],
                "selectors_suggestions": {},
                "interactive_html": "",
                "pagination": {},
            }

            # Detectar opções de paginação
            pagination_info = await page.evaluate("""() => {
                const result = {
                    has_pagination: false,
                    suggestions: []
                };

                // Verificar links de próxima página
                const nextLinks = document.querySelectorAll('a');
                const nextPatterns = ['próxima', 'proxima', 'next', '>', '»', '›', '>>', 'pagina', 'page'];
                
                for (const link of nextLinks) {
                    const text = link.textContent?.toLowerCase().trim() || '';
                    const href = link.getAttribute('href');
                    
                    if (nextPatterns.some(p => text.includes(p)) || href?.includes('pag=') || href?.includes('page=') || href?.includes('/page/')) {
                        result.has_pagination = true;
                        result.suggestions.push({
                            type: 'next_button',
                            selector: getSelector(link),
                            text: text.substring(0, 50),
                            href: href
                        });
                        break;
                    }
                }

                // Verificar URLs com parâmetros de paginação
                const url = window.location.href;
                if (url.includes('?pag=') || url.includes('?page=') || url.includes('/page/')) {
                    result.has_pagination = true;
                    const urlObj = new URL(url);
                    result.current_page = urlObj.searchParams.get('pag') || urlObj.searchParams.get('page') || '1';
                    result.page_param = 'pag';
                }

                return result;
            }

            function getSelector(el) {
                if (el.id) return '#' + el.id;
                let path = [];
                while (el && el.nodeType === Node.ELEMENT_NODE && el.tagName !== 'BODY') {
                    let selector = el.tagName.toLowerCase();
                    if (el.className && typeof el.className === 'string') {
                        const classes = el.className.trim().split(/\\s+/).filter(c => c && c.length < 20);
                        if (classes.length > 0 && classes.length < 4) {
                            selector += '.' + classes.join('.');
                        }
                    }
                    const parent = el.parentElement;
                    if (parent) {
                        const siblings = Array.from(parent.children).filter(s => s.tagName === el.tagName);
                        if (siblings.length > 1) {
                            const index = siblings.indexOf(el) + 1;
                            selector += ':nth-child(' + index + ')';
                        }
                    }
                    path.unshift(selector);
                    el = el.parentElement;
                }
                return path.join(' > ');
            }""")
            result["pagination"] = pagination_info

            # Se o usuário forneceu selectors, tenta extrair
            if list_selector and item_selector:
                items = await page.query_selector_all(
                    f"{list_selector} {item_selector}"
                )
                result["items_found"] = len(items)

                if items:
                    first_item = items[0]
                    # Tenta sugerir selectors comuns
                    result["selectors_suggestions"] = await self._suggest_selectors(
                        first_item
                    )

                    # Extrai HTML do primeiro item para preview
                    result["html_preview"] = await first_item.inner_html()

            # também retorna estrutura da página para sugerir selectors
            # Preserva estilos originais
            body_html = await page.evaluate("""() => {
                // Pega todos os links <style> e <link> da página
                const styles = [];
                document.querySelectorAll('style').forEach(el => {
                    styles.push(el.outerHTML);
                });
                document.querySelectorAll('link[rel="stylesheet"]').forEach(el => {
                    styles.push(el.outerHTML);
                });
                
                // Clona o body preservando estrutura e estilos inline
                const body = document.body.cloneNode(true);
                
                // Remove scripts, noscript, iframes (mantém styles)
                body.querySelectorAll('script, noscript, iframe').forEach(el => el.remove());
                
                // Adiciona estilos no topo do body clonado
                const styleBlock = '<style>' + 
                    'body { font-family: system-ui, -apple-system, sans-serif; } ' +
                    'a { color: #0066cc; } ' +
                    'img { max-width: 100%; height: auto; }' +
                    '</style>';
                
                return {
                    html: styleBlock + body.innerHTML.substring(0, 80000),
                    styles: styles,
                    title: document.title
                };
            }""")
            result["body_html"] = body_html.get("html", "")
            result["page_styles"] = body_html.get("styles", [])

            return result

        except Exception as e:
            logger.error(f"Preview error: {e}")
            return {"error": str(e), "url": url}
        finally:
            await page.close()

    async def generate_interactive_preview(self, url: str) -> dict[str, Any]:
        """
        Gera um HTML interativo onde o usuário pode clicar nos elementos
        para descobrir os selectors corretos.
        """
        browser = await self._get_browser()
        page = await browser.new_page()

        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)

            # Get page title
            title = await page.title()

            # Generate clickable HTML with element paths and preserve styles
            interactive_html = await page.evaluate("""() => {
                function generateCSSSelector(el) {
                    if (el.id) {
                        return '#' + el.id;
                    }
                    
                    let path = [];
                    while (el.nodeType === Node.ELEMENT_NODE) {
                        let selector = el.tagName.toLowerCase();
                        
                        if (el.className && typeof el.className === 'string' && el.className.trim()) {
                            const classes = el.className.trim().split(/\\s+/).filter(c => c && c.length < 20);
                            if (classes.length > 0 && classes.length < 4) {
                                selector += '.' + classes.join('.');
                            }
                        }
                        
                        // Add nth-child for uniqueness
                        const parent = el.parentElement;
                        if (parent) {
                            const siblings = Array.from(parent.children).filter(
                                s => s.tagName === el.tagName
                            );
                            if (siblings.length > 1) {
                                const index = siblings.indexOf(el) + 1;
                                selector += ':nth-child(' + index + ')';
                            }
                        }
                        
                        path.unshift(selector);
                        el = el.parentElement;
                        
                        if (!el || el.tagName === 'BODY' || el.tagName === 'HTML') {
                            break;
                        }
                    }
                    
                    return path.join(' > ');
                }

                function getElementInfo(el) {
                    const info = {
                        tag: el.tagName.toLowerCase(),
                        id: el.id || null,
                        classes: el.className ? el.className.split(/\\s+/).filter(c => c) : [],
                        text: el.textContent ? el.textContent.trim().substring(0, 80) : '',
                        selector: generateCSSSelector(el),
                        attributes: {},
                        isLink: el.tagName.toLowerCase() === 'a'
                    };
                    
                    // Get key attributes
                    ['href', 'src', 'title', 'alt', 'class', 'id'].forEach(attr => {
                        if (el.hasAttribute(attr)) {
                            info.attributes[attr] = el.getAttribute(attr);
                        }
                    });
                    
                    return info;
                }

                // Get styles from page
                const styles = [];
                document.querySelectorAll('style').forEach(el => styles.push(el.outerHTML));
                document.querySelectorAll('link[rel="stylesheet"]').forEach(el => styles.push(el.outerHTML));
                
                // Get body content
                const body = document.body.cloneNode(true);
                
                // Remove scripts, styles, and hidden elements
                body.querySelectorAll('script, noscript, iframe, nav, footer, header').forEach(el => el.remove());
                
                // Add overlay styles
                const overlayStyle = document.createElement('style');
                overlayStyle.textContent = `
                    .scrap-element {
                        position: relative !important;
                        cursor: pointer !important;
                        outline: 2px solid #ff6b6b !important;
                        background-color: rgba(255, 107, 107, 0.2) !important;
                        border-radius: 3px !important;
                        margin: 4px !important;
                        padding: 2px !important;
                        display: inline-block !important;
                    }
                    .scrap-element:hover {
                        outline: 3px solid #738cd9 !important;
                        background-color: rgba(115, 140, 217, 0.3) !important;
                    }
                    /* Links have green border */
                    .scrap-element[data-is-link="true"] {
                        outline-color: #22c55e !important;
                        background-color: rgba(34, 197, 94, 0.15) !important;
                    }
                    .scrap-element[data-is-link="true"]:hover {
                        outline-color: #16a34a !important;
                        background-color: rgba(34, 197, 94, 0.25) !important;
                    }
                    .scrap-badge {
                        position: absolute;
                        top: -8px;
                        left: -8px;
                        background: #ff6b6b;
                        color: white !important;
                        font-size: 10px;
                        font-weight: bold;
                        padding: 2px 5px;
                        border-radius: 10px;
                        z-index: 99999;
                        font-family: Arial, sans-serif;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
                    }
                    .scrap-element:hover .scrap-badge {
                        background: #738cd9;
                    }
                    /* Force dark text for readability */
                    .scrap-preview-wrapper {
                        color: #111 !important;
                        background: #fff !important;
                        padding: 10px !important;
                    }
                    .scrap-preview-wrapper * {
                        color: #111 !important;
                        background: transparent !important;
                    }
                `;
                body.prepend(overlayStyle);
                
                // Add data attributes to make elements clickable FIRST
                let elementsData = [];
                let index = 0;
                
                // First pass: mark all links
                const allLinks = new Set();
                body.querySelectorAll('a').forEach(link => {
                    allLinks.add(link);
                });
                
                body.querySelectorAll('a, div, span, p, h1, h2, h3, h4, h5, h6, li, article, section').forEach(el => {
                    if (el.textContent && el.textContent.trim().length > 5) {
                        const isLink = allLinks.has(el);
                        const info = getElementInfo(el);
                        info.index = index;
                        info.isLink = isLink;
                        if (isLink) {
                            info.attributes = info.attributes || {};
                            info.attributes.href = el.getAttribute('href');
                        }
                        elementsData.push(info);
                        
                        // Add clickable class
                        el.classList.add('scrap-element');
                        el.setAttribute('data-scrap-index', index);
                        el.setAttribute('data-scrap-selector', info.selector);
                        if (isLink) {
                            el.setAttribute('data-is-link', 'true');
                        }
                        
                        // Add numbered badge
                        const badge = document.createElement('span');
                        badge.className = 'scrap-badge';
                        badge.textContent = (index + 1).toString();
                        el.appendChild(badge);
                        
                        index++;
                    }
                });
                
                // Prevent link navigation - replace a tags with spans AFTER adding classes
                const links = body.querySelectorAll('a.scrap-element');
                links.forEach(link => {
                    const href = link.getAttribute('href') || '';
                    
                    const span = document.createElement('span');
                    span.innerHTML = link.innerHTML;
                    span.setAttribute('data-original-href', href);
                    span.setAttribute('data-is-link', 'true');
                    span.setAttribute('data-scrap-index', link.getAttribute('data-scrap-index') || '');
                    span.setAttribute('data-scrap-selector', link.getAttribute('data-scrap-selector') || '');
                    span.className = 'scrap-element';
                    
                    // Preserve badge
                    const badge = link.querySelector('.scrap-badge');
                    if (badge) {
                        span.appendChild(badge);
                    }
                    
                    link.parentNode?.replaceChild(span, link);
                });
                
                // Wrap body content
                const wrapper = document.createElement('div');
                wrapper.className = 'scrap-preview-wrapper';
                while (body.firstChild) {
                    wrapper.appendChild(body.firstChild);
                }
                body.appendChild(wrapper);

                return {
                    title: document.title,
                    url: window.location.href,
                    html: body.innerHTML.substring(0, 100000),
                    elements: elementsData.slice(0, 80),
                    styles: styles.slice(0, 20),
                    wrapper_class: 'scrap-preview-wrapper'
                };
            }""")

            return {
                "url": url,
                "title": title,
                "interactive_html": interactive_html.get("html", ""),
                "elements": interactive_html.get("elements", []),
                "styles": interactive_html.get("styles", []),
                "base_url": url,
            }

        except Exception as e:
            logger.error(f"Interactive preview error: {e}")
            return {"error": str(e), "url": url}
        finally:
            await page.close()

    async def _suggest_selectors(self, element: ElementHandle) -> dict[str, Any]:
        """Sugere selectors baseados no elemento."""
        return await element.evaluate("""(el) => {
            const suggestions = {};
            
            // Classes
            if (el.className && typeof el.className === 'string') {
                suggestions.classes = el.className.split(' ').filter(c => c);
            }
            
            // ID
            if (el.id) {
                suggestions.id = el.id;
            }
            
            // Tag
            suggestions.tag = el.tagName.toLowerCase();
            
            // Atributos comuns
            const attrs = ['href', 'src', 'title', 'class', 'id'];
            suggestions.attributes = {};
            attrs.forEach(attr => {
                if (el.hasAttribute(attr)) {
                    suggestions.attributes[attr] = el.getAttribute(attr);
                }
            });
            
            // Títulos e textos
            if (el.querySelector) {
                const title = el.querySelector('.titulo, .title, h1, h2, h3, h4, h5, h6');
                if (title) suggestions.text_content = title.textContent?.trim().substring(0, 100);
                
                const category = el.querySelector('.categoria, .category, .tag');
                if (category) suggestions.category = category.textContent?.trim();
            }
            
            return suggestions;
        }""")

    async def execute_workflow(
        self, workflow: WorkflowConfig, base_url: str, limit: int = 50
    ) -> ScrapResult:
        """Executa o workflow completo de scraping."""
        browser = await self._get_browser()

        # Encontrar nó inicial
        start_node = None
        for node in workflow.nodes:
            if node.id == workflow.start_node_id:
                start_node = node
                break

        if not start_node:
            return ScrapResult(
                success=False, items=[], error="Nó inicial não encontrado"
            )

        try:
            # Executar nó inicial
            items = await self._execute_node(browser, start_node, base_url, limit)

            # Se tem nó seguinte, buscar dados de detalhe
            nodes_executed = [start_node.id]

            if start_node.next_node_id and items:
                next_node = None
                for node in workflow.nodes:
                    if node.id == start_node.next_node_id:
                        next_node = node
                        break

                if next_node:
                    # Para cada item, navegar para e link extrair detalhes
                    detail_items = await self._execute_detail_node(
                        browser, next_node, items, limit
                    )
                    nodes_executed.append(next_node.id)

                    # Mesclar dados
                    for i, item in enumerate(items):
                        if i < len(detail_items):
                            item.detail_data = detail_items[i].data

            return ScrapResult(success=True, items=items, nodes_executed=nodes_executed)

        except Exception as e:
            logger.error(f"Workflow execution error: {e}")
            return ScrapResult(success=False, items=[], error=str(e))

    async def _execute_node(
        self, browser: Browser, node: NodeConfig, base_url: str, limit: int
    ) -> list[ScrapedItem]:
        """Executa um nó do workflow com suporte a paginação."""
        url = node.url or base_url
        if not url.startswith("http"):
            url = urljoin(base_url, url)

        items: list[ScrapedItem] = []
        current_page = 1
        max_pages = node.pagination.max_pages if node.pagination else 5
        pagination_type = node.pagination.type if node.pagination else "none"

        while len(items) < limit and current_page <= max_pages:
            page = await browser.new_page()
            try:
                # Constrói URL com parâmetro de página se necessário
                page_url = url
                if pagination_type == "page_param" and current_page > 1:
                    param_name = (
                        node.pagination.page_param_name if node.pagination else "pag"
                    )
                    separator = "&" if "?" in url else "?"
                    page_url = f"{url}{separator}{param_name}={current_page}"

                await page.goto(page_url, wait_until="networkidle", timeout=30000)

                # Encontrar itens da lista
                if node.list_selector and node.item_selector:
                    selector = f"{node.list_selector} {node.item_selector}"
                elif node.item_selector:
                    selector = node.item_selector
                else:
                    selector = None

                if selector:
                    elements = await page.query_selector_all(selector)

                    if not elements:
                        # Se não encontrou itens e paginação está ativa, tenta parar
                        if node.pagination and node.pagination.stop_when_empty:
                            break
                        continue

                    for el in elements[: limit - len(items)]:
                        item_data = {"_page": current_page}

                        # Extrair campos configurados
                        for field_cfg in node.fields:
                            value = await self._extract_field(el, field_cfg)
                            item_data[field_cfg.name] = value

                        # Se precisa seguir links, guardar o link
                        if node.follow_links and node.link_selector:
                            link = await el.query_selector(node.link_selector)
                            if link:
                                href = await link.get_attribute("href")
                                if href:
                                    item_data["_detail_url"] = urljoin(base_url, href)

                        items.append(ScrapedItem(data=item_data))

                # Verificar se há próxima página
                if pagination_type == "next_button" and node.pagination:
                    next_btn = await page.query_selector(
                        node.pagination.next_button_selector
                    )
                    if next_btn:
                        current_page += 1
                        await page.close()
                        continue
                    else:
                        break
                elif pagination_type == "page_param":
                    current_page += 1
                    await page.close()
                    continue
                else:
                    break

            except Exception as e:
                logger.warning(f"Error on page {current_page}: {e}")
                break
            finally:
                await page.close()

        return items

    async def _execute_detail_node(
        self, browser: Browser, node: NodeConfig, items: list[ScrapedItem], limit: int
    ) -> list[ScrapedItem]:
        """Executa nó de detalhe - navega para cada URL e extrai campos."""
        detail_items: list[ScrapedItem] = []

        # Coletar URLs únicas
        urls = []
        for item in items[:limit]:
            if detail_url := item.data.get("_detail_url"):
                urls.append(detail_url)

        # Processar cada URL
        for url in urls:
            page = await browser.new_page()
            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)

                detail_data = {}

                for field_cfg in node.fields:
                    # Tenta encontrar o elemento na página
                    element = await page.query_selector(field_cfg.selector)
                    if element:
                        value = await self._extract_field(element, field_cfg)
                        detail_data[field_cfg.name] = value

                detail_items.append(ScrapedItem(data=detail_data))

            except Exception as e:
                logger.warning(f"Error fetching detail {url}: {e}")
                detail_items.append(ScrapedItem(data={"error": str(e)}))
            finally:
                await page.close()

        return detail_items

    async def preview_link(self, url: str, base_url: str = "") -> dict[str, Any]:
        """
        Faz preview de um link clicado na página.
        Útil para configurar scraping de páginas de detalhe.
        """
        browser = await self._get_browser()
        page = await browser.new_page()

        try:
            # Resolve URL relativa se necessário
            if not url.startswith("http"):
                url = urljoin(base_url, url)

            await page.goto(url, wait_until="networkidle", timeout=30000)

            # Get page info
            title = await page.title()

            # Get content with styles
            page_content = await page.evaluate("""() => {
                const styles = [];
                document.querySelectorAll('style').forEach(el => styles.push(el.outerHTML));
                document.querySelectorAll('link[rel="stylesheet"]').forEach(el => styles.push(el.outerHTML));
                
                const body = document.body.cloneNode(true);
                body.querySelectorAll('script, noscript, iframe').forEach(el => el.remove());
                
                return {
                    html: body.innerHTML.substring(0, 80000),
                    styles: styles.slice(0, 20),
                    title: document.title,
                    url: window.location.href
                };
            }""")

            # Sugere selectors para campos comuns
            selectors_suggestions = await page.evaluate("""() => {
                const suggestions = {
                    title: [],
                    content: [],
                    date: [],
                    image: []
                };
                
                // Title selectors
                const titles = document.querySelectorAll('h1, h2, .title, .titulo, .article-title, [class*="title"]');
                titles.forEach(el => suggestions.title.push({
                    text: el.textContent?.trim().substring(0, 50),
                    selector: getSelector(el)
                }));
                
                // Content selectors
                const contents = document.querySelectorAll('.content, .article-content, .post-content, [class*="content"], article, main');
                contents.forEach(el => suggestions.content.push({
                    text: el.textContent?.trim().substring(0, 100),
                    selector: getSelector(el)
                }));
                
                // Date selectors
                const dates = document.querySelectorAll('.date, .data, time, [class*="date"], [class*="data"]');
                dates.forEach(el => suggestions.date.push({
                    text: el.textContent?.trim(),
                    selector: getSelector(el),
                    datetime: el.getAttribute('datetime')
                }));
                
                // Image selectors
                const images = document.querySelectorAll('article img, .content img, main img');
                if (images.length > 0) {
                    suggestions.image.push({
                        src: images[0].getAttribute('src'),
                        selector: getSelector(images[0])
                    });
                }
                
                return suggestions;
            }

            function getSelector(el) {
                if (el.id) return '#' + el.id;
                let path = [];
                while (el && el.nodeType === Node.ELEMENT_NODE && el.tagName !== 'BODY') {
                    let selector = el.tagName.toLowerCase();
                    if (el.className && typeof el.className === 'string') {
                        const classes = el.className.trim().split(/\\s+/).filter(c => c && c.length < 20);
                        if (classes.length > 0 && classes.length < 4) {
                            selector += '.' + classes.join('.');
                        }
                    }
                    const parent = el.parentElement;
                    if (parent) {
                        const siblings = Array.from(parent.children).filter(s => s.tagName === el.tagName);
                        if (siblings.length > 1) {
                            const index = siblings.indexOf(el) + 1;
                            selector += ':nth-child(' + index + ')';
                        }
                    }
                    path.unshift(selector);
                    el = el.parentElement;
                }
                return path.join(' > ');
            }""")

            return {
                "url": url,
                "title": title,
                "html": page_content.get("html", ""),
                "styles": page_content.get("styles", []),
                "selectors_suggestions": selectors_suggestions,
            }

        except Exception as e:
            logger.error(f"Link preview error: {e}")
            return {"error": str(e), "url": url}
        finally:
            await page.close()

    async def _extract_field(
        self, element: ElementHandle, field_cfg: FieldConfig
    ) -> Any:
        """Extrai valor de um campo baseado na configuração."""
        if field_cfg.field_type == "text":
            return await element.text_content()
        elif field_cfg.field_type == "html":
            return await element.inner_html()
        elif field_cfg.field_type == "attribute":
            if field_cfg.attribute:
                return await element.get_attribute(field_cfg.attribute)
            return None
        elif field_cfg.field_type == "image":
            return await element.get_attribute("src")
        else:
            return await element.text_content()

    async def quick_scrape(
        self,
        url: str,
        selectors: dict[str, str],  # nome -> selector
        item_selector: Optional[str] = None,
        limit: int = 20,
    ) -> ScrapResult:
        """
        Scraping rápido com selectors simples.
        Útil para testes rápidos.
        """
        browser = await self._get_browser()
        page = await browser.new_page()

        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)

            items: list[ScrapedItem] = []

            if item_selector:
                elements = await page.query_selector_all(item_selector)
            else:
                elements = [page]

            for el in elements[:limit]:
                data = {}
                for name, selector in selectors.items():
                    try:
                        sub_el = await el.query_selector(selector)
                        if sub_el:
                            data[name] = await sub_el.text_content()
                        else:
                            data[name] = None
                    except Exception as e:
                        data[name] = f"Error: {e}"

                items.append(ScrapedItem(data=data))

            return ScrapResult(success=True, items=items)

        except Exception as e:
            return ScrapResult(success=False, items=[], error=str(e))
        finally:
            await page.close()


# Instância global do serviço
_scraper_service: Optional[ScraperService] = None


def get_scraper_service() -> ScraperService:
    """Obtém instância do serviço de scraping."""
    global _scraper_service
    if _scraper_service is None:
        _scraper_service = ScraperService()
    return _scraper_service


async def close_scraper():
    """Fecha o serviço de scraping."""
    global _scraper_service
    if _scraper_service:
        await _scraper_service.close()
        _scraper_service = None
