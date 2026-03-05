#!/bin/bash

# Script para configurar serviços systemd para TerezIA
# Uso: sudo bash setup_systemd.sh

echo "🚀 Configurando serviços systemd para TerezIA"
echo "=========================================="

# Criar diretório para serviços
mkdir -p /etc/systemd/system/terezia

# Copiar arquivos de serviço
cp /root/pilot-atendimento/scripts/systemd/terezia-api.service /etc/systemd/system/terezia/terezia-api.service
cp /root/pilot-atendimento/scripts/systemd/terezia-grafana.service /etc/systemd/system/terezia/terezia-grafana.service

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
