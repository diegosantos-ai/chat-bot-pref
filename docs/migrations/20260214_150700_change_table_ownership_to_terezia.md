# 20260214_150700_change_table_ownership_to_terezia

## Data: 2026-02-14 15:07:00

## Descrição
Alteração do ownership de todas as tabelas do banco de dados `terezia` do usuário `postgres` para o usuário `terezia`.

## Motivação
Padronizar o acesso ao banco de dados para usar o usuário específico da aplicação (`terezia`) ao invés do superusuário (`postgres`), seguindo boas práticas de segurança.

## Tabelas Alteradas
- admin_users
- audit_events
- boost_configs
- conversas
- rag_documents
- rag_queries
- scrap_configs
- scrap_imported_items
- scrap_results
- scrap_schedules
- usuarios_anonimos

## Total: 11 tabelas

## Comando Executado
```sql
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN 
        SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tableowner = 'postgres'
    LOOP
        EXECUTE format('ALTER TABLE %I.%I OWNER TO terezia', 'public', r.tablename);
        RAISE NOTICE 'Changed ownership of table % to terezia', r.tablename;
    END LOOP;
END $$;
```

## Aplicação no Servidor
Este script foi executado diretamente no servidor via psql:
```bash
PGPASSWORD=24052014 psql -h localhost -p 5432 -U postgres -d terezia
```

## Verificação
Após a execução, todas as 11 tabelas agora têm owner = terezia.
