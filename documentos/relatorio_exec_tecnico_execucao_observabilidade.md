# Relatorio Executivo e Tecnico - Execucao/Observabilidade

Data: 2026-01-19  
Projeto: {bot_name} (pilot-atendimento)

## 1) Resumo Executivo

### Problema
- Execucao local inconsistente (principalmente por divergencia de portas 8000 vs 8001 em scripts/docs/testes).
- Grafana com falha de login (`Internal Server Error`), impedindo a validacao de dashboards.

### O que foi feito
- Padronizacao da porta/host da API via variaveis `APP_HOST` e `APP_PORT` (padrao `0.0.0.0:8000`), aplicada ao entrypoint e scripts de suporte.
- Criacao de scripts simples para iniciar/parar a API no Windows/PowerShell.
- Ajuste de scripts de teste/smoke e webhook para lerem `APP_PORT`/`APP_HOST`.
- Diagnostico do Grafana: o erro de login decorre de lock no SQLite (`database is locked` / `cannot start a transaction within a transaction`).

### Resultado
- Execucao da API ficou previsivel: a mesma configuracao controla todos os scripts e testes.
- Smoke tests e simulacoes passam a apontar para a porta configurada.
- Causa raiz do erro do Grafana foi identificada; a correcao operacional depende de parar o servico (requer permissao de administrador).

## 2) Resumo Tecnico (Mudancas no Repo)

### Padronizacao de porta/host
- `app/settings.py`: adicionados `APP_HOST` e `APP_PORT` (padrao `0.0.0.0:8000`).
- `app/main.py`: `uvicorn.run(...)` passou a usar `settings.APP_HOST` e `settings.APP_PORT`.
- `.env.example`: inclui `APP_HOST` e `APP_PORT`.

### Scripts atualizados
- `scripts/start_tunnel.py`: usa `APP_PORT` ao criar o tunel (ngrok) (remove dependencia fixa em 8001).
- `scripts/test_webhook_local.py`: usa `APP_HOST`/`APP_PORT` para montar a URL do webhook.
- `scripts/simulate_webhook.py`: usa `APP_HOST`/`APP_PORT` para montar a URL do webhook.
- `scripts/debug_verify.py`: mensagens de erro usam `APP_PORT`.
- `scripts/ops/validate_infrastructure.py`: instrucoes/outputs atualizados para porta padrao (ou `APP_PORT`).
- `scripts/smoke_tests_prod.py`: selecao automatica de base URL passa a usar `APP_HOST`/`APP_PORT` (ou `SMOKE_BASE_URL` / `--base-url`).

### Testes
- `tests/test_api.py`: base URL passou a ser configuravel via `API_BASE_URL` (fallback para `APP_HOST`/`APP_PORT`).

### Scripts novos (Windows)
- `scripts/run_api.ps1`: inicia a API lendo `APP_HOST`/`APP_PORT` do `.env` (opcional `-Reload`).
- `scripts/stop_api.ps1`: encerra o processo que estiver ouvindo a `APP_PORT` (por PID). Se falhar, requer PowerShell como Admin.

### Docs atualizados (execucao padrao 8000)
- `README.md`
- `docs/QUICKSTART_AGENT.md`
- `docs/infrastructure_validation.md`
- `INFRASTRUCTURE_CHECKLIST.md`
- `docs/runbook.md`

## 3) Diagnostico do Grafana (Nao e mudanca de codigo)

### Sintoma
- Login no `http://localhost:3001` falha com `Internal Server Error`.

### Evidencia (logs)
- Arquivo: `D:\Programas\grafana\data\log\grafana.log`
- Erros recorrentes:
  - `database is locked (SQLITE_BUSY)`
  - `SQL logic error: cannot start a transaction within a transaction`

### Causa provavel
- SQLite travado por concorrencia/instancia duplicada ou encerramento incorreto (presenca de `D:\Programas\grafana\data\grafana.db-journal`).

### Correcao operacional recomendada (requer Admin)
1) Parar o servico do Grafana e processos associados.
2) Remover `grafana.db-journal`.
3) Subir o servico novamente.

Comandos (PowerShell como Administrador):
```powershell
Stop-Service Grafana
Get-Process | Where-Object { $_.ProcessName -like '*grafana*' } | Stop-Process -Force
Remove-Item "D:\Programas\grafana\data\grafana.db-journal"
Start-Service Grafana
```

Verificacao:
```powershell
Get-Content -Tail 60 "D:\Programas\grafana\data\log\grafana.log"
```

## 4) Como Conferir (Passo a passo)

### 4.1 Subir a API
```powershell
scripts\run_api.ps1 -Reload
```

Verificar:
- `GET http://localhost:8000/health` (ou `APP_PORT`)
- `GET http://localhost:8000/docs`

### 4.2 Rodar smoke tests (gera auditoria)
```powershell
python scripts\smoke_tests_prod.py --base-url http://localhost:8000
```

### 4.3 Parar a API
```powershell
scripts\stop_api.ps1
```

### 4.4 Backups (Postgres + ChromaDB)
```powershell
python scripts\backup_postgres.py --gzip --verify
python scripts\backup_chroma.py
```

Agendamento (Windows Task Scheduler):
```powershell
schtasks /Query /TN "{bot_name}-Backup" /V /FO LIST
```

## 5) Lista de arquivos alterados (neste lote)
- `INFRASTRUCTURE_CHECKLIST.md`
- `README.md`
- `app/main.py`
- `app/settings.py`
- `docs/QUICKSTART_AGENT.md`
- `docs/infrastructure_validation.md`
- `docs/runbook.md`
- `scripts/debug_verify.py`
- `scripts/simulate_webhook.py`
- `scripts/smoke_tests_prod.py`
- `scripts/start_tunnel.py`
- `scripts/test_webhook_local.py`
 - `scripts/ops/validate_infrastructure.py`
- `tests/test_api.py`
- `scripts/run_api.ps1` (novo)
- `scripts/stop_api.ps1` (novo)
