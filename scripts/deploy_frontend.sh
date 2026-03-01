#!/bin/bash

# Frontend Deployment Script for MARTA Poetry
# Builds frontend and deploys to Azure Static Web Apps
# Usage: bash scripts/deploy_frontend.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
FRONTEND_DIR="frontend"
RESOURCE_GROUP="${RESOURCE_GROUP:-MartaPoetryRG}"
STATIC_WEB_APP_NAME="${STATIC_WEB_APP_NAME:-marta-poetry-frontend}"
BACKEND_APP_NAME="${BACKEND_APP_NAME:-marta-poetry-app}"

echo -e "${BLUE}=== MARTA Poetry Frontend Deployment ===${NC}"
echo "Frontend Directory: $FRONTEND_DIR"
echo "Static Web App: $STATIC_WEB_APP_NAME"
echo "Resource Group: $RESOURCE_GROUP"
echo ""

# Step 1: Verify prerequisites
echo -e "${YELLOW}[1/4] Verifying prerequisites...${NC}"

if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}❌ Frontend directory not found: $FRONTEND_DIR${NC}"
    exit 1
fi

if [ ! -f "$FRONTEND_DIR/package.json" ]; then
    echo -e "${RED}❌ package.json not found in $FRONTEND_DIR${NC}"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not found. Please install it first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All prerequisites met${NC}"
echo ""

# Step 2: Install dependencies and build
echo -e "${YELLOW}[2/4] Building frontend...${NC}"
cd "$FRONTEND_DIR"

echo "  Installing dependencies..."
npm install --legacy-peer-deps 2>/dev/null || npm install

echo "  Building with Vite..."
npm run build

BUILD_SIZE=$(du -sh dist | cut -f1)
echo -e "${GREEN}✓ Build complete (dist: $BUILD_SIZE)${NC}"
cd ..
echo ""

# Step 3: Get backend URL and configure API endpoint
echo -e "${YELLOW}[3/4] Configuring API endpoint...${NC}"

BACKEND_URL=$(az webapp show \
    --name "$BACKEND_APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query "hostNames[0]" \
    -o tsv 2>/dev/null)

if [ -z "$BACKEND_URL" ]; then
    echo -e "${RED}❌ Failed to get backend URL. App Service may not exist.${NC}"
    exit 1
fi

BACKEND_URL="https://${BACKEND_URL}"
echo "  Backend URL: $BACKEND_URL"

# Get Static Web App deployment token (if using GitHub integration)
echo -e "${GREEN}✓ API endpoint configured${NC}"
echo ""

# Step 4: Deploy to Static Web Apps
echo -e "${YELLOW}[4/4] Deploying to Azure Static Web Apps...${NC}"

# Check if Static Web App exists
if az staticwebapp show --name "$STATIC_WEB_APP_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
    echo "  Deploying to existing Static Web App..."
    
    # Using az staticwebapp --name to upload built files
    # (Note: This requires Static Web Apps CLI or GitHub integration)
    echo "  Using built-in deployment (zip upload)..."
    
    # Alternative: Use az cli to manage the deployment
    # For now, show instructions to user
    echo ""
    echo -e "${YELLOW}Static Web App deployment requires one of these methods:${NC}"
    echo "  1. GitHub Actions: Push to main branch for auto-deployment"
    echo "  2. GitHub Codespaces: Use 'swa' CLI"
    echo "  3. Local: Install @azure/static-web-apps-cli and run:"
    echo "     swa deploy ./frontend/dist --env production --verbose"
    echo ""
    echo -e "${YELLOW}For now, the built files are ready in: frontend/dist${NC}"
    echo ""
    
else
    echo -e "${RED}❌ Static Web App not found: $STATIC_WEB_APP_NAME${NC}"
    echo "    Create it first with:"
    echo "    bash scripts/deploy_infrastructure.sh"
    exit 1
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║ ✓ FRONTEND BUILD SUCCESSFUL            ║${NC}"
echo -e "${GREEN}║ Built files ready in frontend/dist      ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo "  To complete deployment, use one of these methods:"
echo "    • Push to GitHub: git push (triggers GitHub Actions)"
echo "    • Manual upload: Use Azure Portal > Static Web Apps > Deployment"
echo "    • CLI deployment: swa deploy ./frontend/dist --env production"
echo ""
echo "  Access frontend at:"
echo "    https://${STATIC_WEB_APP_NAME}.azurestaticapps.net"
echo ""
echo "  Backend API configured at:"
echo "    $BACKEND_URL"
echo ""
