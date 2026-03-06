#!/bin/bash
# ========================================
# Import All Dashboards to Grafana
# ========================================
# Import all dashboards to Grafana
# Version: 1.0

set -e

GRAFANA_URL="http://localhost:3001"
GRAFANA_USER="admin"
GRAFANA_PASS="admin24052014"
DASHBOARDS_DIR="/root/pilot-atendimento/dashboards"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCESSO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERRO]${NC} $1"
}

echo "========================================"
echo -e "${BLUE}📊 Importação de Dashboards Grafana${NC}"
echo "========================================"
echo ""

# Check Grafana is accessible
log_info "Verificando conexão com Grafana..."
if ! curl -s -u "$GRAFANA_USER:$GRAFANA_PASS" "$GRAFANA_URL/api/health" > /dev/null 2>&1; then
    log_error "Grafana não está acessível em $GRAFANA_URL"
    exit 1
fi
log_success "Grafana está online"

# Get or create folder
FOLDER_ID=""
FOLDER_RESPONSE=$(curl -s -u "$GRAFANA_USER:$GRAFANA_PASS" "$GRAFANA_URL/api/folders" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

if [ -n "$FOLDER_RESPONSE" ]; then
    FOLDER_ID="$FOLDER_RESPONSE"
    log_info "Usando pasta existente (ID: $FOLDER_ID)"
else
    # Create folder
    FOLDER_CREATE=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -u "$GRAFANA_USER:$GRAFANA_PASS" \
        "$GRAFANA_URL/api/folders" \
        -d '{"title":"{bot_name} Services"}')
    FOLDER_ID=$(echo "$FOLDER_CREATE" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
    log_success "Pasta '{bot_name} Services' criada (ID: $FOLDER_ID)"
fi

# Counters
IMPORTED=0
FAILED=0

# Function to import dashboard
import_dashboard() {
    local file=$1
    local filename=$(basename "$file")
    
    log_info "Importando: $filename"
    
    # Read dashboard content
    DASHBOARD_JSON=$(cat "$file")
    
    # Import
    RESPONSE=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -u "$GRAFANA_USER:$GRAFANA_PASS" \
        "$GRAFANA_URL/api/dashboards/db" \
        -d "{\"dashboard\": $DASHBOARD_JSON, \"folderId\": ${FOLDER_ID:-0}, \"overwrite\": true}" 2>&1)
    
    if echo "$RESPONSE" | grep -q '"status":"success"'; then
        log_success "✓ $filename importado"
        ((IMPORTED++))
    else
        log_error "✗ Falha ao importar $filename"
        log_info "Resposta: $RESPONSE"
        ((FAILED++))
    fi
}

# Import all dashboards in order
echo ""
log_info "Iniciando importação de dashboards..."
echo ""

# List of dashboards in desired order
DASHBOARDS=(
    "01-overview-services.json:Overview de Servicos"
    "02-terezia-api.json:{bot_name} API"
    "03-nginx.json:Nginx"
    "04-postgresql.json:PostgreSQL"
    "05-n8n.json:N8N"
    "06-loki-infrastructure.json:Loki Infrastructure"
)

for item in "${DASHBOARDS[@]}"; do
    IFS=':' read -r filename title <<< "$item"
    filepath="$DASHBOARDS_DIR/$filename"
    
    if [ -f "$filepath" ]; then
        import_dashboard "$filepath"
    else
        log_warning "Dashboard não encontrado: $filename"
        ((FAILED++))
    fi
done

echo ""
echo "========================================"
echo -e "${GREEN}✅ Importação Concluída!${NC}"
echo "========================================"
echo ""
echo -e "${GREEN}Importados:${NC} $IMPORTED"
echo -e "${RED}Falhas:${NC} $FAILED"
echo ""
echo -e "${BLUE}📊 Acesse os dashboards:${NC}"
echo "   URL: https://nexobasis.com.br/grafana"
echo "   Pasta: {bot_name} Services"
echo ""
echo -e "${BLUE}📁 Dashboards disponíveis:${NC}"
echo "   • Overview de Servicos - Visão geral de todos os serviços"
echo "   • {bot_name} API - Logs da API (uvicorn)"
echo "   • Nginx - Logs do servidor web"
echo "   • PostgreSQL - Logs do banco de dados"
echo "   • N8N - Logs do workflow automation"
echo "   • Loki Infrastructure - Monitoramento do próprio Loki"
echo ""
