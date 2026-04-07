#!/usr/bin/env bash
# Deploy Apex Loyalty System to Azure Container Apps
# Usage: ./deploy/azure-deploy.sh [--api-key sk-ant-...]
set -euo pipefail

# ── Config (override via env vars) ───────────────────────────────────
RESOURCE_GROUP="${RESOURCE_GROUP:-apex-loyalty-rg}"
LOCATION="${LOCATION:-eastus}"
ACR_NAME="${ACR_NAME:-apexloyaltyacr}"
ENV_NAME="${ENV_NAME:-apex-loyalty-env}"
BACKEND_APP="${BACKEND_APP:-apex-loyalty-backend}"
FRONTEND_APP="${FRONTEND_APP:-apex-loyalty-frontend}"
ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-}"

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

while [[ $# -gt 0 ]]; do
  case $1 in
    --api-key) ANTHROPIC_API_KEY="$2"; shift 2 ;;
    --resource-group) RESOURCE_GROUP="$2"; shift 2 ;;
    --location) LOCATION="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

log()  { echo -e "\n\033[0;36m==> $*\033[0m"; }
ok()   { echo -e "    \033[0;32m$*\033[0m"; }
warn() { echo -e "    \033[0;33m$*\033[0m"; }

# ── 1. Pre-flight ─────────────────────────────────────────────────────
log "Pre-flight checks"
command -v az     >/dev/null || { echo "Azure CLI not found. Install: https://aka.ms/installazurecli"; exit 1; }
command -v docker >/dev/null || { echo "Docker not found."; exit 1; }
az account show >/dev/null 2>&1 || { warn "Not logged in — running az login"; az login; }
ok "Azure CLI ready: $(az account show --query user.name -o tsv)"

# ── 2. Resource Group ─────────────────────────────────────────────────
log "Creating resource group: $RESOURCE_GROUP ($LOCATION)"
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --output none
ok "Resource group ready"

# ── 3. Azure Container Registry ───────────────────────────────────────
log "Creating ACR: $ACR_NAME"
az acr create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$ACR_NAME" \
    --sku Basic \
    --admin-enabled true \
    --output none

ACR_SERVER=$(az acr show --name "$ACR_NAME" --query loginServer -o tsv)
ACR_PASS=$(az acr credential show --name "$ACR_NAME" --query "passwords[0].value" -o tsv)
ok "ACR ready: $ACR_SERVER"

# ── 4. Backend image ──────────────────────────────────────────────────
log "Building backend Docker image"
BACKEND_IMAGE="$ACR_SERVER/apex-loyalty-backend:latest"
docker build -f "$PROJECT_ROOT/backend/Dockerfile" -t "$BACKEND_IMAGE" "$PROJECT_ROOT"
docker login "$ACR_SERVER" -u "$ACR_NAME" -p "$ACR_PASS"
docker push "$BACKEND_IMAGE"
ok "Backend image pushed: $BACKEND_IMAGE"

# ── 5. Container Apps Environment ─────────────────────────────────────
log "Creating Container Apps environment: $ENV_NAME"
az containerapp env create \
    --name "$ENV_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --output none
ok "Environment ready"

# ── 6. Deploy backend ─────────────────────────────────────────────────
log "Deploying backend: $BACKEND_APP"
ENV_VARS="PYTHONUNBUFFERED=1"
if [[ -n "$ANTHROPIC_API_KEY" ]]; then
    ENV_VARS="$ENV_VARS ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY"
    ok "Claude AI mode enabled"
else
    warn "No API key — running in Rule Engine mode"
fi

az containerapp create \
    --name "$BACKEND_APP" \
    --resource-group "$RESOURCE_GROUP" \
    --environment "$ENV_NAME" \
    --image "$BACKEND_IMAGE" \
    --registry-server "$ACR_SERVER" \
    --registry-username "$ACR_NAME" \
    --registry-password "$ACR_PASS" \
    --target-port 8080 \
    --ingress external \
    --cpu 0.5 --memory 1.0Gi \
    --min-replicas 1 --max-replicas 3 \
    --env-vars $ENV_VARS \
    --output none

BACKEND_FQDN=$(az containerapp show --name "$BACKEND_APP" --resource-group "$RESOURCE_GROUP" --query properties.configuration.ingress.fqdn -o tsv)
BACKEND_URL="https://$BACKEND_FQDN"
ok "Backend live: $BACKEND_URL"

# ── 7. Frontend image (with backend URL injected) ─────────────────────
log "Building frontend image (API_URL=$BACKEND_URL)"
FRONTEND_IMAGE="$ACR_SERVER/apex-loyalty-frontend:latest"
docker build \
    -f "$PROJECT_ROOT/frontend/Dockerfile" \
    --build-arg "API_URL=$BACKEND_URL" \
    -t "$FRONTEND_IMAGE" \
    "$PROJECT_ROOT/frontend"
docker push "$FRONTEND_IMAGE"
ok "Frontend image pushed: $FRONTEND_IMAGE"

# ── 8. Deploy frontend ────────────────────────────────────────────────
log "Deploying frontend: $FRONTEND_APP"
az containerapp create \
    --name "$FRONTEND_APP" \
    --resource-group "$RESOURCE_GROUP" \
    --environment "$ENV_NAME" \
    --image "$FRONTEND_IMAGE" \
    --registry-server "$ACR_SERVER" \
    --registry-username "$ACR_NAME" \
    --registry-password "$ACR_PASS" \
    --target-port 80 \
    --ingress external \
    --cpu 0.25 --memory 0.5Gi \
    --min-replicas 1 --max-replicas 2 \
    --output none

FRONTEND_FQDN=$(az containerapp show --name "$FRONTEND_APP" --resource-group "$RESOURCE_GROUP" --query properties.configuration.ingress.fqdn -o tsv)
FRONTEND_URL="https://$FRONTEND_FQDN"
ok "Frontend live: $FRONTEND_URL"

# ── 9. Summary ────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Deployment Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Frontend (UI)  : $FRONTEND_URL"
echo "  Backend (API)  : $BACKEND_URL"
echo "  Health check   : $BACKEND_URL/health"
echo "  API endpoint   : $BACKEND_URL/api/high-risk-customers"
echo ""
echo "  Resource Group : $RESOURCE_GROUP"
echo "  ACR            : $ACR_SERVER"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
