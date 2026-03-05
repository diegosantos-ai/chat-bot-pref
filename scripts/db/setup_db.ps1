param(
  [string]$DbHost = "localhost",
  [int]$Port = 5432,
  [string]$User = "postgres",
  [string]$Password = "",
  [string]$DbName = "pilot_atendimento"
)

Write-Host "==> Verificando psql..."
if (-not (Get-Command psql -ErrorAction SilentlyContinue)) {
  Write-Error "psql não encontrado. Instale o PostgreSQL ou adicione o binário ao PATH."
  exit 1
}

$env:PGPASSWORD = $Password

Write-Host "==> Verificando existência do banco '$DbName'..."
$exists = psql -h $DbHost -p $Port -U $User -tAc "SELECT 1 FROM pg_database WHERE datname='${DbName}';"

if (-not $exists) {
  Write-Host "==> Criando database '$DbName'..."
  psql -h $DbHost -p $Port -U $User -c "CREATE DATABASE ${DbName};" || exit 1
} else {
  Write-Host "==> Banco '$DbName' já existe."
}

Write-Host "==> Habilitando extensão pgcrypto (gen_random_uuid)..."
psql -h $DbHost -p $Port -U $User -d $DbName -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;" || exit 1

Write-Host "==> Aplicando schema db/schema.sql..."
$schemaPath = Join-Path $PSScriptRoot "..\db\schema.sql"
psql -h $DbHost -p $Port -U $User -d $DbName -f $schemaPath || exit 1

Write-Host "==> Verificando tabelas..."
psql -h $DbHost -p $Port -U $User -d $DbName -c "\dt"

Write-Host "==> Concluído. Banco preparado com tabelas de auditoria (audit_events, rag_queries)."