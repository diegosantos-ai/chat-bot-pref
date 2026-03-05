# =========================================
# TerezIA - Script de Deploy (PowerShell)
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

function Start-TerezIA {
    Write-Info "Iniciando TerezIA..."
    docker-compose up -d --build
    Write-Info "Aguardando container ficar healthy..."
    Start-Sleep -Seconds 10
    Get-TerezIAStatus
}

function Stop-TerezIA {
    Write-Info "Parando TerezIA..."
    docker-compose down
    Write-Info "Containers parados"
}

function Restart-TerezIA {
    Write-Info "Reiniciando TerezIA..."
    docker-compose restart
    Get-TerezIAStatus
}

function Get-TerezIALogs {
    Write-Info "Mostrando logs (Ctrl+C para sair)..."
    docker-compose logs -f terezia
}

function Get-TerezIAStatus {
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

function Build-TerezIA {
    Write-Info "Reconstruindo imagem Docker..."
    docker-compose build --no-cache
    Write-Info "Build concluido"
}

function Update-TerezIA {
    Write-Info "Atualizando e reiniciando..."
    git pull origin main
    docker-compose up -d --build
    Get-TerezIAStatus
}

function Show-Help {
    Write-Host "TerezIA - Script de Deploy" -ForegroundColor Cyan
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
        Start-TerezIA
    }
    "stop" {
        Stop-TerezIA
    }
    "restart" {
        Restart-TerezIA
    }
    "logs" {
        Get-TerezIALogs
    }
    "status" {
        Get-TerezIAStatus
    }
    "build" {
        Test-Requirements
        Build-TerezIA
    }
    "update" {
        Test-Requirements
        Update-TerezIA
    }
    default {
        Show-Help
    }
}
