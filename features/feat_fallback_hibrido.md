🚀 Feature: Fallback Híbrido (Web Real-Time + Escalonamento Humano)
1. Objetivo e Escopo
Objetivo: Implementar um mecanismo de "última tentativa" quando a IA não souber a resposta (Confiança Baixa). O sistema deve tentar buscar a informação no site oficial da prefeitura. Se falhar, deve avisar o gestor por e-mail e confortar o cidadão. Restrição Crítica (Non-Destructive): A lógica atual de ingestão e a base vetorial (ChromaDB) não devem ser alteradas. Esta funcionalidade atua apenas no momento da falha de recuperação (RAG Miss).

2. Fluxo de Decisão (Lógica do Algoritmo)
O fluxo deve seguir estritamente esta ordem:

Tentativa 1 (Existente): Consulta RAG na base vetorial.

Se Confiança > Threshold (ex: 0.7): Responde normalmente.

Se Confiança < Threshold: Inicia Fallback (Nova Funcionalidade).

Tentativa 2 (Nova - Web Scraper): O sistema acessa a URL de "Notícias/Decretos" da Prefeitura em tempo real.

Busca: Procura por palavras-chave da pergunta do usuário nos últimos posts.

Sucesso: O LLM resume a informação encontrada e responde ao usuário (sem citar link, mantendo a persona).

Falha: Vai para a Tentativa 3.

Tentativa 3 (Nova - Escalonamento): O sistema assume que não sabe.

Ação A: Dispara e-mail para lista de gestores cadastrados com a pergunta e metadados.

Ação B: Responde ao usuário no chat: "Não tenho essa informação oficial atualizada na minha base, mas já notifiquei a equipe humana da Prefeitura para verificarem para você."

3. User Stories (Requisitos)
[ ] Story 01 (Backend): Como Sistema, se minha confiança na resposta for baixa, eu quero varrer a página de notícias da prefeitura para ver se algo novo foi publicado sobre o tema.

[ ] Story 02 (Backend/Notification): Como Gestor, quero receber um e-mail imediato quando a IA não souber responder e nem encontrar no site, contendo a pergunta do cidadão, para que eu possa tomar providência.

[ ] Story 03 (User Experience): Como Cidadão, quero receber uma resposta natural baseada no site (se encontrada) ou um aviso de que "a equipe foi notificada" (se não encontrada), sem receber links técnicos ou mensagens de erro.

4. Critérios de Aceitação (Técnicos)
Cenário A: RAG Falha, mas Site Salva (Sucesso no Scraper)
Dado que o RAGRetriever retornou score 0.4 (baixo) para a pergunta "Saiu decreto sobre a dengue hoje?".

Quando o WebScraperService varrer o site e encontrar um título contendo "Dengue" e data de "Hoje".

Então a {bot_name} deve formular a resposta com o conteúdo desse texto.

E NÃO deve enviar e-mail para o gestor.

E NÃO deve fornecer o link da URL na resposta final (apenas o conteúdo).

Cenário B: RAG Falha e Site Falha (Escalonamento)
Dado que o RAGRetriever retornou score baixo e o WebScraperService não achou nada relevante.

Quando o processo terminar.

Então disparar e-mail via SMTP/SendGrid para gestores@santatereza.pr.gov.br.

E responder ao usuário com a mensagem padrão de escalonamento humano.

5. Definições Técnicas para o Agente (Handover)
Novos Componentes (Backend)
Não altere o app/rag/retriever.py existente, apenas estenda o uso no Orchestrator ou crie um Wrapper.

app/services/web_scraper.py:

Usar BeautifulSoup ou Playwright (depende se o site da prefeitura requer JS).

Deve ter timeout agressivo (máx 5s) para não travar a resposta do Instagram.

Target URL: Definida via variável de ambiente.

app/services/mailer.py:

Função assíncrona (async def send_escalation_alert(...)) para não bloquear a thread principal.

Template simples:

Plaintext
Assunto: [{bot_name}] Pergunta sem resposta - Ação Necessária
Cidadão: {user_id} (Instagram)
Pergunta: "{user_query}"
Data: {timestamp}
Status: Não encontrado na Base RAG nem no Site Oficial.
Variáveis de Ambiente (.env):

Adicionar:

FALLBACK_TARGET_URL="https://santatereza.pr.gov.br/noticias/"

SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS

MANAGER_EMAILS="fvlopestecnologia@gmail.com, contato.revolutionagencia@gmail.com"

Alteração no Fluxo (Orchestrator)
No arquivo onde a decisão de resposta é tomada (provavelmente app/services/orchestrator.py):

Python
# Pseudo-código da lógica a ser injetada
context, score = rag_retriever.search(query)

if score < THRESHOLD_CONFIDENCE:
    # 1. Tenta Scraper
    web_content = await web_scraper.search_site(query)
    
    if web_content:
        # Pede pro LLM gerar a resposta com o conteúdo da web
        response = llm.generate(web_content, query)
    else:
        # 2. Escalona
        await mailer.send_escalation_alert(query, user_info)
        response = "Não tenho essa informação oficial atualizada..."
else:
    # Fluxo normal que já existe
    response = llm.generate(context, query)