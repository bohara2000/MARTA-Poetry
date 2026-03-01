#!/bin/bash

# Deploy and Verify Script for MARTA Poetry App
# One-command deployment: zips backend code, deploys to Azure, verifies health
# Usage: bash scripts/deploy_and_verify.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration (can be overridden by env vars)
APP_NAME="${APP_NAME:-marta-poetry-app}"
RESOURCE_GROUP="${RESOURCE_GROUP:-MartaPoetryRG}"
BACKEND_DIR="backend"
ZIP_FILE="$BACKEND_DIR/app.zip"
HEALTH_CHECK_SCRIPT="scripts/post_deploy_health_check.sh"

echo -e "${BLUE}=== MARTA Poetry Deployment & Verification ===${NC}"
echo "App Name: $APP_NAME"
echo "Resource Group: $RESOURCE_GROUP"
echo "Backend Directory: $BACKEND_DIR"
echo ""

# Step 1: Verify prerequisites
echo -e "${YELLOW}[1/4] Verifying prerequisites...${NC}"
if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI not found. Please install it first.${NC}"
    exit 1
fi

if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}❌ Backend directory not found: $BACKEND_DIR${NC}"
    exit 1
fi

if [ ! -f "$HEALTH_CHECK_SCRIPT" ]; then
    echo -e "${RED}❌ Health check script not found: $HEALTH_CHECK_SCRIPT${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All prerequisites met${NC}"
echo ""

# Step 2: Create deployment package
echo -e "${YELLOW}[2/4] Creating deployment package...${NC}"
cd "$BACKEND_DIR"

# Remove old zip if exists
rm -f app.zip

# Create zip with all necessary files
echo "  Zipping backend code..."
zip -r -q app.zip \
    app.py \
    config.py \
    admin_api.py \
    audio_service.py \
    requirements.txt \
    poetry/ \
    services/ \
    storage/ \
    tests/ \
    __pycache__/ 2>/dev/null || true

if [ ! -f "app.zip" ]; then
    echo -e "${RED}❌ Failed to create deployment package${NC}"
    exit 1
fi

ZIP_SIZE=$(du -h app.zip | cut -f1)
echo -e "${GREEN}✓ Created app.zip ($ZIP_SIZE)${NC}"
cd ..
echo ""

# Step 3: Deploy to Azure
echo -e "${YELLOW}[3/4] Deploying to Azure App Service...${NC}"
echo "  Running: az webapp deployment source config-zip --name $APP_NAME --resource-group $RESOURCE_GROUP --src $ZIP_FILE"

if az webapp deployment source config-zip \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --src "$ZIP_FILE" >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Deployment package uploaded successfully${NC}"
else
    echo -e "${RED}❌ Failed to deploy package to App Service${NC}"
    exit 1
fi

echo "  Waiting for App Service to process deployment (10s)..."
sleep 10
echo ""

# Step 4: Verify app health
echo -e "${YELLOW}[4/4] Verifying app health...${NC}"
echo "  Running health check with retries (up to 3 minutes)..."
echo ""

if bash "$HEALTH_CHECK_SCRIPT"; then
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║ ✓ DEPLOYMENT SUCCESSFUL               ║${NC}"
    echo -e "${GREEN}║ App is running and ready for requests  ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
    echo ""
    echo "  Access the app at:"
    echo "    - API docs: https://$APP_NAME.azurewebsites.net/docs"
    echo "    - API root: https://$APP_NAME.azurewebsites.net/"
    echo "    - OpenAPI schema: https://$APP_NAME.azurewebsites.net/openapi.json"
    exit 0
else
    echo ""
    echo -e "${RED}╔════════════════════════════════════════╗${NC}"
    echo -e "${RED}║ ✗ DEPLOYMENT FAILED - HEALTH CHECK     ║${NC}"
    echo -e "${RED}║ App is not responding as expected      ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════╝${NC}"
    echo ""
    echo "  Troubleshooting:"
    echo "    1. Check app logs: az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
    echo "    2. Check app status: az webapp show --name $APP_NAME --resource-group $RESOURCE_GROUP"
    echo "    3. Review configuration: az webapp config show --name $APP_NAME --resource-group $RESOURCE_GROUP"
    echo ""
    exit 1
fi
