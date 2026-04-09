param(
  [string]$HostUrl = "http://localhost:8000",
  [int]$Users = 10,
  [int]$SpawnRate = 2,
  [int]$RunTimeSec = 120,
  [int]$Products = 30,
  [int]$BuyerPoolSize = 200,
  [string]$DbPath = "..\..\data\deliverinno.db"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "==> Init test users/products in SQLite..."
poetry run python .\init_test_users.py --db-path $DbPath --products $Products --buyer-pool-size $BuyerPoolSize
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> Starting locust..."
poetry run locust `
  -f .\locustfile.py `
  --host $HostUrl `
  --headless `
  -u $Users `
  -r $SpawnRate `
  -t "${RunTimeSec}s"
