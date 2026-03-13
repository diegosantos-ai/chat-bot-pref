#!/bin/bash
# =========================================
# {bot_name} - Script de Deploy
# =========================================
# Uso: ./scripts/deploy.sh [comando]
# Comandos: start, stop, restart, logs, status, build

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Verifica pré-requisitos
check_requirements() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker não está instalado. Instale em: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose não está instalado."
        exit 1
    fi
    
    if [ ! -f ".env" ]; then
        log_error "Arquivo .env não encontrado!"
        log_warn "Copie .env.prod.example para .env e configure os valores."
        exit 1
    fi
    
    log_info "Pré-requisitos OK ✓"
}

# Comandos
start() {
    log_info "Iniciando {bot_name}..."
    docker-compose up -d --build
    log_info "Aguardando container ficar healthy..."
    sleep 10
    status
}

stop() {
    log_info "Parando {bot_name}..."
    docker-compose down
    log_info "Containers parados ✓"
}

restart() {
    log_info "Reiniciando {bot_name}..."
    docker-compose restart
    status
}

logs() {
    log_info "Mostrando logs (Ctrl+C para sair)..."
    docker-compose logs -f terezia
}

status() {
    log_info "Status dos containers:"
    docker-compose ps
    echo ""
    log_info "Testando health check..."
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        log_info "API está respondendo ✓"
    else
        log_warn "API ainda não está respondendo (pode estar iniciando)"
    fi
}

build() {
    log_info "Reconstruindo imagem Docker..."
    docker-compose build --no-cache
    log_info "Build concluído ✓"
}

update() {
    log_info "Atualizando e reiniciando..."
    git pull origin main
    docker-compose up -d --build
    status
}

# Menu principal
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
        echo "{bot_name} - Script de Deploy"
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
