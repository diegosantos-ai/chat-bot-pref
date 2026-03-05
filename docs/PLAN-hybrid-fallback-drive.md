# PLANO-fallback-hibrido-drive

## 1. Contexto e Objetivo
O objetivo é implementar um **Mecanismo de Fallback Híbrido** e um **Atualizador Automático da Base de Conhecimento** via Google Drive.
-   **Reativo**: Quando a confiança do RAG for baixa, o sistema faz um "scraping" no site da prefeitura (`santatereza.pr.gov.br`) em busca de notícias/decretos em tempo real. Se encontrar, responde. Se não, escala via e-mail.
-   **Proativo**: Uma tarefa em segundo plano (background job) verifica uma pasta específica do Google Drive 2x ao dia em busca de novos arquivos PDF/DOCX, ingere-os na base RAG e os torna disponíveis para consultas futuras.

## 2. Arquitetura e Componentes

### 2.1. Novas Dependências
-   `google-api-python-client`, `google-auth`: Para API do Google Drive.
-   `beautifulsoup4`: Para scraping do site (leve).
-   `apscheduler`: Para agendar o job em segundo plano (2x/dia).
-   `emails` ou `smtplib` (lib padrão): Para envio de e-mails de escalonamento.

### 2.2. Estrutura de Módulos
-   `app/services/`: Criar este diretório (conforme solicitado no arquivo da feature).
    -   `web_scraper.py`: Lida com o scraping de `santatereza.pr.gov.br`.
    -   `drive_watcher.py`: Lida com a interação da API do Drive e download de arquivos.
    -   `scheduler.py`: Gerencia a instância do APScheduler.
    -   `mailer.py`: Lida com o envio de e-mails.
-   `app/rag/ingest.py`: Refatorar para permitir a ingestão de um único arquivo/texto dinamicamente, não apenas a reconstrução completa do diretório.

### 2.3. Fluxo de Dados
1.  **Consulta do Usuário** -> **Orchestrator** -> **RAG Retriever**.
2.  **Se Score < Limiar (Threshold)**:
    -   **Orchestrator** chama `WebScraper.search(query)`.
    -   **Se Encontrado**: LLM gera resposta -> Usuário.
    -   **Se Não Encontrado**: `Mailer.send_escalation()` -> Gestor; LLM envia "mensagem de fallback" -> Usuário.
3.  **Job em Segundo Plano (08:00, 14:00)**:
    -   `Scheduler` aciona `DriveWatcher`.
    -   `DriveWatcher` lista arquivos na Pasta ID alvo.
    -   Verifica `processed_files.json` (ou BD) para duplicatas (ID + MD5).
    -   Baixa novos arquivos -> Converte para Texto -> Chama `RAG.ingest_document()`.

## 3. Detalhamento das Tarefas

### Fase 1: Configuração e Dependências
- [ ] Adicionar `google-api-python-client`, `beautifulsoup4`, `apscheduler` ao `requirements.txt`.
- [ ] Criar diretório `app/services/`.
- [ ] Configurar `client_secret.json` ou credenciais de Conta de Serviço para Google Drive.

### Fase 2: Fallback Reativo (Web)
- [ ] Implementar `WebScraper` (`app/services/web_scraper.py`).
- [ ] Implementar `Mailer` (`app/services/mailer.py`).
- [ ] Atualizar `Orchestrator` para incluir a lógica de fallback (RAG -> Scraper -> Mailer).

### Fase 3: Auto-Update Proativo (Drive)
- [ ] Implementar `DriveWatcher` (`app/services/drive_watcher.py`).
- [ ] Atualizar `app/rag/ingest.py` para suportar ingestão incremental (adicionar função `ingest_text(content, metadata)`).
- [ ] Implementar `Scheduler` (`app/services/scheduler.py`) para rodar `DriveWatcher` às 08:00 e 14:00.
- [ ] Inicializar Scheduler em `app/main.py` (evento lifespan).

## 4. Plano de Verificação
-   **Web Scraper**: Testar com uma notícia recente conhecida do site.
-   **E-mail**: Disparar uma consulta falsa de baixa confiança e verificar o recebimento do e-mail.
-   **Drive**: Enviar um PDF de teste para a pasta do Drive, aguardar o job (ou acionar manualmente) e verificar se aparece nos resultados de busca do RAG.

## 5. Atribuições de Agentes
-   `@backend-specialist`: Implementação de Serviços e atualizações do RAG.
-   `@orchestrator`: Lógica de integração no fluxo principal.
