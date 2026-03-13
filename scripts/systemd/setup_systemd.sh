#!/bin/bash

# Script para configurar serviços systemd para {bot_name}
# Uso: sudo bash setup_systemd.sh

echo "🚀 Configurando serviços systemd para {bot_name}"
echo "=========================================="

# Criar diretório para serviços
mkdir -p /etc/systemd/system/terezia

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
if [ -x "$PROJECT_DIR/.venv/bin/uvicorn" ]; then
	VENV_BIN="$PROJECT_DIR/.venv/bin"
elif [ -x "$PROJECT_DIR/venv/bin/uvicorn" ]; then
	VENV_BIN="$PROJECT_DIR/venv/bin"
else
	echo "❌ Ambiente virtual não encontrado em $PROJECT_DIR/.venv ou $PROJECT_DIR/venv"
	exit 1
fi

echo "📁 Projeto detectado em: $PROJECT_DIR"
echo "🐍 Venv detectado em: $VENV_BIN"

# Copiar arquivos de serviço
sed -e "s|__PROJECT_DIR__|$PROJECT_DIR|g" -e "s|__VENV_BIN__|$VENV_BIN|g" \
	"$SCRIPT_DIR/terezia-api.service" > /etc/systemd/system/terezia/terezia-api.service
sed -e "s|__PROJECT_DIR__|$PROJECT_DIR|g" \
	"$SCRIPT_DIR/terezia-grafana.service" > /etc/systemd/system/terezia/terezia-grafana.service

# Criar symlinks para ativação
ln -sf /etc/systemd/system/terezia/terezia-api.service /etc/systemd/system/terezia-api.service
ln -sf /etc/systemd/system/terezia/terezia-grafana.service /etc/systemd/system/terezia-grafana.service

# Recarregar daemon do systemd
echo "🔄 Recarregando daemon do systemd..."
systemctl daemon-reload

# Habilitar serviços para iniciar na boot
echo "🔧 Habilitando serviços para iniciar na boot..."
systemctl enable terezia-api.service
systemctl enable terezia-grafana.service

# Iniciar serviços
echo "🚀 Iniciando serviços..."
systemctl start terezia-api.service
systemctl start terezia-grafana.service

# Verificar status
echo ""
echo "📊 Status dos serviços:"
echo "=========================================="
systemctl status terezia-api.service --no-pager -l
echo ""
systemctl status terezia-grafana.service --no-pager -l

echo ""
echo "✅ Configuração concluída!"
echo ""
echo "📋 Comandos úteis:"
echo "  - Verificar logs da API: journalctl -u terezia-api -f"
echo "  - Verificar logs do Grafana: journalctl -u terezia-grafana -f"
echo "  - Reiniciar API: systemctl restart terezia-api"
echo "  - Reiniciar Grafana: systemctl restart terezia-grafana"
echo "  - Parar serviços: systemctl stop terezia-api terezia-grafana"
echo ""
echo "🌐 Acessar serviços:"
echo "  - API: http://localhost:8000"
echo "  - Grafana: http://localhost:3001"
