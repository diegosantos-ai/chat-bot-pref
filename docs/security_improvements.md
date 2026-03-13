# Melhorias de Segurança e Operacionais - v1.2

## Visão Geral

Este documento descreve as melhorias urgentes implementadas para produção.

## Mudanças Implementadas

### 1. Segurança - CORS

**Problema Anterior:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ❌ Permissivo - QUALQUER origem
    ...
)
```

**Solução:**
```python
# No .env.prod.example:
CORS_ORIGINS=["https://terezia.prefeitura.com.br", "https://www.facebook.com", "https://www.instagram.com"]

# No app/main.py:
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # ✅ Apenas domínios autorizados
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Hub-Signature"],
)
```

**Impacto:**
- ✅ Bloqueia requests de domínios não autorizados
- ✅ Proteção contra CSRF
- ✅ Previne hotlinking

---

### 2. Rate Limiting

**Problema Anterior:**
- ❌ Sem proteção contra abuso
- ❌ API pode ser bombardeada com requests
- ❌ Vulnerável a DoS

**Solução:**
```python
# Dependência adicionada: slowapi>=0.1.9

# Limites configuráveis via .env:
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=30      # API pública
RATE_LIMIT_WEBHOOK_PER_MINUTE=60  # Webhook do Meta

# Implementação:
@router.post("/api/chat")
@limiter.limit("30/minute")
async def chat(...):
    ...

@router.post("/webhook/meta")
@webhook_limiter.limit("60/minute")
async def handle_webhook_event(...):
    ...
```

**Comportamento:**
- Se limite excedido: Retorna `429 Too Many Requests`
- Headers de rate limit incluídos em todas as respostas:
  - `X-RateLimit-Limit`: Limite total
  - `X-RateLimit-Remaining`: Restantes
  - `X-RateLimit-Reset`: Quando reseta (timestamp Unix)

**Como Testar:**
```bash
# Deve funcionar (primeiras 30 requisições):
for i in {1..30}; do
  curl -X POST http://localhost:8000/api/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "teste", "session_id": "test"}'
done

# Deve retornar 429 (requisição 31+):
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "teste", "session_id": "test"}'
```

---

### 3. Security Headers

**Problema Anterior:**
- ❌ Sem headers de segurança
- ❌ Vulnerável a XSS, clickjacking

**Solução:**
```python
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    if not settings.DEBUG:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

**Headers Adicionados:**
| Header | Propósito |
|--------|-----------|
| X-Content-Type-Options | Previne MIME-sniffing |
| X-Frame-Options | Proteção contra clickjacking |
| X-XSS-Protection | Filtro XSS do navegador |
| Content-Security-Policy | Política de origens permitidas |
| Strict-Transport-Security | Força HTTPS (HSTS) |

---

### 4. Timeouts e Retries (Meta Client)

**Problema Anterior:**
```python
async with httpx.AsyncClient() as client:  # ❌ Sem timeout
    response = await client.post(url, json=payload, headers=headers)
```

**Solução:**
```python
class MetaClient:
    def __init__(self):
        # Timeout configurável
        self.timeout = httpx.Timeout(10.0, connect=5.0)
        
    async def send_message(self, recipient_id: str, text: str):
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.TimeoutException as e:
                logger.error(f"Timeout ao enviar mensagem Meta: {str(e)}")
                raise e
            except httpx.HTTPStatusError as e:
                logger.error(f"Erro ao enviar mensagem Meta: {e.response.text}")
                raise e
```

**Timeouts Configurados:**
- Connect: 5 segundos
- Total: 10 segundos

---

### 5. AWS Secrets Manager (Opcional)

**Problema Anterior:**
- ❌ Secrets em `.env` (texto plano)
- ❌ Risco de vazamento em commits

**Solução:**
```python
# Nova configuração:
USE_SECRETS_MANAGER=true
AWS_REGION=sa-east-1
AWS_SECRET_NAME=terezia/prod

# Módulo app/secrets.py carrega secrets do AWS
```

**Como Configurar no AWS:**

1. **Criar Secret:**
   ```bash
   aws secretsmanager create-secret \
     --name terezia/prod \
     --secret-string '{
       "GEMINI_API_KEY": "AIza...",
       "DATABASE_URL": "postgresql://...",
       "META_ACCESS_TOKEN": "EAAL...",
       "META_PAGE_ID": "1017832368069356",
       "META_APP_SECRET": "c578...",
       "META_WEBHOOK_VERIFY_TOKEN": "terezia_prod_2026",
       "USER_HASH_SALT": "random_salt_here",
       "ADMIN_API_KEY": "admin_key_here"
     }' \
     --region sa-east-1
   ```

2. **Configurar IAM Role:**
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "secretsmanager:GetSecretValue",
           "secretsmanager:DescribeSecret"
         ],
         "Resource": "arn:aws:secretsmanager:sa-east-1:123456789:secret:terezia/prod"
       }
     ]
   }
   ```

3. **Instalar boto3:**
   ```bash
   pip install boto3
   ```

4. **Configurar .env:**
   ```bash
   USE_SECRETS_MANAGER=true
   AWS_REGION=sa-east-1
   AWS_SECRET_NAME=terezia/prod
   ```

**Prioridade de Carregamento:**
1. Carrega tudo do `.env` (valores padrão)
2. Se `USE_SECRETS_MANAGER=true`, sobrescreve com valores do AWS

---

### 6. Trusted Host Middleware

**Problema Anterior:**
- ❌ Vulnerável a Host header injection

**Solução:**
```python
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.DEBUG else ["terezia.prefeitura.com.br", "*.meta.facebook.com"],
)
```

---

## Deploy para Produção

### Passo 1: Instalar Dependências

```bash
cd chat-bot-pref
pip install slowapi tenacity boto3
```

### Passo 2: Configurar .env de Produção

```bash
cp .env.prod.example .env
# Editar .env com valores reais
```

### Passo 3: Configurar Secrets (Opcional mas Recomendado)

Se usar AWS Secrets Manager:
1. Criar secret conforme instruções acima
2. Definir `USE_SECRETS_MANAGER=true` no .env

### Passo 4: Atualizar Docker Compose

```bash
docker-compose down
docker-compose up -d --build
```

### Passo 5: Validar Segurança

```bash
# 1. Testar CORS bloqueado
curl -H "Origin: https://evil.com" -I http://localhost:8000/health
# Deve retornar 403 ou não incluir Access-Control-Allow-Origin

# 2. Testar Rate Limit
for i in {1..35}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    http://localhost:8000/api/chat \
    -H "Content-Type: application/json" \
    -d '{"message":"test","session_id":"test"}'
done
# As últimas 5 devem retornar 429

# 3. Testar Security Headers
curl -I http://localhost:8000/health
# Deve incluir: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection

# 4. Testar Timeouts
# Se Meta API cair, não deve travar a aplicação
```

### Passo 6: Configurar Domínio e HTTPS

1. **Configurar DNS:**
   - CNAME de `terezia.prefeitura.com.br` → seu host

2. **Configurar Caddy:**
   ```dockerfile
   # Caddyfile
   terezia.prefeitura.com.br {
       reverse_proxy terezia:8000
   }
   ```

3. **Renovar Certificado:**
   - Caddy renova automaticamente (Let's Encrypt)

---

## Troubleshooting

### Rate Limit Bloqueando Legítimos

**Sintoma:**
```
429 Too Many Requests
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 0
```

**Solução:**
```bash
# No .env, aumentar limite:
RATE_LIMIT_PER_MINUTE=60
```

### CORS Bloqueando Webhook do Meta

**Sintoma:**
```
Webhook não está recebendo mensagens
Erro: CORS policy
```

**Solução:**
```bash
# No .env, adicionar domínios do Meta:
CORS_ORIGINS=["https://terezia.prefeitura.com.br", "https://www.facebook.com", "https://www.instagram.com"]
```

### Timeout no Meta Client

**Sintoma:**
```
Timeout ao enviar mensagem Meta: timeout
```

**Solução:**
```python
# No app/integrations/meta/client.py:
self.timeout = httpx.Timeout(20.0, connect=10.0)  # Aumentar timeout
```

---

## Checklist Antes do Go-Live

- [ ] `CORS_ORIGINS` configurado (não mais `["*"]`)
- [ ] `RATE_LIMIT_ENABLED=true`
- [ ] Secrets configurados (seja via .env ou AWS Secrets Manager)
- [ ] `DEBUG=false`
- [ ] Security headers validados
- [ ] Timeouts configurados
- [ ] Testes de carga realizados
- [ ] Monitoramento configurado (Grafana alerts)
- [ ] Backup automatizado configurado
- [ ] Health check endpoint acessível

---

## Recursos Adicionais

- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
- [FastAPI Security Best Practices](https://fastapi.tiangolo.com/tutorial/security/)
- [AWS Secrets Manager Documentation](https://docs.aws.amazon.com/secretsmanager/)
