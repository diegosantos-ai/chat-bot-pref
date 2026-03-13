<#
.SYNOPSIS
Inicia o ambiente local do Chat Pref.

.DESCRIPTION
Inicia o docker compose local com a API principal, o backend admin e o painel web.
#>

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "      Iniciando Chat Pref - Local Demo   " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

function Get-ComposeCommand {
    try {
        docker compose version | Out-Null
        return "docker compose"
    } catch {
        if (Get-Command docker-compose -ErrorAction SilentlyContinue) {
            return "docker-compose"
        }

        Write-Host "Docker Compose nao encontrado. Instale 'docker compose' ou 'docker-compose'." -ForegroundColor Red
        exit 1
    }
}

$ComposeCommand = Get-ComposeCommand

Write-Host "`nSubindo containers com Docker Compose..." -ForegroundColor Yellow
Invoke-Expression "$ComposeCommand -f docker-compose.local.yml up -d --build"

Write-Host "`n=========================================" -ForegroundColor Cyan
Write-Host "🚀 Ambiente Iniciado com Sucesso" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "🌐 Admin Panel (Frontend): http://localhost:8080"
Write-Host "⚙️  Admin Backend (API):   http://localhost:8093/health"
Write-Host "🤖 Chatbot Core (API):    http://localhost:8101/health"
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "`nPara encerrar: $ComposeCommand -f docker-compose.local.yml down" -ForegroundColor Gray
