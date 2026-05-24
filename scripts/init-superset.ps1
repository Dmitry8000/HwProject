$container = "rugby-superset"

Write-Host "Waiting for $container..."
$deadline = (Get-Date).AddMinutes(4)
while ((Get-Date) -lt $deadline) {
    $running = docker inspect -f '{{.State.Running}}' $container 2>$null
    if ($running -eq "true") { break }
    Start-Sleep -Seconds 2
}
if ((docker inspect -f '{{.State.Running}}' $container 2>$null) -ne "true") {
    throw "Container $container is not running"
}

Start-Sleep -Seconds 8
$oldEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"

docker exec $container superset db upgrade
docker exec $container superset fab create-admin `
    --username admin --firstname Admin --lastname User `
    --email admin@local.test --password admin
docker exec $container superset init

$ErrorActionPreference = $oldEap
Write-Host "Superset ready: http://localhost:18088"
