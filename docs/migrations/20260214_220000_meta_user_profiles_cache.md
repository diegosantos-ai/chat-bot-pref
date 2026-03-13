# Migração: Cache de Perfis Meta (Instagram/Facebook)

**Data:** 2026-02-14  
**Autor:** Agente {bot_name}  
**Versão:** v0.8.1  
**Status:** Pronto para Deploy

## Resumo

Implementa um sistema de cache para armazenar perfis de usuários do Instagram/Facebook, permitindo identificar o remetente em emails de escalation sem fazer chamadas repetidas à API da Meta.

## Problema

Quando ocorria um escalation (elevação para atendente humano), o email enviado continha apenas o ID da sessão, dificultando o contato direto com o cidadão:
- "Contato do Usuário: Session: 886304507365682"
- Não mostrava @username do Instagram
- Dificultava resposta direta pela equipe

## Solução

Sistema de cache que:
1. Armazena username, nome e foto de perfil no PostgreSQL
2. Busca na API da Meta **apenas quando necessário** (durante escalation)
3. TTL de 30 dias para atualização automática
4. Fallback para ID numérico se API falhar

## Arquivos Criados/Modificados

### Novos Arquivos

```
db/migrations/20260214_220000_add_meta_user_profiles_cache.sql
app/models/meta_user_profile.py
app/repositories/meta_user_profile_repository.py
docs/migrations/20260214_220000_meta_user_profiles_cache.md
```

### Arquivos Modificados

```
app/integrations/meta/client.py      # + get_user_profile()
app/services/mailer.py               # + username no email
app/orchestrator/service.py          # + busca de perfil no escalate
```

## Schema do Banco

### Nova Tabela: `meta_user_profiles`

```sql
CREATE TABLE meta_user_profiles (
    id SERIAL PRIMARY KEY,
    platform_user_id VARCHAR(50) NOT NULL,
    platform VARCHAR(20) NOT NULL CHECK (platform IN ('instagram', 'facebook')),
    username VARCHAR(100),
    name VARCHAR(200),
    profile_picture_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform_user_id, platform)
);
```

**Índices:**
- `idx_meta_user_profiles_lookup` - Busca por platform_user_id + platform
- `idx_meta_user_profiles_updated` - Limpeza de entradas antigas

## Fluxo de Funcionamento

```
1. Usuário envia mensagem
   ↓
2. {bot_name} processa normalmente
   ↓
3. Se precisar ESCALAR para humano:
   ↓
4. Busca no cache PostgreSQL:
   ├── Se encontrar (atualizado < 30 dias)
   │   └── Usa username do cache ✓
   └── Se não encontrar ou expirado:
       ↓
5. Chama API Meta: GET /{user_id}?fields=username,name
       ↓
6. Salva no cache PostgreSQL
       ↓
7. Envia email com @username
```

## Configuração Necessária

### 1. Aplicar Migration SQL

```bash
psql -d pilot_atendimento -f db/migrations/20260214_220000_add_meta_user_profiles_cache.sql
```

Ou via script Python:
```python
python scripts/db/executar_migrations.py
```

### 2. Permissões na Meta App

A aplicação precisa ter permissão `instagram_basic` para ler perfis.

**Como verificar:**
1. Acesse: https://developers.facebook.com/apps/{APP_ID}/instagram-basic-display/basic-display/
2. Verifique se tem a permissão "instagram_basic"
3. Se não tiver, adicione e reautorize os tokens

**Se não tiver permissão:** O sistema funciona normalmente, mas usa o ID numérico como fallback.

### 3. Variáveis de Ambiente

Nenhuma variável nova necessária. Usa as existentes:
- `DATABASE_URL` - Para conexão com PostgreSQL
- `META_ACCESS_TOKEN_INSTAGRAM` - Para chamadas à API
- `META_ACCESS_TOKEN_FACEBOOK` - Para chamadas à API

## Teste de Funcionamento

### Teste 1: Escalation com usuário novo

```bash
# Enviar mensagem que vai dar escalation
curl -X POST "http://localhost:8000/api/chat/simple" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "pergunta muito específica que não está na base",
    "channel": "instagram_dm",
    "surface_type": "INBOX",
    "session_id": "886304507365682"
  }'
```

**Verificar:**
1. Log deve mostrar: "Perfil não encontrado no cache, buscando na API"
2. Email deve conter @username do Instagram
3. Banco deve ter novo registro na tabela `meta_user_profiles`

### Teste 2: Escalation com usuário cacheado

```bash
# Enviar segunda mensagem do mesmo usuário
curl -X POST "http://localhost:8000/api/chat/simple" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "outra pergunta difícil",
    "channel": "instagram_dm",
    "surface_type": "INBOX",
    "session_id": "886304507365682"
  }'
```

**Verificar:**
1. Log deve mostrar: "Perfil cacheado encontrado"
2. Não deve chamar API da Meta
3. Email enviado rapidamente

### Teste 3: Verificar cache no banco

```sql
-- Listar perfis cacheados
SELECT platform_user_id, platform, username, name, updated_at
FROM meta_user_profiles
ORDER BY updated_at DESC
LIMIT 10;
```

## Formato do Email de Escalation (Novo)

**Antes:**
```
Contato do Usuário: Session: 886304507365682
```

**Depois:**
```
Informações do Usuário
• Contato: @prefeitura_sto (Prefeitura de {client_name})
• Plataforma: INSTAGRAM
• ID Interno: 886304507365682

Para responder via Instagram/Facebook, procure pelo usuário: @prefeitura_sto
```

## Performance

- **Primeira vez:** +100-200ms (chamada à API Meta)
- **Cache hit:** +5ms (consulta PostgreSQL)
- **Memória:** Tabela pequena (< 1MB para 1000 usuários)
- **TTL:** 30 dias (configurável no código)

## Rollback

Se necessário reverter:

```sql
-- Remove a tabela
DROP TABLE IF EXISTS meta_user_profiles;

-- Remove a função do trigger
DROP FUNCTION IF EXISTS update_updated_at_column();
```

## Troubleshooting

### Erro: "Sem permissão para buscar perfil"

**Causa:** App não tem permissão `instagram_basic`  
**Solução:** 
1. Adicionar permissão no Facebook Developers
2. Gerar novo token de acesso
3. Reautorizar a aplicação

### Erro: "Usuário não encontrado na API"

**Causa:** Usuário pode ter bloqueado a app ou perfil privado  
**Solução:** Sistema usa ID numérico como fallback automaticamente

### Erro: "Could not connect to PostgreSQL"

**Causa:** Tabela não foi criada  
**Solução:** Executar migration SQL

## Referências

- [Instagram Basic Display API](https://developers.facebook.com/docs/instagram-basic-display-api)
- [Instagram Graph API - User Endpoint](https://developers.facebook.com/docs/instagram-api/reference/ig-user)
- [Meta App Permissions](https://developers.facebook.com/docs/permissions-reference/)
