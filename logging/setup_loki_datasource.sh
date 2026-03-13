#!/bin/bash
# ========================================
# Setup Loki Data Source in Grafana
# ========================================
# Configura o data source Loki no Grafana automaticamente

set -e

GRAFANA_URL="http://localhost:3001"
GRAFANA_USER="admin"
GRAFANA_PASS="${GRAFANA_PASS:-admin}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🔧 Configurando data source Loki no Grafana..."

# Verificar se Grafana está acessível
if ! curl -s -u "$GRAFANA_USER:$GRAFANA_PASS" "$GRAFANA_URL/api/health" > /dev/null 2>&1; then
    echo "❌ Erro: Grafana não está acessível em $GRAFANA_URL"
    echo "Verifique se o container está rodando: docker ps | grep grafana"
    exit 1
fi

echo "✅ Grafana está acessível"

# Criar data source Loki
RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -u "$GRAFANA_USER:$GRAFANA_PASS" \
  "$GRAFANA_URL/api/datasources" \
  -d '{
    "name": "Loki",
    "type": "loki",
    "url": "http://terezia-loki:3100",
    "access": "proxy",
    "isDefault": false,
    "jsonData": {
      "httpMethod": "POST",
      "manageAlerts": true,
      "alertUid": "",
      "derivedFields": [
        {
          "name": "TraceID",
          "matcherRegex": "traceID=(\\w+)",
          "url": "${__value.raw}"
        }
      ],
      "timeout": 60,
      "maxLines": 1000
    }
  }' 2>&1)

if echo "$RESPONSE" | grep -q "id"; then
    echo "✅ Data source Loki configurado com sucesso!"
    echo ""
    echo "📊 Acesse o Grafana em: https://nexobasis.com.br/grafana"
    echo "🔍 Explore logs em: https://nexobasis.com.br/grafana/explore"
    echo ""
    echo "💡 Queries úteis (LogQL):"
    echo "   • {unit=\"terezia-api.service\"} - Logs do terezia-api"
    echo "   • {job=\"nginx\"} - Logs do nginx"
    echo "   • {container=\"n8n-n8n-1\"} - Logs do n8n"
    echo "   • {unit=\"terezia-api.service\"} |= \"ERROR\" - Apenas erros"
    echo ""
else
    echo "⚠️  Aviso: Pode ser que o data source já exista ou houve um erro"
    echo "Resposta: $RESPONSE"
fi

# Importar dashboard de logs (se existir)
if [ -f "$PROJECT_DIR/dashboards/terezia-logs-dashboard.json" ]; then
    echo ""
    echo "📈 Importando dashboard de logs..."
    
    curl -s -X POST \
      -H "Content-Type: application/json" \
      -u "$GRAFANA_USER:$GRAFANA_PASS" \
      "$GRAFANA_URL/api/dashboards/db" \
      -d @"$PROJECT_DIR/dashboards/terezia-logs-dashboard.json" > /dev/null 2>&1
    
    echo "✅ Dashboard importado!"
fi

echo ""
echo "🎉 Configuração concluída!"
