# Migration: Alteração de VARCHAR para TEXT

**Data:** 2026-02-04
**Versão:** v1.2
**Status:** Aplicar no próximo deploy

## Resumo

Alteração dos campos do tipo `VARCHAR(128)` para `TEXT` nas tabelas do banco de dados para permitir maior flexibilidade no armazenamento de IDs externos das plataformas Meta (Facebook/Instagram).

## Mudanças

### Tabela: `usuarios_anonimos`

```sql
ALTER TABLE usuarios_anonimos 
ALTER COLUMN hash_usuario TYPE TEXT;
```

**Campos alterados:**
- `hash_usuario`: VARCHAR(128) → TEXT

### Tabela: `audit_events`

```sql
ALTER TABLE audit_events 
ALTER COLUMN id_sessao TYPE TEXT,
ALTER COLUMN id_mensagem_externa TYPE TEXT,
ALTER COLUMN id_thread TYPE TEXT,
ALTER COLUMN id_post TYPE TEXT,
ALTER COLUMN id_comentario TYPE TEXT,
ALTER COLUMN id_autor_plataforma TYPE TEXT;
```

**Campos alterados:**
- `id_sessao`: VARCHAR(128) → TEXT
- `id_mensagem_externa`: VARCHAR(128) → TEXT
- `id_thread`: VARCHAR(128) → TEXT
- `id_post`: VARCHAR(128) → TEXT
- `id_comentario`: VARCHAR(128) → TEXT
- `id_autor_plataforma`: VARCHAR(128) → TEXT

## Motivação

Os IDs externos das plataformas Meta (Facebook e Instagram) podem variar em tamanho e não possuem um limite fixo garantido de 128 caracteres. A mudança para TEXT:

1. **Remove restrições artificiais**: Permite armazenar IDs de qualquer tamanho
2. **Melhora compatibilidade**: IDs do Instagram e Facebook podem ser longos
3. **Simplifica manutenção**: Não precisa se preocupar com truncamento
4. **Performance equivalente**: No PostgreSQL, TEXT e VARCHAR têm performance similar

## Instruções de Deploy

### 1. Backup

Faça backup do banco antes de aplicar:
```bash
pg_dump -h localhost -U terezia -d terezia > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 2. Aplicar Migration

Conecte-se ao banco e execute:

```sql
-- Alterar tabela usuarios_anonimos
ALTER TABLE usuarios_anonimos 
ALTER COLUMN hash_usuario TYPE TEXT;

-- Alterar tabela audit_events
ALTER TABLE audit_events 
ALTER COLUMN id_sessao TYPE TEXT,
ALTER COLUMN id_mensagem_externa TYPE TEXT,
ALTER COLUMN id_thread TYPE TEXT,
ALTER COLUMN id_post TYPE TEXT,
ALTER COLUMN id_comentario TYPE TEXT,
ALTER COLUMN id_autor_plataforma TYPE TEXT;
```

Ou execute via psql:
```bash
PGPASSWORD=sua_senha psql -h localhost -U terezia -d terezia -f docs/migrations/20260204_alter_varchar_to_text.sql
```

### 3. Verificação

Verifique se as alterações foram aplicadas:
```sql
\d+ usuarios_anonimos
\d+ audit_events
```

## Rollback

Se necessário, é possível fazer rollback (com limitação de 128 caracteres):

```sql
-- Verificar se há dados maiores que 128 caracteres
SELECT COUNT(*) FROM usuarios_anonimos WHERE LENGTH(hash_usuario) > 128;
SELECT COUNT(*) FROM audit_events WHERE LENGTH(id_sessao) > 128;

-- Se não houver dados grandes, pode fazer rollback:
ALTER TABLE usuarios_anonimos 
ALTER COLUMN hash_usuario TYPE VARCHAR(128);

ALTER TABLE audit_events 
ALTER COLUMN id_sessao TYPE VARCHAR(128),
ALTER COLUMN id_mensagem_externa TYPE VARCHAR(128),
ALTER COLUMN id_thread TYPE VARCHAR(128),
ALTER COLUMN id_post TYPE VARCHAR(128),
ALTER COLUMN id_comentario TYPE VARCHAR(128),
ALTER COLUMN id_autor_plataforma TYPE VARCHAR(128);
```

## Notas

- **Não há perda de dados**: A conversão de VARCHAR para TEXT é segura e não perde dados
- **Índices mantidos**: Todos os índices existentes continuam funcionando
- **Constraints mantidas**: NOT NULL, UNIQUE e CHECK constraints são preservadas
- **FK constraints**: Não há impacto nas foreign keys existentes
