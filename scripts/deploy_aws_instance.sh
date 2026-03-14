#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/chat-pref/app}"
RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE:-/opt/chat-pref/runtime.env}"
REPO_URL="${REPO_URL:-https://github.com/diegosantos-ai/chat-bot-pref.git}"
APP_REF="${APP_REF:-develop}"
TENANT_MANIFEST="${TENANT_MANIFEST:-tenants/prefeitura-vila-serena/tenant.json}"
SERVICE_PORT="${SERVICE_PORT:-8000}"
PUBLIC_HTTPS_ENABLED="${PUBLIC_HTTPS_ENABLED:-false}"
PUBLIC_BASE_HOSTNAME="${PUBLIC_BASE_HOSTNAME:-}"

log() {
  printf '[deploy-aws] %s\n' "$1"
}

build_sslip_hostname() {
  local public_ip="$1"
  printf '%s.sslip.io' "${public_ip//./-}"
}

read_public_ip_from_imds() {
  local token
  token="$(curl -fsS --connect-timeout 2 --max-time 5 -X PUT "http://169.254.169.254/latest/api/token" \
    -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")" || {
    log "Falha ao obter token do IMDS (metadata service). Verifique conectividade e politicas de rede." >&2
    return 1
  }
  curl -fsS --connect-timeout 2 --max-time 5 -H "X-aws-ec2-metadata-token: ${token}" \
    "http://169.254.169.254/latest/meta-data/public-ipv4" || {
    log "Falha ao ler public-ipv4 do IMDS (metadata service). Verifique conectividade e politicas de rede." >&2
    return 1
  }
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

if [ -f "$APP_DIR/.env.compose" ]; then
  file_public_https_enabled="$(awk -F= '/^PUBLIC_HTTPS_ENABLED=/{print $2; exit}' "$APP_DIR/.env.compose")"
  file_public_base_hostname="$(awk -F= '/^PUBLIC_BASE_HOSTNAME=/{print $2; exit}' "$APP_DIR/.env.compose")"
  if [ -n "${file_public_https_enabled:-}" ]; then
    PUBLIC_HTTPS_ENABLED="$file_public_https_enabled"
  fi
  if [ -n "${file_public_base_hostname:-}" ]; then
    PUBLIC_BASE_HOSTNAME="$file_public_base_hostname"
  fi
fi

if [ "$PUBLIC_HTTPS_ENABLED" = "true" ] && [ -z "$PUBLIC_BASE_HOSTNAME" ]; then
  log "Derivando hostname publico HTTPS a partir do IP da instancia"
  PUBLIC_BASE_HOSTNAME="$(build_sslip_hostname "$(read_public_ip_from_imds)")"
  # Garante apenas uma ocorrencia de PUBLIC_BASE_HOSTNAME em .env.compose
  if [ -f "$APP_DIR/.env.compose" ]; then
    sed -i.bak '/^PUBLIC_BASE_HOSTNAME=/d' "$APP_DIR/.env.compose" || true
    rm -f "$APP_DIR/.env.compose.bak"
  fi
  printf '\nPUBLIC_BASE_HOSTNAME=%s\n' "$PUBLIC_BASE_HOSTNAME" >>"$APP_DIR/.env.compose"
fi

if [ "$PUBLIC_HTTPS_ENABLED" = "true" ]; then
  if [ ! -f "$APP_DIR/deploy/caddy/Caddyfile.template" ]; then
    echo "Template do Caddy nao encontrado em $APP_DIR/deploy/caddy/Caddyfile.template." >&2
    exit 1
  fi
  log "Renderizando configuracao do Caddy para $PUBLIC_BASE_HOSTNAME"
  sed "s/__PUBLIC_BASE_HOSTNAME__/${PUBLIC_BASE_HOSTNAME}/g" \
    "$APP_DIR/deploy/caddy/Caddyfile.template" >"$APP_DIR/deploy/caddy/Caddyfile.runtime"
fi

log "Subindo backend via docker compose"
if [ "$PUBLIC_HTTPS_ENABLED" = "true" ]; then
  log "Habilitando proxy HTTPS publico para $PUBLIC_BASE_HOSTNAME"
  docker compose --env-file "$APP_DIR/.env.compose" --profile public -f docker-compose.yml up -d --build
else
  docker compose --env-file "$APP_DIR/.env.compose" -f docker-compose.yml up -d --build
fi

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
  --ingest

log "Validando health remoto local a instancia"
python3 - <<PY
import urllib.request

urllib.request.urlopen("http://127.0.0.1:${SERVICE_PORT}/health", timeout=10).read()
PY

if [ "$PUBLIC_HTTPS_ENABLED" = "true" ]; then
  log "Validando HTTPS publico do proxy"
  attempt=0
  until curl -fsS "https://${PUBLIC_BASE_HOSTNAME}/health" >/dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ "$attempt" -ge 30 ]; then
      echo "Proxy HTTPS publico nao respondeu em https://${PUBLIC_BASE_HOSTNAME}/health." >&2
      docker logs chat-pref-public >&2 || true
      exit 1
    fi
    sleep 5
  done
fi

log "Deploy concluido"
