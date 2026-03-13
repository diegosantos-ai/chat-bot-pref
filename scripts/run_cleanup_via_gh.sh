#!/bin/bash

# Script para executar o workflow de limpeza de branches via GitHub CLI
# Requer: gh (GitHub CLI) instalado e autenticado

set -e

echo "🔧 Executando workflow de limpeza de branches..."
echo ""

# Verificar se gh está instalado
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) não está instalado."
    echo ""
    echo "Para instalar:"
    echo "  - Mac: brew install gh"
    echo "  - Linux: https://github.com/cli/cli/blob/trunk/docs/install_linux.md"
    echo "  - Windows: https://github.com/cli/cli/releases"
    echo ""
    echo "Após instalar, autentique com: gh auth login"
    echo ""
    echo "Alternativamente, execute via interface web:"
    echo "  https://github.com/diegosantos-ai/pilot-atendimento/actions/workflows/cleanup_branches.yml"
    exit 1
fi

# Verificar autenticação
if ! gh auth status &> /dev/null; then
    echo "❌ GitHub CLI não está autenticado."
    echo "Execute: gh auth login"
    exit 1
fi

echo "✅ GitHub CLI instalado e autenticado"
echo ""

# Confirmar execução
echo "⚠️  ATENÇÃO: Este comando irá:"
echo "  1. Mergear todas as branches secundárias na 'develop'"
echo "  2. Deletar todas as branches exceto 'main' e 'develop'"
echo ""
read -p "Digite 'CONFIRMAR' para continuar: " confirmacao

if [ "$confirmacao" != "CONFIRMAR" ]; then
    echo "❌ Operação cancelada."
    exit 0
fi

echo ""
echo "🚀 Iniciando workflow..."

# Executar workflow
gh workflow run cleanup_branches.yml \
    --repo diegosantos-ai/pilot-atendimento \
    --field confirm=CONFIRM

echo ""
echo "✅ Workflow iniciado com sucesso!"
echo ""
echo "Acompanhe o progresso em:"
echo "  https://github.com/diegosantos-ai/pilot-atendimento/actions"
echo ""
echo "Ou via CLI:"
echo "  gh run list --workflow=cleanup_branches.yml --repo diegosantos-ai/pilot-atendimento"
echo "  gh run watch <run-id> --repo diegosantos-ai/pilot-atendimento"
