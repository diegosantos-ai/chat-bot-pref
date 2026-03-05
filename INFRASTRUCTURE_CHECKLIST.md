# Checklist de Validação de Infraestrutura - TerezIA

Use este checklist para validar a infraestrutura antes do deploy em produção.

## 🚀 Pré-requisitos

### Software e Ambiente
- [ ] Python 3.11+ instalado
- [ ] PostgreSQL 12+ instalado e rodando
- [ ] Git instalado
- [ ] Editor de texto/IDE configurado

### Ferramentas de Validação
- [ ] Script `scripts/ops/validate_infrastructure.py` executado com sucesso
- [ ] Todas as dependências instaladas (`pip install -r requirements.txt`)

## 📋 Variáveis de Ambiente

### Arquivo .env
- [ ] Arquivo `.env` criado na raiz do projeto
- [ ] Arquivo `.env` está no `.gitignore` (NUNCA fazer commit)
- [ ] Backup seguro das variáveis em cofre de senhas/secrets manager

### Variáveis Obrigatórias
- [ ] `GEMINI_API_KEY` - Chave válida do Google Gemini
- [ ] `DATABASE_URL` - URL PostgreSQL no formato `postgresql://user:pass@host:5432/db`
- [ ] `META_ACCESS_TOKEN` - Token de acesso da página Facebook
- [ ] `META_PAGE_ID` - ID da página Facebook
- [ ] `META_APP_SECRET` - App Secret do Facebook App
- [ ] `META_WEBHOOK_VERIFY_TOKEN` - Token único para verificação do webhook

### Variáveis Opcionais (com valores sensatos)
- [ ] `ENV` - Ambiente (dev/staging/prod)
- [ ] `DEBUG` - False em produção
- [ ] `CHROMA_PERSIST_DIR` - Diretório ChromaDB (padrão: `./chroma_data`)
- [ ] `GEMINI_MODEL` - Modelo a usar (padrão: `gemini-2.0-flash`)

## 🗄️ Banco de Dados PostgreSQL

### Instalação e Configuração
- [ ] PostgreSQL instalado e rodando
- [ ] Banco de dados criado
- [ ] Usuário com permissões apropriadas criado
- [ ] Firewall configurado (porta 5432)

### Schema e Tabelas
- [ ] Script `scripts/setup_db.py` executado com sucesso
- [ ] Tabela `audit_events` criada
- [ ] Tabela `rag_queries` criada
- [ ] Views de analytics criadas (`analytics/v1/views.sql`)

### Testes de Conectividade
- [ ] Conexão via psql funciona: `psql -U user -h host -d database`
- [ ] Script de validação conecta com sucesso
- [ ] SELECT, INSERT, UPDATE funcionam

### Backup
- [ ] Estratégia de backup definida
- [ ] Backup automatizado configurado (Task Scheduler/cron)
- [ ] Teste de restore realizado

**Sugestão (Windows)**:
- `scripts/backup_postgres.py` (CSV via COPY, sem `psql/pg_dump`)
- `scripts/backup_chroma.py` (zip do `CHROMA_PERSIST_DIR`)
- `scripts/backup_all.ps1` (orquestra ambos)
- Task Scheduler: tarefa diária `TerezIA-Backup`

## 🧠 ChromaDB (Vector Store)

### Configuração
- [ ] Diretório `CHROMA_PERSIST_DIR` existe e é acessível
- [ ] Permissões de leitura/escrita no diretório
- [ ] Espaço em disco suficiente (mínimo 1GB recomendado)

### Dados RAG
- [ ] Documentos da pasta `base/` estão atualizados
- [ ] Ingestão de documentos executada com sucesso
- [ ] ChromaDB contém chunks (verificar com script de validação)

### Backup
- [ ] Backup do diretório ChromaDB configurado (recomendado)

## 🤖 Google Gemini API

### Configuração
- [ ] Chave API `GEMINI_API_KEY` válida
- [ ] Modelo configurado (`GEMINI_MODEL`) disponível na conta

### Testes
- [ ] Script de validação autentica com sucesso
- [ ] Teste manual de geração funciona
- [ ] Rate limits adequados para volume esperado

### Monitoramento
- [ ] Monitoramento/limites revisados na console do Google (Gemini)
- [ ] Alertas de uso/custo configurados

## 📱 Meta Platform (Facebook/Instagram)

### Facebook App
- [ ] App criado em https://developers.facebook.com
- [ ] App em modo de produção (não desenvolvimento)
- [ ] Permissões necessárias aprovadas:
  - [ ] `pages_manage_metadata`
  - [ ] `pages_messaging`
  - [ ] `instagram_basic`
  - [ ] `instagram_manage_messages`

### Página Facebook
- [ ] Página criada e ativa
- [ ] Página vinculada ao Facebook App
- [ ] Token de acesso de página gerado (não expira ou tem validade longa)
- [ ] ID da página correto em `META_PAGE_ID`

### Webhook
- [ ] URL do webhook configurada (deve ser HTTPS)
- [ ] Token de verificação configurado
- [ ] Webhook verificado pelo Meta
- [ ] Eventos subscritos:
  - [ ] `messages`
  - [ ] `messaging_postbacks`
  - [ ] `feed` (comentários)

### Testes
- [ ] Script `scripts/verify_meta_tokens.py` passa
- [ ] Teste de envio de mensagem funciona
- [ ] Teste de recebimento de webhook funciona

## 🚀 Aplicação FastAPI

### Instalação
- [ ] Todas as dependências Python instaladas
- [ ] Virtual environment configurado (recomendado)

### Configuração
- [ ] Arquivo `app/settings.py` carrega variáveis do `.env`
- [ ] Logs configurados adequadamente
- [ ] CORS configurado (se necessário)

### Execução
- [ ] Aplicação inicia sem erros: `uvicorn app.main:app --host 0.0.0.0 --port 8000` (ou `APP_PORT`)
- [ ] Endpoint `/health` responde 200 OK
- [ ] Documentação OpenAPI acessível em `/docs`

### Testes de Endpoints
- [ ] `GET /` - Retorna informações da API
- [ ] `GET /health` - Health check
- [ ] `POST /api/chat/simple` - Chat simples funciona
- [ ] `POST /webhook/meta` - Recebe webhooks

## 🔒 Segurança

### Secrets e Tokens
- [ ] Nenhum token/senha no código fonte
- [ ] Arquivo `.env` no `.gitignore`
- [ ] Tokens em produção gerenciados por secrets manager
- [ ] Tokens com validade verificada periodicamente

### Acesso e Permissões
- [ ] Acesso ao servidor restrito (SSH keys, firewall)
- [ ] Banco de dados com usuário de privilégios mínimos
- [ ] HTTPS configurado (certificado SSL válido)

### LGPD e Compliance
- [ ] Logs não contêm dados sensíveis (PII)
- [ ] Policy Guard configurado e testado
- [ ] Disclaimer legal no prompt do sistema
- [ ] Retenção de dados definida

## 📊 Observabilidade

### Logs
- [ ] Logs estruturados (JSON recomendado)
- [ ] Rotação de logs configurada
- [ ] Acesso aos logs configurado

### Métricas
- [ ] Views SQL de analytics criadas
- [ ] Dashboard de métricas implementado/planejado
- [ ] KPIs definidos (ver `docs/observability.md`)

### Alertas
- [ ] Alertas para falhas críticas definidos
- [ ] Notificações configuradas (email/Slack/etc)
- [ ] Rotina de monitoramento definida
- [ ] Responsáveis por incidentes designados

## ✅ Validação Final

### Script Automatizado
- [ ] `python scripts/ops/validate_infrastructure.py` - **Todas verificações passam**

### Testes Funcionais
- [ ] Enviar mensagem via Facebook Messenger - Resposta recebida
- [ ] Enviar mensagem via Instagram DM - Resposta recebida
- [ ] Teste de resposta de crise (CVV) - Script correto retornado
- [ ] Teste de fallback - Redirecionamento adequado
- [ ] Auditoria registrada no banco de dados

### Smoke Tests (Produção)
- [ ] Perguntas de fluxo principal funcionam (ver `implementation_plan.md`)
- [ ] Redirecionamentos funcionam
- [ ] Respostas de crise funcionam
- [ ] Fallback funciona
- [ ] Privacidade respeitada

## 📝 Documentação

### Documentação Técnica
- [ ] README.md atualizado
- [ ] Variáveis de ambiente documentadas
- [ ] Processo de deploy documentado
- [ ] Troubleshooting documentado

### Documentação Operacional
- [ ] Runbook de operação criado
- [ ] Procedimentos de contingência documentados
- [ ] Contatos de escalação definidos
- [ ] SLA/SLO definidos (se aplicável)

### Treinamento
- [ ] Equipe treinada no uso do sistema
- [ ] Acesso ao painel de observabilidade configurado
- [ ] Procedimentos de suporte documentados

## 🎯 Go-Live

### Pré-Deploy
- [ ] Todas as verificações acima completas
- [ ] Backup completo realizado
- [ ] Janela de manutenção comunicada (se aplicável)
- [ ] Rollback plan definido

### Deploy
- [ ] Aplicação deployada com sucesso
- [ ] Health check passa
- [ ] Smoke tests passam
- [ ] Logs não mostram erros críticos

### Pós-Deploy
- [ ] Monitoramento ativo por 24-48h
- [ ] Métricas dentro do esperado
- [ ] Nenhum incidente crítico
- [ ] Feedback de usuários coletado

---

## 📞 Contatos de Suporte

**PostgreSQL**: [Administrador DB]  
**Gemini**: https://ai.google.dev/  
**Meta Platform**: https://developers.facebook.com/support  
**Equipe Interna**: [Contatos]

---

**Data da Validação**: ___/___/______  
**Responsável**: _______________________  
**Ambiente**: [ ] Dev [ ] Staging [ ] Produção  
**Status**: [ ] ✅ Aprovado [ ] ⚠️ Com ressalvas [ ] ❌ Reprovado

**Observações**:
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
