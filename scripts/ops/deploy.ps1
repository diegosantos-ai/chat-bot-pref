# =========================================
# {bot_name} - Script de Deploy (PowerShell)
# =========================================
# Uso: .\scripts\deploy.ps1 [comando]
# Comandos: start, stop, restart, logs, status, build

param(
    [Parameter(Position=0)]
    [ValidateSet("start", "stop", "restart", "logs", "status", "build", "update", "help")]
    [string]$Command = "help"
)

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectDir

function Write-Info { param($Message) Write-Host "[INFO] $Message" -ForegroundColor Green }
function Write-Warn { param($Message) Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Write-Err { param($Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }

function Test-Requirements {
    # Verifica Docker
    try {
        docker --version | Out-Null
    } catch {
        Write-Err "Docker nao esta instalado. Instale em: https://docs.docker.com/get-docker/"
        exit 1
    }
    
    # Verifica .env
    if (-not (Test-Path ".env")) {
        Write-Err "Arquivo .env nao encontrado!"
        Write-Warn "Copie .env.prod.example para .env e configure os valores."
        exit 1
    }
    
    Write-Info "Pre-requisitos OK"
}

function Start-{bot_name} {
    Write-Info "Iniciando {bot_name}..."
    docker-compose up -d --build
    Write-Info "Aguardando container ficar healthy..."
    Start-Sleep -Seconds 10
    Get-{bot_name}Status
}

function Stop-{bot_name} {
    Write-Info "Parando {bot_name}..."
    docker-compose down
    Write-Info "Containers parados"
}

function Restart-{bot_name} {
    Write-Info "Reiniciando {bot_name}..."
    docker-compose restart
    Get-{bot_name}Status
}

function Get-{bot_name}Logs {
    Write-Info "Mostrando logs (Ctrl+C para sair)..."
    docker-compose logs -f terezia
}

function Get-{bot_name}Status {
    Write-Info "Status dos containers:"
    docker-compose ps
    Write-Host ""
    Write-Info "Testando health check..."
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Info "API esta respondendo"
        }
    } catch {
        Write-Warn "API ainda nao esta respondendo (pode estar iniciando)"
    }
}

function Build-{bot_name} {
    Write-Info "Reconstruindo imagem Docker..."
    docker-compose build --no-cache
    Write-Info "Build concluido"
}

function Update-{bot_name} {
    Write-Info "Atualizando e reiniciando..."
    git pull origin main
    docker-compose up -d --build
    Get-{bot_name}Status
}

function Show-Help {
    Write-Host "{bot_name} - Script de Deploy" -ForegroundColor Cyan
    Write-Host "==========================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Uso: .\scripts\deploy.ps1 [comando]"
    Write-Host ""
    Write-Host "Comandos:"
    Write-Host "  start    - Inicia os containers (build + up)"
    Write-Host "  stop     - Para os containers"
    Write-Host "  restart  - Reinicia os containers"
    Write-Host "  logs     - Mostra logs em tempo real"
    Write-Host "  status   - Mostra status dos containers"
    Write-Host "  build    - Reconstroi a imagem Docker"
    Write-Host "  update   - Git pull + rebuild + restart"
}

# Executa comando
switch ($Command) {
    "start" {
        Test-Requirements
        Start-{bot_name}
    }
    "stop" {
        Stop-{bot_name}
    }
    "restart" {
        Restart-{bot_name}
    }
    "logs" {
        Get-{bot_name}Logs
    }
    "status" {
        Get-{bot_name}Status
    }
    "build" {
        Test-Requirements
        Build-{bot_name}
    }
    "update" {
        Test-Requirements
        Update-{bot_name}
    }
    default {
        Show-Help
    }
}
