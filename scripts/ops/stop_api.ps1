param()

$root = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $root ".env"

$appPort = "8000"

if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*APP_PORT\s*=\s*(.+)$') { $appPort = $Matches[1].Trim() }
    }
}

$appPort = $appPort.Trim().Trim('"').Trim("'")

try {
    $connections = Get-NetTCPConnection -LocalPort $appPort -State Listen -ErrorAction Stop
} catch {
    Write-Host "No process listening on port $appPort."
    return
}

if (-not $connections) {
    Write-Host "No process listening on port $appPort."
    return
}

$pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
foreach ($processId in $pids) {
    try {
        Write-Host "Stopping PID $processId (port $appPort) ..."
        Stop-Process -Id $processId -Force -ErrorAction Stop
    } catch {
        Write-Host "Failed to stop PID $processId. Try running this script as Administrator."
    }
}

Write-Host "Done."
