# Setup do Banco de Dados (PostgreSQL)

Este projeto usa PostgreSQL para auditoria. O schema está definido no AGENTS.md e pode ser aplicado via scripts.

## Pré-requisitos
- PostgreSQL 15+ instalado (com `psql` no PATH)
- Credenciais do banco (host, porta, usuário, senha)
- `.env` configurado (copie `.env.example` para `.env` e ajuste `DATABASE_URL`)

## Inicialização rápida (Windows/PowerShell)
1. Abra o PowerShell na pasta do projeto
2. Execute o script de setup:
   
   Exemplo:
    `./scripts/setup_db.ps1 -Host localhost -Port 5432 -User terezia -Password "pandora" -DbName terezia`

O script irá:
- Criar o database (se não existir)
- Habilitar `pgcrypto` (necessário para `gen_random_uuid()`)
- Aplicar o schema de `db/schema.sql`
- Listar as tabelas criadas

## Verificação
- Tabelas esperadas: `audit_events`, `rag_queries`, `usuarios_anonimos`, `conversas`
- Rode as consultas de analytics em `analytics/v1/queries.sql`

## Dicas
- Se preferir GUI, use pgAdmin/DBeaver. Crie a conexão e importe `db/schema.sql`.
- O `DATABASE_URL` do `.env` deve apontar para o mesmo host/porta/DB acima.
