#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/chat-pref/app}"
RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE:-/opt/chat-pref/runtime.env}"
REPO_URL="${REPO_URL:-https://github.com/diegosantos-ai/chat-bot-pref.git}"
APP_REF="${APP_REF:-develop}"
TENANT_MANIFEST="${TENANT_MANIFEST:-tenants/prefeitura-vila-serena/tenant.json}"
SERVICE_PORT="${SERVICE_PORT:-8000}"

log() {
  printf '[deploy-aws] %s\n' "$1"
}

if ! command -v docker >/dev/null 2>&1; then
  echo "docker nao encontrado no host remoto." >&2
  exit 1
fi

if ! command -v git >/dev/null 2>&1; then
  echo "git nao encontrado no host remoto." >&2
  exit 1
fi

mkdir -p "$(dirname "$APP_DIR")"

if [ ! -d "$APP_DIR/.git" ]; then
  log "Clonando repositorio em $APP_DIR"
  git clone --depth 1 --branch "$APP_REF" "$REPO_URL" "$APP_DIR"
fi

cd "$APP_DIR"

log "Atualizando codigo para $APP_REF"
git fetch --depth 1 origin "$APP_REF"
git checkout --force FETCH_HEAD

if [ -f "$RUNTIME_ENV_FILE" ]; then
  log "Sincronizando runtime env para .env.compose"
  cp "$RUNTIME_ENV_FILE" "$APP_DIR/.env.compose"
elif [ -f "$APP_DIR/.env.prod.example" ]; then
  log "Usando .env.prod.example como fallback do ambiente"
  cp "$APP_DIR/.env.prod.example" "$APP_DIR/.env.compose"
else
  echo "Nenhum arquivo de ambiente encontrado para o deploy." >&2
  exit 1
fi

log "Subindo backend via docker compose"
docker compose -f docker-compose.yml up -d --build

attempt=0
until [ "$(docker inspect -f '{{.State.Health.Status}}' chat-pref-api 2>/dev/null)" = "healthy" ]; do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge 60 ]; then
    echo "Container chat-pref-api nao ficou healthy a tempo." >&2
    docker logs chat-pref-api >&2 || true
    exit 1
  fi
  sleep 2
done

log "Bootstrapando tenant demonstrativo"
docker exec chat-pref-api python scripts/bootstrap_demo_tenant.py \
  --manifest "$TENANT_MANIFEST" \
  --purge-documents \
  --ingest \
  --phase-report fase13

log "Validando health remoto local a instancia"
python3 - <<PY
import urllib.request

urllib.request.urlopen("http://127.0.0.1:${SERVICE_PORT}/health", timeout=10).read()
PY

log "Deploy concluido"
