$ErrorActionPreference = "Stop"
Write-Host "1. Iniciando provisionamento GKE..."
.\scripts\infra\provision_gke.ps1

Write-Host "2. Aguardando estabilizacao (30s)..."
Start-Sleep -Seconds 30

Write-Host "3. Executando bateria completa de benchmarks (3 rodadas)..."
bash scripts/benchmarks/run_benchmarks_gke.sh --rounds 3

Write-Host "4. Benchmark concluido com sucesso!"
