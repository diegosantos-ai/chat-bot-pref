<#
.SYNOPSIS
Inicia a demonstração do Nexo Gov SaaS localmente.

.DESCRIPTION
Este script verifica se a rede infra_nexo-network existe, 
inicia o docker-compose local com o Bot, o Admin Backend e o Admin Panel.
#>

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "   Iniciando Nexo Gov SaaS - Local Demo  " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Função para verificar se a rede existe
function Ensure-Network {
    Write-Host "Verificando rede infra_nexo-network..." -ForegroundColor Yellow
    $networkExists = docker network ls | Select-String "infra_nexo-network"
    
    if (-not $networkExists) {
        Write-Host "Rede infra_nexo-network não encontrada. Criando rede local bridge..." -ForegroundColor Yellow
        docker network create infra_nexo-network
        Write-Host "Rede criada com sucesso." -ForegroundColor Green
    } else {
        Write-Host "Rede infra_nexo-network já existe." -ForegroundColor Green
    }
}

Ensure-Network

Write-Host "`nSubindo containers com Docker Compose..." -ForegroundColor Yellow
docker-compose -f docker-compose.local.yml up -d --build

if ($LASTEXITCODE -ne 0) {
    Write-Host "`bErro ao subir o Docker Compose. Verifique os logs acima." -ForegroundColor Red
    exit 1
}

Write-Host "`n=========================================" -ForegroundColor Cyan
Write-Host "🚀 Ambiente Iniciado com Sucesso" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "🌐 Admin Panel (Frontend): http://localhost:8080"
Write-Host "⚙️  Admin Backend (API):   http://localhost:8093/health"
Write-Host "🤖 Chatbot Core (API):    http://localhost:8101/health"
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "`nPara encerrar: docker-compose -f docker-compose.local.yml down" -ForegroundColor Gray
