#!/bin/bash
# ========================================
# Instalação Completa: Loki + Promtail
# ========================================
# Centralização de logs para TerezIA
# Versão: 1.0
# Data: 2026-02-04

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOGGING_DIR="$SCRIPT_DIR"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funções de log
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCESSO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[AVISO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERRO]${NC} $1"
}

# ========================================
# VERIFICAÇÕES INICIAIS
# ========================================
log_info "Iniciando instalação do Loki + Promtail..."
log_info "Diretório do projeto: $PROJECT_DIR"

# Verificar Docker
cd "$LOGGING_DIR"

if ! command -v docker &> /dev/null; then
    log_error "Docker não está instalado"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    log_error "Docker Compose plugin não está instalado"
    exit 1
fi

log_success "Docker e Docker Compose encontrados"

# Verificar se a rede existe
if ! docker network ls | grep -q "pilot-atendimento_default"; then
    log_warning "Rede pilot-atendimento_default não encontrada"
    log_info "Verificando se Grafana está rodando..."
    
    if docker ps | grep -q "terezia-grafana"; then
        log_info "Grafana encontrado, obtendo rede..."
        NETWORK=$(docker inspect terezia-grafana --format='{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}' 2>/dev/null || echo "")
        if [ -n "$NETWORK" ]; then
            log_info "Usando rede existente: $NETWORK"
            sed -i "s/pilot-atendimento_default/$NETWORK/g" docker-compose-loki.yml
        else
            log_error "Não foi possível detectar a rede do Grafana"
            exit 1
        fi
    else
        log_error "Grafana não está rodando. Inicie o Grafana primeiro."
        exit 1
    fi
else
    log_success "Rede pilot-atendimento_default encontrada"
fi

# Verificar permissões nos logs
log_info "Verificando permissões de leitura nos logs..."

if [ -r "/var/log/journal" ]; then
    log_success "Acesso ao journald OK"
else
    log_warning "Sem acesso direto ao journald. Tentando alternativa..."
fi

if [ -r "/var/log/nginx/access.log" ]; then
    log_success "Acesso aos logs do nginx OK"
else
    log_warning "Sem acesso aos logs do nginx"
fi

if [ -r "/var/run/docker.sock" ]; then
    log_success "Acesso ao Docker socket OK"
else
    log_error "Sem acesso ao Docker socket"
    exit 1
fi

# ========================================
# BACKUP
# ========================================
log_info "Criando backup das configurações existentes..."
if [ -d "loki-data" ]; then
    BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
    mv loki-data "$BACKUP_DIR"
    log_success "Backup criado: $BACKUP_DIR"
fi

# ========================================
# INICIAR SERVIÇOS
# ========================================
log_info "Iniciando containers Loki e Promtail..."

docker compose -f docker-compose-loki.yml down 2>/dev/null || true
docker compose -f docker-compose-loki.yml up -d

# Aguardar inicialização
log_info "Aguardando inicialização (15s)..."
sleep 5

# Verificar se Loki está saudável
RETRIES=0
MAX_RETRIES=12
while [ $RETRIES -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:3100/ready > /dev/null 2>&1; then
        log_success "Loki está pronto!"
        break
    fi
    RETRIES=$((RETRIES + 1))
    log_info "Aguardando Loki... ($RETRIES/$MAX_RETRIES)"
    sleep 5
done

if [ $RETRIES -eq $MAX_RETRIES ]; then
    log_error "Loki não iniciou corretamente"
    log_info "Verificando logs: docker logs terezia-loki"
    exit 1
fi

# Verificar Promtail
if docker ps | grep -q "terezia-promtail"; then
    log_success "Promtail está rodando!"
else
    log_error "Promtail não iniciou corretamente"
    log_info "Verificando logs: docker logs terezia-promtail"
    exit 1
fi

# ========================================
# CONFIGURAR GRAFANA
# ========================================
log_info "Configurando data source no Grafana..."

chmod +x setup_loki_datasource.sh
./setup_loki_datasource.sh

# ========================================
# IMPORTAR DASHBOARD
# ========================================
log_info "Importando dashboard de logs..."

if [ -f "$PROJECT_DIR/dashboards/terezia-logs-dashboard.json" ]; then
    log_success "Dashboard encontrado"
    
    # Copiar para diretório de provisioning do Grafana
    GRAFANA_DASHBOARD_DIR="/var/lib/docker/volumes/pilot-atendimento_grafana_data/_data/dashboards"
    if [ -d "$GRAFANA_DASHBOARD_DIR" ]; then
        cp "$PROJECT_DIR/dashboards/terezia-logs-dashboard.json" "$GRAFANA_DASHBOARD_DIR/"
        log_success "Dashboard copiado para Grafana"
    else
        log_warning "Diretório de dashboards do Grafana não encontrado"
    fi
else
    log_warning "Dashboard JSON não encontrado"
fi

# ========================================
# RESUMO
# ========================================
echo ""
echo "========================================"
echo -e "${GREEN}✅ INSTALAÇÃO CONCLUÍDA!${NC}"
echo "========================================"
echo ""
echo -e "${BLUE}📊 Acesse o Grafana:${NC}"
echo "   URL: https://nexobasis.com.br/grafana"
echo "   Usuário: admin"
echo "   Senha: admin24052014"
echo ""
echo -e "${BLUE}🔍 Explore os logs:${NC}"
echo "   https://nexobasis.com.br/grafana/explore"
echo ""
echo -e "${BLUE}📝 Queries úteis (LogQL):${NC}"
echo "   {unit=\"terezia-api.service\"}           → Logs da API"
echo "   {job=\"nginx\"}                          → Logs do nginx"
echo "   {container=\"n8n-n8n-1\"}                → Logs do n8n"
echo "   {unit=\"terezia-api.service\"} |= \"ERROR\"  → Apenas erros"
echo ""
echo -e "${BLUE}🔧 Serviços em execução:${NC}"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(loki|promtail)"
echo ""
echo -e "${BLUE}📁 Arquivos de configuração:${NC}"
echo "   $LOGGING_DIR/loki-config.yml"
echo "   $LOGGING_DIR/promtail-config.yml"
echo "   $LOGGING_DIR/docker-compose-loki.yml"
echo ""
echo -e "${YELLOW}⚠️  Retenção de logs: 7 dias${NC}"
echo "   Logs antigos são automaticamente removidos"
echo ""
echo -e "${BLUE}🆘 Comandos úteis:${NC}"
echo "   Ver logs Loki:    docker logs -f terezia-loki"
echo "   Ver logs Promtail: docker logs -f terezia-promtail"
echo "   Reiniciar:        docker compose -f docker-compose-loki.yml restart"
echo "   Parar:            docker compose -f docker-compose-loki.yml down"
echo ""
log_success "Instalação finalizada com sucesso!"
