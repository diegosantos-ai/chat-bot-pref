# Migration 20260126 — Add audit schema (v1.1)

Resumo
------
Esta migração adiciona o schema relacional esperado pela aplicação v1.1:
- cria ENUMs necessários
- cria tabela `usuarios_anonimos` (se ausente)
- altera `audit_events` existente adicionando colunas esperadas pelo código
- cria `rag_queries` e `conversas` (se ausentes)
- adiciona índices para consultas comuns

Riscos
-----
- A tabela `audit_events` atual no banco pode conter dados antigos em formato JSONB (coluna `data`). A migração é não-destrutiva: apenas adiciona colunas.
- A criação de índice único em `id_mensagem_externa` pode falhar se existirem duplicatas. Verifique e deduplique se necessário.
- É obrigatório ter privilégios suficientes (usuário superuser ou owner das tabelas). O script pressupõe acesso para criar tipos e alterar tabelas.

Backup (obrigatório)
--------------------
Faça backup completo antes de executar:

PGPASSWORD=<postgres-password> pg_dump -Fc -h localhost -U postgres -d terezia -f /tmp/terezia_pre_migration.dump

Aplicação do migration
----------------------
1. Faça backup (comando acima).
2. Como usuário com privilégios (postgres), execute:

   PGPASSWORD=<postgres-password> psql "postgresql://postgres:<password>@localhost:5432/terezia" -f docs/migrations/20260126_terezia_add_audit_schema.sql

3. Verifique o resultado:

   PGPASSWORD=<postgres-password> psql "postgresql://postgres:<password>@localhost:5432/terezia" -c "\d+ audit_events"
   PGPASSWORD=<postgres-password> psql "postgresql://postgres:<password>@localhost:5432/terezia" -c "SELECT tablename FROM pg_tables WHERE tablename IN ('rag_queries','conversas','usuarios_anonimos');"

4. Reinicie a aplicação:

   sudo systemctl restart terezia-api
   sudo journalctl -u terezia-api -f

Rollback (simples)
------------------
Remover as colunas adicionadas não é trivial sem perder dados. Melhor restaurar a partir do backup:

PGPASSWORD=<postgres-password> pg_restore -h localhost -U postgres -d terezia /tmp/terezia_pre_migration.dump

Notas adicionais
----------------
- Depois da migração, se quiser migrar dados do antigo formato JSONB (`data` coluna) para as novas colunas, eu posso gerar scripts `UPDATE` para extrair campos (ex.: session_id, id_mensagem_externa) a partir do JSON.
- Registre este arquivo em `docs/migrations/` (feito).

Execução por mim
----------------
Você me deu credenciais para o usuário postgres; se quiser que eu execute, confirme e eu rodarei:
1) backup (pg_dump) — salvo em `/tmp`
2) aplicação do migration SQL
3) reinício do serviço e verificação de logs

Se aprovar, responda "execute".
