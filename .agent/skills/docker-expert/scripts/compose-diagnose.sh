#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  compose-diagnose.sh [service]

Description:
  Print a quick diagnostic snapshot for Docker Compose.
  If [service] is provided, print container env keys and tail logs for that service.

Optional environment variables:
  TAIL_LINES      Number of log lines to print (default: 120)
  CHECK_ENV_KEYS  Comma-separated env keys to inspect inside container
                  (example: DB_USER,DB_NAME,NEXO_SERVICE_KEYS)
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

SERVICE="${1:-}"
TAIL_LINES="${TAIL_LINES:-120}"
CHECK_ENV_KEYS="${CHECK_ENV_KEYS:-}"

section() {
  printf "\n=== %s ===\n" "$1"
}

section "Versions"
docker --version || true
docker compose version || true

section "Compose Services"
docker compose config --services || true

section "Compose Status"
docker compose ps || true

if [[ -z "${SERVICE}" ]]; then
  section "Compose Status (all)"
  docker compose ps -a || true
  exit 0
fi

section "Service Container ID"
CONTAINER_ID="$(docker compose ps -q "${SERVICE}" || true)"
if [[ -z "${CONTAINER_ID}" ]]; then
  echo "Service '${SERVICE}' has no running container."
  docker compose ps -a "${SERVICE}" || true
  exit 0
fi

CONTAINER_NAME="$(docker inspect -f '{{.Name}}' "${CONTAINER_ID}" | sed 's#^/##')"
echo "Service: ${SERVICE}"
echo "Container ID: ${CONTAINER_ID}"
echo "Container Name: ${CONTAINER_NAME}"

if [[ -n "${CHECK_ENV_KEYS}" ]]; then
  section "Selected Environment Keys"
  IFS=',' read -r -a KEYS <<<"${CHECK_ENV_KEYS}"
  for key in "${KEYS[@]}"; do
    key_trimmed="$(echo "${key}" | xargs)"
    if [[ -z "${key_trimmed}" ]]; then
      continue
    fi
    value="$(docker exec "${CONTAINER_NAME}" /bin/sh -lc "printenv '${key_trimmed}'" || true)"
    if [[ -n "${value}" ]]; then
      printf "%s=%s\n" "${key_trimmed}" "${value}"
    else
      printf "%s=<missing>\n" "${key_trimmed}"
    fi
  done
fi

section "Recent Logs"
docker logs --tail "${TAIL_LINES}" "${CONTAINER_NAME}" || true

