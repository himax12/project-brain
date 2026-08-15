# Local CockroachDB (insecure single-node). For Cloud, skip this and set DATABASE_URL from the console.

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

Write-Host "Starting CockroachDB via docker compose..."
docker compose up -d

$envFile = Join-Path $PWD ".env"
$url = "postgresql://root@localhost:26257/defaultdb?sslmode=disable"
if (-not (Test-Path $envFile)) {
  Copy-Item ".env.example" $envFile
}
$raw = Get-Content $envFile -Raw
if ($raw -match "DATABASE_URL=") {
  $raw = [regex]::Replace($raw, "DATABASE_URL=.*", "DATABASE_URL=$url", 1)
  Set-Content -Path $envFile -Value $raw -NoNewline
}

Write-Host "Waiting for SQL on 26257..."
$ok = $false
for ($i = 0; $i -lt 30; $i++) {
  try {
    docker compose exec -T cockroach ./cockroach sql --insecure -e "SELECT 1" | Out-Null
    $ok = $true
    break
  } catch {
    Start-Sleep -Seconds 2
  }
}
if (-not $ok) { throw "CockroachDB did not become ready" }

Write-Host "DATABASE_URL=$url"
Write-Host "Next: cd apps\api; uv sync --extra dev; uv run python ..\..\scripts\migrate.py; uv run python ..\..\scripts\smoke_v0.py"
