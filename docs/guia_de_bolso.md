# Guia de Bolso (Windows) - {bot_name} / pilot-atendimento

Este guia ajuda a **rodar e acessar** a API + observabilidade (DB/Grafana) mesmo para quem nunca viu o projeto.

## 0) Antes de comecar (1 vez)

### 0.1 Requisitos
- Windows 10/11
- Python 3.11+ instalado
- Git instalado (para clonar/atualizar)
- Acesso ao PostgreSQL (host/porta/usuario/senha) usado pelo projeto

### 0.2 Abrir o projeto
No PowerShell:
```powershell
cd C:\Users\santo\pilot-atendimento
```

### 0.3 Criar/usar o ambiente virtual do projeto
O projeto usa `.venv` (pasta na raiz).

Se **ainda nao existe**:
```powershell
python -m venv .venv
```

Ativar:
```powershell
.\.venv\Scripts\Activate.ps1
```

Instalar dependencias:
```powershell
python -m pip install -r requirements.txt
```

### 0.4 Configurar variaveis de ambiente
Copie o exemplo e preencha:
```powershell
Copy-Item .env.example .env
notepad .env
```

Minimo recomendado para rodar local:
- `DATABASE_URL=...`
- `GEMINI_API_KEY=...` (se a LLM estiver ativa no pipeline)
- `APP_PORT=8000` (padrao)

### 0.5 Validar infraestrutura (recomendado)
```powershell
python scripts\validate_infrastructure.py
```

## 1) Subir o sistema (todo dia)

### 1.1 Banco de dados
Garanta que o PostgreSQL esta online e acessivel.

Teste de rede (exemplo):
```powershell
Test-NetConnection localhost -Port 5432
```

### 1.2 Subir a API
Forma mais simples:
```powershell
scripts\run_api.ps1 -Reload
```

Se quiser manual:
```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 1.3 Conferir se esta OK
- Health: `http://localhost:8000/health`
- Swagger: `http://localhost:8000/docs`

## 2) Gerar dados (auditoria) com smoke tests

Isso faz chamadas reais na API e verifica que cada teste gerou linhas em `audit_events`.

```powershell
python scripts\smoke_tests_prod.py --base-url http://localhost:8000
```

## 3) Observabilidade (Grafana)

### 3.1 Acessar
- URL: `http://localhost:3001/`

### 3.2 Datasource (Postgres)
No Grafana:
- Connections -> Data sources -> Postgres
- Aponte para o mesmo Postgres do `DATABASE_URL` (ou um replica de leitura)

### 3.3 Views de analytics (se necessario)
As views sao criadas a partir de `analytics/v1/views.sql`.

Execute:
```powershell
python scripts\create_views.py
```

### 3.4 Dashboard
Importe o JSON do dashboard:
- Arquivo: `grafana/dashboard_terezia.json`

## 4) Consultar dados no banco (sem psql)

Se voce nao tem `psql` instalado, da para consultar pelo Python (asyncpg).

Contar auditoria:
```powershell
@'
import os, asyncio
import asyncpg
from dotenv import load_dotenv
load_dotenv(".env")

async def main():
    conn = await asyncpg.connect(dsn=os.environ["DATABASE_URL"])
    try:
        n = await conn.fetchval("select count(*) from audit_events")
        print("audit_events =", n)
    finally:
        await conn.close()

asyncio.run(main())
'@ | python -
```

## 5) Parar a API

```powershell
scripts\stop_api.ps1
```

## 6) Backups (Postgres + ChromaDB)

Backup manual (recomendado antes de mudanças):
```powershell
python scripts\backup_postgres.py --gzip --verify
python scripts\backup_chroma.py
```

Saída:
- `artifacts\backups\postgres\...`
- `artifacts\backups\chroma\...`

## 7) Problemas comuns (check rapido)

### Porta 8000 em uso
```powershell
Get-NetTCPConnection -LocalPort 8000 -State Listen
scripts\stop_api.ps1
```

### Grafana nao loga / erro 500
Em geral e lock do SQLite ou servico quebrado. Ver `docs/runbook.md` e o log:
`D:\Programas\grafana\data\log\grafana.log`.

### "psql nao e reconhecido"
Nao tem o cliente instalado. Use a secao **4)** (consulta via Python) ou instale o PostgreSQL client tools.
