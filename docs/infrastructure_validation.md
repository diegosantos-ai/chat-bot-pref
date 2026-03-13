# Guia de Validação de Infraestrutura

## Visão Geral

Este documento descreve o processo de validação da infraestrutura e variáveis de ambiente necessárias para o funcionamento do **{bot_name} - Pilot Atendimento**.

## Script de Validação

O script `scripts/ops/validate_infrastructure.py` executa verificações completas da infraestrutura e reporta problemas encontrados.

### Como Executar

```bash
python scripts/ops/validate_infrastructure.py
```

### O que é Validado

O script verifica os seguintes componentes:

#### 1. **Versão do Python**
- ✅ Verifica se Python 3.11+ está instalado
- ⚠️ Versões anteriores não são suportadas

#### 2. **Dependências Python**
Valida se todas as bibliotecas necessárias estão instaladas:
- `fastapi` - Framework web
- `uvicorn` - Servidor ASGI
- `pydantic` - Validação de dados
- `pydantic_settings` - Configurações com Pydantic
- `python-multipart` - Upload de arquivos/form
- `asyncpg` - Driver PostgreSQL assíncrono
- `chromadb` - Banco vetorial para RAG
- `google-genai` - SDK Google Gemini
- `httpx` - Cliente HTTP assíncrono
- `python-dotenv` - Carregamento de variáveis .env

**Solução**: Se falhar, execute:
```bash
pip install -r requirements.txt
```

#### 3. **Arquivo .env**
- Verifica se o arquivo `.env` existe na raiz do projeto
- Este arquivo deve conter todas as variáveis de ambiente sensíveis

**Solução**: Crie um arquivo `.env` na raiz do projeto com as variáveis listadas abaixo.

#### 4. **Variáveis de Ambiente Obrigatórias**

O script valida a presença das seguintes variáveis:

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `GEMINI_API_KEY` | Chave da API Google Gemini | `AIza...` |
| `DATABASE_URL` | URL de conexão PostgreSQL | `postgresql://user:pass@host:5432/db` |
| `META_ACCESS_TOKEN` | Token de acesso da Meta Platform | `EAA...` |
| `META_PAGE_ID` | ID da Página do Facebook | `123456789...` |
| `META_APP_SECRET` | App Secret da aplicação Meta | `abc123...` |
| `META_WEBHOOK_VERIFY_TOKEN` | Token de verificação do webhook | `verify_token_webhook` |

**Variáveis Opcionais** (com valores padrão):
- `CHROMA_PERSIST_DIR` - Diretório ChromaDB (padrão: `./chroma_data`)
- `RAG_BASE_ID` - ID da base RAG (padrão: `BA-RAG-PILOTO-2026.01.v1`)
- `GEMINI_MODEL` - Modelo Gemini (padrão: `gemini-2.0-flash`)
- `ENV` - Ambiente de execução (padrão: `dev`)
- `DEBUG` - Modo debug (padrão: `False`)

#### 5. **Conexão PostgreSQL**
- Testa conectividade com o banco de dados
- Verifica versão do PostgreSQL
- Valida existência das tabelas `audit_events`, `rag_queries`, `usuarios_anonimos` e `conversas`

**Solução**: Se falhar:
1. Verifique se o PostgreSQL está rodando
2. Confirme que a `DATABASE_URL` está correta
3. Execute o script de setup do banco:
   ```bash
   python scripts/setup_db.py --database-url "postgresql://user:pass@host:5432/db"
   ```

#### 6. **ChromaDB**
- Verifica se o diretório de persistência existe
- Conta quantos arquivos existem (indicador de dados ingeridos)

**Solução**: O diretório será criado automaticamente na primeira ingestão de documentos.

#### 7. **Google Gemini API**
- Testa autenticação com a Google Gemini API
- Verifica se o modelo configurado (`GEMINI_MODEL`) está disponível

**Solução**: Se falhar:
1. Verifique se a chave `GEMINI_API_KEY` está correta
2. Confirme que a chave não expirou
3. Teste manualmente com a API do Gemini

#### 8. **Meta Platform API**
- Testa autenticação com a Meta Graph API
- Valida o token de acesso
- Verifica consistência do `META_PAGE_ID`

**Solução**: Se falhar:
1. Use o script `scripts/verify_meta_tokens.py` para diagnóstico detalhado
2. Verifique se o token não expirou (tokens de página têm validade)
3. Confirme que as permissões estão corretas no Facebook App

#### 9. **Estrutura de Arquivos**
Valida a existência de arquivos e diretórios críticos:
- `app/main.py` - Aplicação principal
- `app/settings.py` - Configurações
- `requirements.txt` - Dependências
- `base/` - Documentos RAG
- `prompts/` - Prompts do sistema

## Checklist de Validação Manual

Além do script automatizado, é recomendado verificar manualmente:

### Infraestrutura

- [ ] **Servidores/Cloud**
  - [ ] Instância/VM provisionada
  - [ ] Recursos adequados (CPU, RAM, disco)
  - [ ] Permissões de acesso configuradas
  - [ ] Firewall configurado (portas 8000, 5432)

- [ ] **PostgreSQL**
  - [ ] Banco de dados criado
  - [ ] Schema aplicado (tabelas `audit_events`, `rag_queries`, `usuarios_anonimos`, `conversas`)
  - [ ] Usuário com permissões corretas
  - [ ] Backup configurado

- [ ] **ChromaDB**
  - [ ] Diretório de persistência acessível
  - [ ] Espaço em disco suficiente
  - [ ] Documentos RAG ingeridos
  - [ ] Backup configurado (recomendado)

- [ ] **FastAPI/Uvicorn**
  - [ ] Aplicação inicia sem erros
  - [ ] Endpoint `/health` responde
  - [ ] Documentação acessível em `/docs`
  - [ ] CORS configurado (se necessário)

### Segurança

- [ ] **Variáveis de Ambiente**
  - [ ] Arquivo `.env` **não** está no controle de versão
  - [ ] Valores sensíveis não estão hardcoded no código
  - [ ] Tokens e segredos estão em cofre seguro (produção)

- [ ] **Tokens e Credenciais**
  - [ ] Tokens da Meta não expirados
  - [ ] Chave Gemini com quota disponível
  - [ ] Senha do banco de dados forte
  - [ ] Webhook verify token único e seguro

### Meta Platform (Facebook/Instagram)

- [ ] **Facebook App**
  - [ ] App criado e configurado
  - [ ] Permissões solicitadas e aprovadas:
    - `pages_manage_metadata`
    - `pages_messaging`
    - `instagram_basic`
    - `instagram_manage_messages`
  - [ ] Webhook configurado e verificado
  - [ ] URL do webhook HTTPS válida

- [ ] **Página do Facebook**
  - [ ] Página vinculada ao App
  - [ ] Token de acesso de página gerado
  - [ ] ID da página correto

### Google Gemini

- [ ] **API Key**
  - [ ] Chave válida e não expirada
  - [ ] Quota disponível na conta
  - [ ] Modelo configurado disponível
  - [ ] Rate limits adequados para o volume esperado

### Observabilidade (Fase 5)

- [ ] **Logs**
  - [ ] Logs estruturados configurados
  - [ ] Rotação de logs ativa
  - [ ] Agregação de logs (se aplicável)

- [ ] **Métricas**
  - [ ] Views SQL criadas (`analytics/v1/views.sql`)
  - [ ] Dashboard de métricas configurado
  - [ ] KPIs definidos

- [ ] **Alertas**
  - [ ] Alertas para falhas críticas
  - [ ] Notificações configuradas
  - [ ] Rotina de monitoramento definida

## Troubleshooting

### Erro: "psycopg2 não instalado"

```bash
pip install psycopg2-binary
```

Ou para produção:
```bash
pip install psycopg2
```

### Erro: "Conexão com PostgreSQL falhou"

1. Verifique se o PostgreSQL está rodando:
   ```bash
   # Linux/Mac
   sudo systemctl status postgresql
   
   # Windows (se instalado como serviço)
   sc query postgresql
   ```

2. Teste conexão manual:
   ```bash
   psql -U username -h hostname -d database_name
   ```

3. Verifique firewall e permissões

### Erro: "Google Gemini API inválida"

1. Teste a chave manualmente:
   ```bash
   curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent" \
     -H "x-goog-api-key: $GEMINI_API_KEY" \
     -H "Content-Type: application/json" \
     -d "{\"contents\":[{\"parts\":[{\"text\":\"ping\"}]}]}"
   ```

2. Verifique quota e permissões no Google AI Studio.

### Erro: "Meta Token inválido"

1. Execute diagnóstico detalhado:
   ```bash
   python scripts/verify_meta_tokens.py
   ```

2. Regenere o token no Facebook App se necessário

3. Verifique permissões e aprovações

## Scripts Auxiliares

- **`scripts/ops/validate_infrastructure.py`** - Validação completa (este guia)
- **`scripts/verify_meta_tokens.py`** - Diagnóstico específico Meta
- **`scripts/setup_db.py`** - Setup do banco de dados
- **`scripts/test_webhook_local.py`** - Teste local de webhooks

## Próximos Passos

Após a validação bem-sucedida:

1. **Execute a aplicação**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

2. **Teste endpoints**:
   - `GET /health` - Health check
   - `POST /api/chat/simple` - Chat simples
   - `POST /webhook/meta` - Webhook Meta

3. **Execute smoke tests** conforme `implementation_plan.md` (Fase 5)

4. **Configure observabilidade** conforme `docs/observability.md`

## Referências

- [README.md](../README.md) - Visão geral do projeto
- [docs/observability.md](./observability.md) - Guia de observabilidade
- [implementation_plan.md](../implementation_plan.md) - Plano de implementação Fase 5
- [app/settings.py](../app/settings.py) - Todas as configurações disponíveis

---

**Última atualização**: Janeiro 2026  
**Versão**: 1.0
