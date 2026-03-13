#!/bin/bash
# =========================================
# Chat Pref - Script de Operacao com Docker Compose
# =========================================
# Uso: ./scripts/ops/deploy.sh [comando]
# Comandos: start, stop, restart, logs, status, build

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR"
SERVICE_NAME="${SERVICE_NAME:-chat-pref-api}"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

compose_cmd() {
    if docker compose version >/dev/null 2>&1; then
        docker compose "$@"
    elif command -v docker-compose >/dev/null 2>&1; then
        docker-compose "$@"
    else
        log_error "Docker Compose nao esta instalado."
        exit 1
    fi
}

check_requirements() {
    if ! command -v docker >/dev/null 2>&1; then
        log_error "Docker nao esta instalado. Instale em: https://docs.docker.com/get-docker/"
        exit 1
    fi

    if [ ! -f ".env" ]; then
        log_error "Arquivo .env nao encontrado!"
        log_warn "Copie .env.prod.example para .env e configure os valores."
        exit 1
    fi

    log_info "Pre-requisitos OK"
}

start() {
    log_info "Iniciando Chat Pref..."
    compose_cmd up -d --build
    log_info "Aguardando container ficar healthy..."
    sleep 10
    status
}

stop() {
    log_info "Parando Chat Pref..."
    compose_cmd down
    log_info "Containers parados"
}

restart() {
    log_info "Reiniciando Chat Pref..."
    compose_cmd restart
    status
}

logs() {
    log_info "Mostrando logs (Ctrl+C para sair)..."
    compose_cmd logs -f "$SERVICE_NAME"
}

status() {
    log_info "Status dos containers:"
    compose_cmd ps
    echo ""
    log_info "Testando health check..."
    if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
        log_info "API esta respondendo"
    else
        log_warn "API ainda nao esta respondendo (pode estar iniciando)"
    fi
}

build() {
    log_info "Reconstruindo imagem Docker..."
    compose_cmd build --no-cache
    log_info "Build concluido"
}

update() {
    log_info "Atualizando e reiniciando..."
    local current_branch
    current_branch="$(git branch --show-current)"
    git pull --ff-only origin "$current_branch"
    compose_cmd up -d --build
    status
}

case "${1:-help}" in
    start)
        check_requirements
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    logs)
        logs
        ;;
    status)
        status
        ;;
    build)
        check_requirements
        build
        ;;
    update)
        check_requirements
        update
        ;;
    *)
        echo "Chat Pref - Script de Operacao"
        echo "=========================="
        echo ""
        echo "Uso: $0 [comando]"
        echo ""
        echo "Comandos:"
        echo "  start    - Inicia os containers (build + up)"
        echo "  stop     - Para os containers"
        echo "  restart  - Reinicia os containers"
        echo "  logs     - Mostra logs em tempo real"
        echo "  status   - Mostra status dos containers"
        echo "  build    - Reconstrói a imagem Docker"
        echo "  update   - Git pull + rebuild + restart"
        ;;
esac
