param(
    [switch]$Reload
)

$root = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $root ".env"

$appHost = "0.0.0.0"
$appPort = "8000"

if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*APP_HOST\s*=\s*(.+)$') { $appHost = $Matches[1].Trim() }
        if ($_ -match '^\s*APP_PORT\s*=\s*(.+)$') { $appPort = $Matches[1].Trim() }
    }
}

$python = Join-Path $root ".venv\\Scripts\\python.exe"
if (-not (Test-Path $python)) { $python = "python" }

$args = @("-m","uvicorn","app.main:app","--host",$appHost,"--port",$appPort)
if ($Reload) { $args += "--reload" }

Write-Host "Starting API on $appHost`:$appPort ..."
& $python @args
