param (
    [switch]$SkipApiEnable = $false
)

$ErrorActionPreference = "Stop"

$ProjectID = "tcc-performance-2026"
$Region = "us-central1"
$Zone = "us-central1-a"
$RepoName = "tcc-benchmarks"
$ClusterName = "tcc-cluster"
$RegistryURL = "$Region-docker.pkg.dev/$ProjectID/$RepoName"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Iniciando Provisionamento GKE - TCC" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Ativar APIs (se não pular)
if (-not $SkipApiEnable) {
    Write-Host "`n[1/5] Habilitando APIs (isso pode demorar minutos)..." -ForegroundColor Yellow
    gcloud services enable container.googleapis.com artifactregistry.googleapis.com compute.googleapis.com
} else {
    Write-Host "`n[1/5] Habilitando APIs: PULADO (-SkipApiEnable)" -ForegroundColor Yellow
}

# 2. Configurar Artifact Registry
Write-Host "`n[2/5] Configurando Artifact Registry e autenticando Docker..." -ForegroundColor Yellow

$ErrorActionPreference = "Continue"
$repoExists = gcloud artifacts repositories describe $RepoName --location=$Region --format="value(name)" 2>$null
$ErrorActionPreference = "Stop"

if (-not $repoExists) {
    Write-Host " -> Criando repositório $RepoName..."
    gcloud artifacts repositories create $RepoName --repository-format=docker --location=$Region --description="TCC Performance Comparison Images"
} else {
    Write-Host " Repositório $RepoName já existe."
}
gcloud auth configure-docker "$Region-docker.pkg.dev" --quiet

# 3. Build & Push
Write-Host "`n[3/5] Fazendo Build multi-arch e Push das imagens Docker..." -ForegroundColor Yellow

$Images = @("backend-java", "backend-go", "backend-quarkus", "mock-external-api")

foreach ($Img in $Images) {
    Write-Host " -> Build e Push: $Img"
    $AppDir = if ($Img -eq "mock-external-api") { "mock-external-api" } else { $Img }
    $ImgName = if ($Img -eq "mock-external-api") { "mock-api" } else { $Img }
    
    docker buildx build --platform linux/amd64 -t "$RegistryURL/$ImgName:latest" --push "./apps/$AppDir/"
}

# 4. Criar Cluster e Node Pool
Write-Host "`n[4/5] Criando Cluster GKE e Node Pool..." -ForegroundColor Yellow

$ErrorActionPreference = "Continue"
$clusterExists = gcloud container clusters describe $ClusterName --zone $Zone --format="value(name)" 2>$null
$ErrorActionPreference = "Stop"

if (-not $clusterExists) {
    Write-Host " -> Criando cluster base ($ClusterName)..."
    gcloud container clusters create $ClusterName --zone $Zone --num-nodes 1 --machine-type e2-standard-2 --disk-size 30 --no-enable-autoupgrade
} else {
    Write-Host " Cluster $ClusterName já existe."
}

$ErrorActionPreference = "Continue"
$poolExists = gcloud container node-pools describe benchmark-pool --cluster $ClusterName --zone $Zone --format="value(name)" 2>$null
$ErrorActionPreference = "Stop"

if (-not $poolExists) {
    Write-Host " -> Criando Node Pool de benchmark..."
    gcloud container node-pools create benchmark-pool --cluster $ClusterName --zone $Zone --machine-type e2-standard-4 --num-nodes 1 --node-labels role=benchmark --disk-size 30
} else {
    Write-Host " Node pool benchmark-pool já existe."
}

# Obter credenciais K8s
Write-Host " -> Obtendo credenciais do Kubernetes..."
gcloud container clusters get-credentials $ClusterName --zone $Zone

# 5. Aplicar Manifests
Write-Host "`n[5/5] Aplicando Manifests Kubernetes..." -ForegroundColor Yellow
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/infra/
kubectl apply -f k8s/backends/
kubectl apply -f k8s/observability/
kubectl apply -f k8s/jobs/k6-job.yaml

Write-Host "`n============================================================" -ForegroundColor Green
Write-Host " PROVISIONAMENTO CONCLUÍDO COM SUCESSO!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host "Para acompanhar a saúde do cluster, execute: kubectl get pods -n tcc"
Write-Host "Quando todos os pods estiverem rodando, você pode iniciar os testes com:"
Write-Host "bash scripts/benchmarks/run_benchmarks_gke.sh"
