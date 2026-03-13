param(
    [switch]$Gzip,
    [switch]$Verify
)

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { $python = "python" }

Set-Location $root

$logDir = Join-Path $root "artifacts\backups\task_logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logFile = Join-Path $logDir "backup_all_$stamp.log"

Start-Transcript -Path $logFile -Force | Out-Null
try {
Write-Host "== Backup Postgres =="
$pgScript = Join-Path $root "scripts\backup_postgres.py"
$pgArgs = @($pgScript)
if ($Gzip) { $pgArgs += "--gzip" }
if ($Verify) { $pgArgs += "--verify" }
& $python @pgArgs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n== Backup ChromaDB =="
$chromaScript = Join-Path $root "scripts\backup_chroma.py"
& $python $chromaScript
exit $LASTEXITCODE
} finally {
    Stop-Transcript | Out-Null
    Write-Host "Log: $logFile"
}
