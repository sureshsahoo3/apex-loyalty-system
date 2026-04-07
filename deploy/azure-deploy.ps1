<#
.SYNOPSIS
    Deploy Apex Loyalty System to Azure Container Apps.

.DESCRIPTION
    Creates all required Azure resources and deploys both backend (FastAPI)
    and frontend (Angular) as Container Apps, then outputs the public URLs.

.PARAMETER ResourceGroup
    Azure resource group name. Default: apex-loyalty-rg

.PARAMETER Location
    Azure region. Default: eastus

.PARAMETER AcrName
    Azure Container Registry name (must be globally unique). Default: apexloyaltyacr

.PARAMETER AnthropicApiKey
    Optional Anthropic API key to enable Claude AI agent mode.

.EXAMPLE
    .\azure-deploy.ps1 -AnthropicApiKey "sk-ant-..."
    .\azure-deploy.ps1 -ResourceGroup "my-rg" -Location "westeurope"
#>

param(
    [string]$ResourceGroup   = "apex-loyalty-rg",
    [string]$Location        = "eastus",
    [string]$AcrName         = "apexloyaltyacr",
    [string]$EnvName         = "apex-loyalty-env",
    [string]$BackendAppName  = "apex-loyalty-backend",
    [string]$FrontendAppName = "apex-loyalty-frontend",
    [string]$AnthropicApiKey = ""
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

function Log-Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Log-Ok($msg)   { Write-Host "    $msg" -ForegroundColor Green }
function Log-Warn($msg) { Write-Host "    $msg" -ForegroundColor Yellow }

# ── 1. Pre-flight checks ─────────────────────────────────────────────
Log-Step "Pre-flight checks"

if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    throw "Azure CLI not found. Install from https://aka.ms/installazurecliwindows"
}
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker not found. Install Docker Desktop from https://www.docker.com"
}

$account = az account show 2>$null | ConvertFrom-Json
if (-not $account) {
    Log-Warn "Not logged in to Azure. Running 'az login'..."
    az login | Out-Null
}
Log-Ok "Logged in as: $($account.user.name) | Subscription: $($account.name)"

# ── 2. Resource Group ────────────────────────────────────────────────
Log-Step "Creating resource group: $ResourceGroup ($Location)"
az group create --name $ResourceGroup --location $Location --output none
Log-Ok "Resource group ready"

# ── 3. Azure Container Registry ──────────────────────────────────────
Log-Step "Creating Azure Container Registry: $AcrName"
az acr create `
    --resource-group $ResourceGroup `
    --name $AcrName `
    --sku Basic `
    --admin-enabled true `
    --output none
Log-Ok "ACR created"

$AcrLoginServer = (az acr show --name $AcrName --query loginServer -o tsv)
$AcrPassword    = (az acr credential show --name $AcrName --query "passwords[0].value" -o tsv)
Log-Ok "ACR server: $AcrLoginServer"

# ── 4. Build & push backend image ────────────────────────────────────
Log-Step "Building backend Docker image"
$BackendImage = "$AcrLoginServer/apex-loyalty-backend:latest"
docker build `
    -f "$ProjectRoot/backend/Dockerfile" `
    -t $BackendImage `
    $ProjectRoot
Log-Ok "Backend image built: $BackendImage"

Log-Step "Pushing backend image to ACR"
docker login $AcrLoginServer -u $AcrName -p $AcrPassword
docker push $BackendImage
Log-Ok "Backend image pushed"

# ── 5. Create Container Apps Environment ─────────────────────────────
Log-Step "Creating Container Apps environment: $EnvName"
az containerapp env create `
    --name $EnvName `
    --resource-group $ResourceGroup `
    --location $Location `
    --output none
Log-Ok "Container Apps environment ready"

# ── 6. Deploy Backend Container App ──────────────────────────────────
Log-Step "Deploying backend container app: $BackendAppName"

$envVars = "PYTHONUNBUFFERED=1"
if ($AnthropicApiKey) {
    $envVars += " ANTHROPIC_API_KEY=$AnthropicApiKey"
    Log-Ok "Claude AI mode enabled"
} else {
    Log-Warn "No Anthropic API key — running in Rule Engine mode"
}

az containerapp create `
    --name $BackendAppName `
    --resource-group $ResourceGroup `
    --environment $EnvName `
    --image $BackendImage `
    --registry-server $AcrLoginServer `
    --registry-username $AcrName `
    --registry-password $AcrPassword `
    --target-port 8080 `
    --ingress external `
    --cpu 0.5 `
    --memory 1.0Gi `
    --min-replicas 1 `
    --max-replicas 3 `
    --env-vars $envVars `
    --output none

$BackendUrl = "https://$(az containerapp show --name $BackendAppName --resource-group $ResourceGroup --query properties.configuration.ingress.fqdn -o tsv)"
Log-Ok "Backend deployed: $BackendUrl"

# ── 7. Build & push frontend image (with backend URL injected) ────────
Log-Step "Building frontend Docker image (API_URL=$BackendUrl)"
$FrontendImage = "$AcrLoginServer/apex-loyalty-frontend:latest"
docker build `
    -f "$ProjectRoot/frontend/Dockerfile" `
    --build-arg "API_URL=$BackendUrl" `
    -t $FrontendImage `
    "$ProjectRoot/frontend"
Log-Ok "Frontend image built: $FrontendImage"

Log-Step "Pushing frontend image to ACR"
docker push $FrontendImage
Log-Ok "Frontend image pushed"

# ── 8. Deploy Frontend Container App ─────────────────────────────────
Log-Step "Deploying frontend container app: $FrontendAppName"
az containerapp create `
    --name $FrontendAppName `
    --resource-group $ResourceGroup `
    --environment $EnvName `
    --image $FrontendImage `
    --registry-server $AcrLoginServer `
    --registry-username $AcrName `
    --registry-password $AcrPassword `
    --target-port 80 `
    --ingress external `
    --cpu 0.25 `
    --memory 0.5Gi `
    --min-replicas 1 `
    --max-replicas 2 `
    --output none

$FrontendUrl = "https://$(az containerapp show --name $FrontendAppName --resource-group $ResourceGroup --query properties.configuration.ingress.fqdn -o tsv)"
Log-Ok "Frontend deployed: $FrontendUrl"

# ── 9. Summary ────────────────────────────────────────────────────────
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host " Deployment Complete!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host ""
Write-Host "  Frontend (UI)  : $FrontendUrl" -ForegroundColor White
Write-Host "  Backend (API)  : $BackendUrl"  -ForegroundColor White
Write-Host "  Health check   : $BackendUrl/health" -ForegroundColor Gray
Write-Host "  API endpoint   : $BackendUrl/api/high-risk-customers" -ForegroundColor Gray
Write-Host ""
Write-Host "  Resource Group : $ResourceGroup" -ForegroundColor Gray
Write-Host "  ACR            : $AcrLoginServer" -ForegroundColor Gray
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
