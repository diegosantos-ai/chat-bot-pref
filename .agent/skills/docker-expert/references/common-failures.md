# Common Docker/Compose Failures

## `NEXO_SERVICE_KEYS is not configured`

- Symptom: Internal health endpoint fails with missing S2S keys.
- Cause: Container was created before env var existed, then only restarted.
- Fix:
  1. Recreate service: `docker compose up -d --force-recreate api`
  2. Verify env in container: `docker exec nexo-360-api /bin/sh -lc 'printenv | grep "^NEXO_SERVICE_KEYS="'`

## `Missing X-Tenant-ID`

- Symptom: `/internal/v1/health` returns `401` or `400` with missing tenant header.
- Cause: Required contextual header omitted.
- Fix:
  1. Include `X-Tenant-ID` in request headers.
  2. Re-test endpoint before changing infrastructure.

## `container name ... already in use`

- Symptom: `docker compose up` fails due to container name conflict.
- Cause: Stale container with same `container_name` exists from another stack/session.
- Fix:
  1. `docker stop <container>`
  2. `docker rm <container>`
  3. `docker compose up -d --force-recreate <service>`

## `password authentication failed for user "nexo_admin"`

- Symptom: API enters restart loop on migrations/startup.
- Cause: App DB credentials do not match running Postgres users or database.
- Fix:
  1. Inspect app env (`DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_HOST`).
  2. Inspect Postgres users/databases.
  3. Align app env or create missing role/database.

## PowerShell `curl` parsing errors

- Symptom: `-s`/`-H` flags fail with `Invoke-WebRequest` argument errors.
- Cause: `curl` is an alias to `Invoke-WebRequest` in PowerShell.
- Fix:
  1. Use `curl.exe` for cURL flags.
  2. Or use `Invoke-RestMethod -Headers @{...}` native syntax.

