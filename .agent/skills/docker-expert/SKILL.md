---
name: docker-expert
description: Diagnose and fix Docker and Docker Compose build, startup, networking, environment, and healthcheck issues. Use when users ask to debug failing containers, restart loops, health endpoint failures, env var mismatches, container name conflicts, PowerShell curl issues, or service-to-service connectivity problems.
---

# Docker Expert

## Overview

Diagnose Docker and Docker Compose failures with the smallest safe fix.
Validate each fix with executable checks and report objective evidence.

## Workflow

1. Capture the failing context.
- Record shell type, working directory, command, full error text, and target service.
- Remove prompt text from copied commands (`(venv) PS ... >`) before execution.

2. Resolve Compose configuration first.
- Run `docker compose config` to catch invalid/deprecated keys and interpolation issues.
- Confirm expected env vars for the target service.

3. Inspect runtime state.
- Run `docker compose ps` and `docker ps -a`.
- Check for restart loops, stopped dependencies, or `container name already in use`.
- Read logs with `docker logs --tail 200 <container>`.

4. Validate service internals.
- Inspect effective env vars with `docker exec <container> /bin/sh -lc 'printenv | grep ...'`.
- Run health endpoints from host and, when needed, from inside the container.
- Include all required auth/context headers before diagnosing deeper issues.

5. Apply the minimal recovery action.
- Use `docker compose restart <service>` only for transient faults.
- Use `docker compose up -d --force-recreate <service>` after env/image/command changes.
- Use `docker compose stop <service>`, `docker compose rm -f <service>`, then `up -d` for stale containers or name conflicts.
- Avoid destructive cleanup commands unless explicitly requested.

6. Prove the result.
- Re-run the failing command or health endpoint.
- Report root cause, exact fix, and verification output.

## Decision Rules

- If `restart` does not apply env changes, recreate the service.
- If errors mention missing DB role/user/database, compare app `DB_*` vars with the running Postgres users/databases.
- If PowerShell `curl` fails with `-s` or `-H`, use `curl.exe` or `Invoke-RestMethod`.
- If endpoint auth fails, verify required headers before changing containers.

## Nexo 360 Patterns

- `NEXO_SERVICE_KEYS is not configured`: container was created without env; recreate `api`.
- `Missing X-Tenant-ID` on `/internal/v1/health`: include `X-Tenant-ID` header.
- `container name already in use`: remove stale container for that name, then recreate.
- `password authentication failed for user "nexo_admin"`: align `DB_USER/DB_PASSWORD/DB_NAME` with actual Postgres or create missing role/database.

## Resources

- Use `scripts/compose-diagnose.sh` to capture compose status, logs, and key env vars for one service.
- Read `references/common-failures.md` for symptom-to-fix mappings.
- Read `references/powershell-docker-cheatsheet.md` for PowerShell command equivalents.
