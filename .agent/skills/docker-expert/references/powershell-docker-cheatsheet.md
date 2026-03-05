# PowerShell Docker Cheatsheet

## Compose state

- List services: `docker compose ps`
- Recreate one service: `docker compose up -d --force-recreate api`
- Tail logs: `docker logs --tail 200 nexo-360-api`

## Health checks

- Public health:
  `Invoke-RestMethod -Uri "http://localhost:8090/health"`

- Internal health (with required headers):
  `Invoke-RestMethod -Uri "http://localhost:8090/internal/v1/health" -Headers @{ "X-Nexo-Service-Key"="service-key-1"; "X-Nexo-Service-Name"="test"; "X-Tenant-ID"="00000000-0000-0000-0000-000000000001" }`

## cURL behavior in PowerShell

- Use real cURL binary:
  `curl.exe -s -H "X-Nexo-Service-Key: service-key-1" -H "X-Nexo-Service-Name: test" -H "X-Tenant-ID: 00000000-0000-0000-0000-000000000001" "http://localhost:8090/internal/v1/health"`

- Avoid pasting terminal prompt text (`(venv) PS ... >`) before command.

