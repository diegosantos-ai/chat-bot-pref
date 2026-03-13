# =========================================
# Chat Pref - Script de Operacao com Docker Compose
# =========================================
# Uso: .\scripts\ops\deploy.ps1 [comando]
# Comandos: start, stop, restart, logs, status, build

param(
    [Parameter(Position=0)]
    [ValidateSet("start", "stop", "restart", "logs", "status", "build", "update", "help")]
    [string]$Command = "help"
)

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))
Set-Location $ProjectDir
$ServiceName = if ($env:SERVICE_NAME) { $env:SERVICE_NAME } else { "chat-pref-api" }

function Write-Info { param($Message) Write-Host "[INFO] $Message" -ForegroundColor Green }
function Write-Warn { param($Message) Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Write-Err { param($Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }

function Invoke-Compose {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Arguments
    )

    docker compose version *> $null
    if ($LASTEXITCODE -eq 0) {
        & docker compose @Arguments
        return
    }

    if (Get-Command docker-compose -ErrorAction SilentlyContinue) {
        & docker-compose @Arguments
        return
    }

    Write-Err "Docker Compose nao esta instalado."
    exit 1
}

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

function Start-ChatPref {
    Write-Info "Iniciando Chat Pref..."
    Invoke-Compose up -d --build
    Write-Info "Aguardando container ficar healthy..."
    Start-Sleep -Seconds 10
    Get-ChatPrefStatus
}

function Stop-ChatPref {
    Write-Info "Parando Chat Pref..."
    Invoke-Compose down
    Write-Info "Containers parados"
}

function Restart-ChatPref {
    Write-Info "Reiniciando Chat Pref..."
    Invoke-Compose restart
    Get-ChatPrefStatus
}

function Get-ChatPrefLogs {
    Write-Info "Mostrando logs (Ctrl+C para sair)..."
    Invoke-Compose logs -f $ServiceName
}

function Get-ChatPrefStatus {
    Write-Info "Status dos containers:"
    Invoke-Compose ps
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

function Build-ChatPref {
    Write-Info "Reconstruindo imagem Docker..."
    Invoke-Compose build --no-cache
    Write-Info "Build concluido"
}

function Update-ChatPref {
    Write-Info "Atualizando e reiniciando..."
    $CurrentBranch = git branch --show-current
    git pull --ff-only origin $CurrentBranch
    Invoke-Compose up -d --build
    Get-ChatPrefStatus
}

function Show-Help {
    Write-Host "Chat Pref - Script de Operacao" -ForegroundColor Cyan
    Write-Host "==========================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Uso: .\scripts\ops\deploy.ps1 [comando]"
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
        Start-ChatPref
    }
    "stop" {
        Stop-ChatPref
    }
    "restart" {
        Restart-ChatPref
    }
    "logs" {
        Get-ChatPrefLogs
    }
    "status" {
        Get-ChatPrefStatus
    }
    "build" {
        Test-Requirements
        Build-ChatPref
    }
    "update" {
        Test-Requirements
        Update-ChatPref
    }
    default {
        Show-Help
    }
}
