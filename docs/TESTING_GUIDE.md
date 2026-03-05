# Guia Rápido de Testes - {bot_name}

Este guia explica como testar as funcionalidades principais do {bot_name}, incluindo o RAG atualizado e os futuros recursos de Fallback e Google Drive.

## 1. Teste de RAG (Busca na Base de Conhecimento)

Use o script criado para simular perguntas do usuário e ver o que o sistema encontra na base vetorial.

**Comando:**
```powershell
python scripts/query_rag.py "Sua pergunta entre aspas"
```

**Exemplo (Validar REFIS 2025):**
```powershell
python scripts/query_rag.py "até quando vai o refis 2025"
```
*Esperado: Encontrar o trecho que menciona "prorrogado até 27 de fevereiro de 2025".*

## 2. Teste de Ingestão Manual (Forçar atualização)

Se você editar um arquivo Markdown na pasta `data/knowledge_base`, rode este comando para atualizar o banco de dados:

**Comando:**
```powershell
python -m app.rag.ingest data/knowledge_base/BA-RAG-PILOTO-2026.01.v1
```

## 3. Testes Automatizados (Unitários)

Para garantir que nada quebrou na lógica interna:

**Comando:**
```powershell
pytest
```

## 4. Testes Futuros (Fallback e Drive)

> *Estes testes serão possíveis após a implementação da feature `hybrid-fallback-drive`.*

### Teste de Fallback (Simulação)
Para simular uma falha no RAG e ativar o Web Scraper:
1.  Faça uma pergunta sobre um fato muito recente não contido na base (ex: "Resultado do jogo de ontem").
2.  Verifique se o log mostra `[FALLBACK] Acionando WebScraper...`.

### Teste de Auto-Update (Google Drive)
1.  Coloque um arquivo `.pdf` ou `.docx` na pasta monitorada do Google Drive.
2.  Aguarde o horário do job ou force a execução (instruções futuras).
3.  Use o `scripts/query_rag.py` para buscar conteúdo desse novo arquivo.
