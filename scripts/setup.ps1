# Полная настройка после docker compose up -d --build
# Запуск из каталога Project: .\scripts\setup.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "=== Rugby Project setup ===" -ForegroundColor Cyan

Write-Host "Starting containers..."
docker compose up -d --build

$ch = "rugby-clickhouse"
$deadline = (Get-Date).AddMinutes(5)
Write-Host "Waiting for ClickHouse..."
while ((Get-Date) -lt $deadline) {
    $ok = docker exec $ch clickhouse-client --query "SELECT 1" 2>$null
    if ($LASTEXITCODE -eq 0) { break }
    Start-Sleep -Seconds 3
}
if ($LASTEXITCODE -ne 0) { throw "ClickHouse not ready" }

function Invoke-ChSql($file) {
    Write-Host "  SQL: $file"
    $base = Split-Path -Leaf $file
    docker cp $file "${ch}:/tmp/$base" | Out-Null
    docker exec $ch bash -c "clickhouse-client --multiquery < /tmp/$base"
    if ($LASTEXITCODE -ne 0) { throw "Failed: $file" }
}

Start-Sleep -Seconds 10
Write-Host "Applying Kafka pipeline and marts..."
Invoke-ChSql "sql\01_kafka_pipeline.sql"
Invoke-ChSql "sql\02_seed_dimensions.sql"
Invoke-ChSql "sql\03_marts.sql"

Write-Host "Initializing Superset (admin/admin)..."
& "$PSScriptRoot\init-superset.ps1"

Write-Host ""
Write-Host "Setup complete." -ForegroundColor Green
Write-Host "Next: docs\QUICKSTART.md (stream + bootstrap)" -ForegroundColor Cyan
Write-Host "  ClickHouse HTTP: http://localhost:28123"
Write-Host "  Grafana:         http://localhost:3000  (admin/admin) -> Rugby Platform - monitoring"
Write-Host "  Prometheus:      http://localhost:19090 -> Status / Targets"
Write-Host "  Superset:        http://localhost:18088 (admin/admin)"
Write-Host ""
Write-Host "Stream demo match:"
Write-Host "  cd producer"
Write-Host "  pip install -r requirements.txt"
Write-Host "  python stream_match.py --fresh"
Write-Host ""
Write-Host "Superset dashboard:"
Write-Host "  pip install -r scripts\requirements.txt"
Write-Host "  python scripts\bootstrap_superset_dashboard.py"
Write-Host ""
Write-Host "Verify:"
Write-Host "  .\scripts\verify.ps1"
Write-Host "  .\scripts\verify-monitoring.ps1"
