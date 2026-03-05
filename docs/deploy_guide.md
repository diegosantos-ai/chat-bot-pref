# Guia de Deploy - {bot_name}

Este guia explica como fazer o deploy do {bot_name} em produção para que o webhook fique **sempre disponível** (24/7).

## 📋 Índice

1. [Pré-requisitos](#pré-requisitos)
2. [Estrutura de Arquivos](#estrutura-de-arquivos)
3. [Opção 1: Deploy Local (Windows)](#opção-1-deploy-local-windows)
4. [Opção 2: Deploy em VPS (Linux)](#opção-2-deploy-em-vps-linux)
5. [Configuração do Domínio e HTTPS](#configuração-do-domínio-e-https)
6. [Configuração do Webhook na Meta](#configuração-do-webhook-na-meta)
7. [Testes e Validação](#testes-e-validação)
8. [Manutenção](#manutenção)

---

## Pré-requisitos

### Software Necessário
- **Docker Desktop** (Windows/Mac) ou **Docker Engine** (Linux)
- **Docker Compose** (incluído no Docker Desktop)
- **Git** (para clonar/atualizar o projeto)

### Acesso
- Acesso ao servidor onde será feito o deploy
- Acesso ao painel do Facebook Developers
- Domínio ou subdomínio configurado (para HTTPS)

### Credenciais
- Chave API do Gemini
- Tokens da API Meta (ACCESS_TOKEN/PAGE_ID/APP_SECRET por plataforma)
- Credenciais do PostgreSQL

---

## Estrutura de Arquivos

```
pilot-atendimento/
├── docker-compose.yml    # Orquestração dos containers
├── Dockerfile            # Build da imagem da API
├── Caddyfile            # Configuração do reverse proxy (HTTPS)
├── .env                  # Variáveis de ambiente (NÃO commitar!)
├── .env.prod.example     # Template para produção
├── scripts/
│   └── ops/
│       ├── deploy.sh     # Script de deploy (Linux/Mac)
│       └── deploy.ps1    # Script de deploy (Windows)
└── ...
```

---

## Opção 1: Deploy Local (Windows)

### 1.1 Instalar Docker Desktop

1. Baixe em: https://docker.com/products/docker-desktop
2. Instale e reinicie o computador
3. Abra o Docker Desktop e aguarde iniciar

### 1.2 Preparar Ambiente

```powershell
# Navegar para o diretório do projeto
cd C:\Users\santo\pilot-atendimento

# Copiar template de variáveis
Copy-Item .env.prod.example .env

# Editar .env com os valores reais (Notepad, VS Code, etc.)
code .env
```

### 1.3 Configurar .env

Edite o arquivo `.env` com os valores reais:

```env
# Valores obrigatórios
GEMINI_API_KEY=sua_chave_real
DATABASE_URL=postgresql://terezia:senha@192.168.3.12:5432/terezia
META_ACCESS_TOKEN_FACEBOOK=token_da_pagina_facebook
META_PAGE_ID_FACEBOOK=id_da_pagina_facebook
META_APP_SECRET_FACEBOOK=app_secret_facebook
META_ACCESS_TOKEN_INSTAGRAM=token_da_pagina_instagram
META_PAGE_ID_INSTAGRAM=id_da_pagina_instagram
META_APP_SECRET_INSTAGRAM=app_secret_instagram
META_WEBHOOK_VERIFY_TOKEN=seu_token_unico
```

### 1.4 Iniciar

```powershell
# Usando script de deploy
.\scripts\ops\deploy.ps1 start

# Ou manualmente
docker-compose up -d --build
```

### 1.5 Verificar

```powershell
# Status
.\scripts\ops\deploy.ps1 status

# Logs
.\scripts\ops\deploy.ps1 logs

# Testar endpoint
Invoke-WebRequest http://localhost:8000/health
```

---

## Opção 2: Deploy em VPS (Linux)

### 2.1 Preparar VPS

```bash
# Conectar via SSH
ssh usuario@ip-da-vps

# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Instalar Docker Compose
sudo apt install docker-compose-plugin -y

# Logout e login novamente para aplicar grupo docker
exit
ssh usuario@ip-da-vps
```

### 2.2 Clonar Projeto

```bash
# Clonar repositório
git clone https://github.com/seu-usuario/pilot-atendimento.git
cd pilot-atendimento

# Configurar variáveis
cp .env.prod.example .env
nano .env  # Editar com valores reais
```

### 2.3 Iniciar

```bash
# Dar permissão ao script
chmod +x scripts/ops/deploy.sh

# Iniciar
./scripts/ops/deploy.sh start
```

### 2.4 Configurar como Serviço (opcional)

Para garantir que reinicie automaticamente após reboot:

```bash
# Criar serviço systemd
sudo nano /etc/systemd/system/terezia.service
```

Conteúdo:
```ini
[Unit]
Description={bot_name} Chatbot
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/usuario/pilot-atendimento
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down

[Install]
WantedBy=multi-user.target
```

```bash
# Habilitar e iniciar
sudo systemctl enable terezia
sudo systemctl start terezia
```

---

## Configuração do Domínio e HTTPS

### Requisitos
- Domínio apontando para o IP do servidor (DNS A record)
- Portas 80 e 443 abertas no firewall

### Configurar Caddyfile

Edite o arquivo `Caddyfile`:

```caddyfile
# Substituir pelo seu domínio real
terezia.prefeitura.com.br {
    reverse_proxy terezia:8000
    
    header {
        X-Content-Type-Options nosniff
        X-Frame-Options DENY
    }
}
```

### Reiniciar para aplicar

```bash
docker-compose restart caddy
```

O Caddy obtém certificado SSL automaticamente via Let's Encrypt!

---

## Configuração do Webhook na Meta

### 1. Acessar Facebook Developers
1. Vá para https://developers.facebook.com
2. Selecione seu App
3. No menu lateral: **Webhooks** ou **Messenger > Settings**

### 2. Configurar Callback URL

- **Callback URL**: `https://terezia.seudominio.com.br/webhook/meta`
- **Verify Token**: O mesmo valor de `META_WEBHOOK_VERIFY_TOKEN` (ou `META_WEBHOOK_VERIFY_TOKEN_FACEBOOK` / `META_WEBHOOK_VERIFY_TOKEN_INSTAGRAM`) no .env

### 3. Selecionar Eventos

Marque os seguintes campos:
- [x] `messages`
- [x] `messaging_postbacks`
- [x] `feed` (para comentários)

### 4. Verificar

Clique em "Verify and Save". Se tudo estiver correto, aparecerá ✓ verde.

---

## Testes e Validação

### Teste 1: Health Check
```bash
curl https://terezia.seudominio.com.br/health
# Esperado: {"status": "ok", ...}
```

### Teste 2: Webhook Verification
```bash
curl "https://terezia.seudominio.com.br/webhook/meta?hub.mode=subscribe&hub.verify_token=SEU_TOKEN&hub.challenge=teste123"
# Esperado: teste123
```

### Teste 3: Enviar Mensagem
Envie uma mensagem para a página do Facebook via Messenger e verifique:
- Logs: `docker-compose logs -f terezia`
- Resposta recebida no chat

### Teste 4: Verificar Auditoria
```sql
-- No PostgreSQL
SELECT * FROM audit_events ORDER BY created_at DESC LIMIT 10;
```

---

## Manutenção

### Atualizar Código
```bash
git pull origin main
./scripts/ops/deploy.sh update
```

### Ver Logs
```bash
./scripts/ops/deploy.sh logs
```

### Reiniciar
```bash
./scripts/ops/deploy.sh restart
```

### Parar
```bash
./scripts/ops/deploy.sh stop
```

### Backup ChromaDB
```bash
# Fazer backup do diretório de dados
tar -czvf backup_chroma_$(date +%Y%m%d).tar.gz chroma_data/
```

---

## Troubleshooting

### Container não inicia
```bash
docker-compose logs terezia
# Verificar mensagens de erro
```

### Webhook não verifica
1. Verificar se URL está acessível: `curl https://sua-url/health`
2. Verificar token: deve ser idêntico ao configurado no .env
3. Verificar logs: `docker-compose logs -f`

### Erro de conexão com PostgreSQL
1. Verificar se PostgreSQL está acessível do container:
   ```bash
   docker exec -it terezia-api bash
   ping localhost
   ```
2. Verificar firewall do PostgreSQL

### Certificado SSL não funciona
1. Verificar se domínio aponta para IP correto: `nslookup seudominio.com`
2. Verificar se portas 80/443 estão abertas
3. Logs do Caddy: `docker-compose logs caddy`

---

## Contatos

- **Documentação Meta**: https://developers.facebook.com/docs/messenger-platform
- **Docker**: https://docs.docker.com
- **Caddy**: https://caddyserver.com/docs
