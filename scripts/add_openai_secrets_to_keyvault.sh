#!/bin/bash

# Add OpenAI credentials to Azure Key Vault and configure app settings
# This script:
#   1. Reads OpenAI API keys from local .env file
#   2. Stores them securely in Azure Key Vault
#   3. Updates App Service and Function App settings with Key Vault references

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

RESOURCE_GROUP="MartaPoetryRG"
WEB_APP_NAME="marta-poetry-app"
FUNCTION_APP_NAME="marta-poetry-functions"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_DIR/backend"

echo -e "${YELLOW}Adding OpenAI Secrets to Key Vault${NC}"
echo "====================================="

# ==================== LOAD .ENV FILE ====================
echo -e "${YELLOW}Loading OpenAI credentials from .env...${NC}"

if [ ! -f "$BACKEND_DIR/.env" ]; then
    echo -e "${RED}Error: .env file not found at $BACKEND_DIR/.env${NC}"
    echo -e "${YELLOW}Please run this script from the project root directory${NC}"
    exit 1
fi

# Source the .env file carefully (only get variables we need)
AZURE_OPENAI_API_KEY=$(grep "^AZURE_OPENAI_API_KEY=" "$BACKEND_DIR/.env" | cut -d '=' -f 2-)
AZURE_OPENAI_ENDPOINT=$(grep "^AZURE_OPENAI_ENDPOINT=" "$BACKEND_DIR/.env" | cut -d '=' -f 2-)
AZURE_OPENAI_DEPLOYMENT_NAME=$(grep "^AZURE_OPENAI_DEPLOYMENT_NAME=" "$BACKEND_DIR/.env" | cut -d '=' -f 2-)
AZURE_OPENAI_API_VERSION=$(grep "^AZURE_OPENAI_API_VERSION=" "$BACKEND_DIR/.env" | cut -d '=' -f 2-)
AZURE_OPENAI_API_KEY_TITLES=$(grep "^AZURE_OPENAI_API_KEY_TITLES=" "$BACKEND_DIR/.env" | cut -d '=' -f 2-)
AZURE_OPENAI_ENDPOINT_TITLES=$(grep "^AZURE_OPENAI_ENDPOINT_TITLES=" "$BACKEND_DIR/.env" | cut -d '=' -f 2-)
OPENAI_API_KEY=$(grep "^OPENAI_API_KEY=" "$BACKEND_DIR/.env" | cut -d '=' -f 2-)
MAPBOX_ACCESS_TOKEN=$(grep "^MAPBOX_ACCESS_TOKEN=" "$BACKEND_DIR/.env" | cut -d '=' -f 2-)
GTFS_API_KEY=$(grep "^GTFS_API_KEY=" "$BACKEND_DIR/.env" | cut -d '=' -f 2-)
GTFS_RT_API_KEY=$(grep "^GTFS_RT_API_KEY=" "$BACKEND_DIR/.env" | cut -d '=' -f 2-)
RAIL_RT_API_KEY=$(grep "^RAIL_RT_API_KEY=" "$BACKEND_DIR/.env" | cut -d '=' -f 2-)

# Validate required OpenAI variables
REQUIRED_VARS=(
    "AZURE_OPENAI_API_KEY"
    "AZURE_OPENAI_ENDPOINT"
    "AZURE_OPENAI_DEPLOYMENT_NAME"
    "AZURE_OPENAI_API_VERSION"
)

MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo -e "${RED}Missing required environment variables:${NC}"
    printf '%s\n' "${MISSING_VARS[@]}"
    echo -e "${YELLOW}Please set these in your .env file before running this script.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Found OpenAI credentials${NC}"

# ==================== GET KEY VAULT ====================
echo -e "${YELLOW}Finding Key Vault...${NC}"
KEY_VAULT_NAME=$(az keyvault list --resource-group "$RESOURCE_GROUP" --query "[0].name" -o tsv)

if [ -z "$KEY_VAULT_NAME" ]; then
    echo -e "${RED}No Key Vault found in resource group.${NC}"
    exit 1
fi

echo -e "${GREEN}Key Vault: ${KEY_VAULT_NAME}${NC}"

KEY_VAULT_URI=$(az keyvault show --name "$KEY_VAULT_NAME" --resource-group "$RESOURCE_GROUP" --query "properties.vaultUri" -o tsv)
echo -e "${GREEN}Key Vault URI: ${KEY_VAULT_URI}${NC}"

# ==================== ADD SECRETS TO KEY VAULT ====================
echo ""
echo -e "${YELLOW}Storing OpenAI secrets in Key Vault...${NC}"

# Azure OpenAI - Primary endpoint
az keyvault secret set \
    --vault-name "$KEY_VAULT_NAME" \
    --name "AzureOpenAiApiKey" \
    --value "$AZURE_OPENAI_API_KEY" > /dev/null
echo -e "${GREEN}✓ AzureOpenAiApiKey${NC}"

az keyvault secret set \
    --vault-name "$KEY_VAULT_NAME" \
    --name "AzureOpenAiEndpoint" \
    --value "$AZURE_OPENAI_ENDPOINT" > /dev/null
echo -e "${GREEN}✓ AzureOpenAiEndpoint${NC}"

az keyvault secret set \
    --vault-name "$KEY_VAULT_NAME" \
    --name "AzureOpenAiDeploymentName" \
    --value "$AZURE_OPENAI_DEPLOYMENT_NAME" > /dev/null
echo -e "${GREEN}✓ AzureOpenAiDeploymentName${NC}"

az keyvault secret set \
    --vault-name "$KEY_VAULT_NAME" \
    --name "AzureOpenAiApiVersion" \
    --value "$AZURE_OPENAI_API_VERSION" > /dev/null
echo -e "${GREEN}✓ AzureOpenAiApiVersion${NC}"

# Azure OpenAI - Alternate endpoint for titles (optional)
if [ -n "$AZURE_OPENAI_API_KEY_TITLES" ] && [ "$AZURE_OPENAI_API_KEY_TITLES" != "$AZURE_OPENAI_API_KEY" ]; then
    az keyvault secret set \
        --vault-name "$KEY_VAULT_NAME" \
        --name "AzureOpenAiApiKeyTitles" \
        --value "$AZURE_OPENAI_API_KEY_TITLES" > /dev/null
    echo -e "${GREEN}✓ AzureOpenAiApiKeyTitles${NC}"
fi

if [ -n "$AZURE_OPENAI_ENDPOINT_TITLES" ] && [ "$AZURE_OPENAI_ENDPOINT_TITLES" != "$AZURE_OPENAI_ENDPOINT" ]; then
    az keyvault secret set \
        --vault-name "$KEY_VAULT_NAME" \
        --name "AzureOpenAiEndpointTitles" \
        --value "$AZURE_OPENAI_ENDPOINT_TITLES" > /dev/null
    echo -e "${GREEN}✓ AzureOpenAiEndpointTitles${NC}"
fi

# OpenAI (if using direct OpenAI API)
if [ -n "$OPENAI_API_KEY" ]; then
    az keyvault secret set \
        --vault-name "$KEY_VAULT_NAME" \
        --name "OpenAiApiKey" \
        --value "$OPENAI_API_KEY" > /dev/null
    echo -e "${GREEN}✓ OpenAiApiKey${NC}"
fi

# Mapbox token (if present)
if [ -n "$MAPBOX_ACCESS_TOKEN" ]; then
    az keyvault secret set \
        --vault-name "$KEY_VAULT_NAME" \
        --name "MapboxAccessToken" \
        --value "$MAPBOX_ACCESS_TOKEN" > /dev/null
    echo -e "${GREEN}✓ MapboxAccessToken${NC}"
fi

# MARTA API keys (if present)
if [ -n "$GTFS_API_KEY" ]; then
    az keyvault secret set \
        --vault-name "$KEY_VAULT_NAME" \
        --name "GtfsApiKey" \
        --value "$GTFS_API_KEY" > /dev/null
    echo -e "${GREEN}✓ GtfsApiKey${NC}"
fi

if [ -n "$GTFS_RT_API_KEY" ]; then
    az keyvault secret set \
        --vault-name "$KEY_VAULT_NAME" \
        --name "GtfsRtApiKey" \
        --value "$GTFS_RT_API_KEY" > /dev/null
    echo -e "${GREEN}✓ GtfsRtApiKey${NC}"
fi

if [ -n "$RAIL_RT_API_KEY" ]; then
    az keyvault secret set \
        --vault-name "$KEY_VAULT_NAME" \
        --name "RailRtApiKey" \
        --value "$RAIL_RT_API_KEY" > /dev/null
    echo -e "${GREEN}✓ RailRtApiKey${NC}"
fi

# ==================== UPDATE APP SETTINGS ====================
echo ""
echo -e "${YELLOW}Configuring Web App settings with Key Vault references...${NC}"

az webapp config appsettings set \
    --name "$WEB_APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --settings \
        "AZURE_OPENAI_API_KEY=@Microsoft.KeyVault(SecretUri=${KEY_VAULT_URI}secrets/AzureOpenAiApiKey/)" \
        "AZURE_OPENAI_ENDPOINT=@Microsoft.KeyVault(SecretUri=${KEY_VAULT_URI}secrets/AzureOpenAiEndpoint/)" \
        "AZURE_OPENAI_DEPLOYMENT_NAME=@Microsoft.KeyVault(SecretUri=${KEY_VAULT_URI}secrets/AzureOpenAiDeploymentName/)" \
        "AZURE_OPENAI_API_VERSION=@Microsoft.KeyVault(SecretUri=${KEY_VAULT_URI}secrets/AzureOpenAiApiVersion/)" \
        "AZURE_OPENAI_DEPLOYMENT_NAME_TITLES=gpt-4o" \
        "AZURE_OPENAI_API_VERSION_TITLES=2024-12-01-preview" > /dev/null

echo -e "${GREEN}✓ Web App configured${NC}"

echo -e "${YELLOW}Configuring Function App settings with Key Vault references...${NC}"

az functionapp config appsettings set \
    --name "$FUNCTION_APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --settings \
        "AZURE_OPENAI_API_KEY=@Microsoft.KeyVault(SecretUri=${KEY_VAULT_URI}secrets/AzureOpenAiApiKey/)" \
        "AZURE_OPENAI_ENDPOINT=@Microsoft.KeyVault(SecretUri=${KEY_VAULT_URI}secrets/AzureOpenAiEndpoint/)" \
        "AZURE_OPENAI_DEPLOYMENT_NAME=@Microsoft.KeyVault(SecretUri=${KEY_VAULT_URI}secrets/AzureOpenAiDeploymentName/)" \
        "AZURE_OPENAI_API_VERSION=@Microsoft.KeyVault(SecretUri=${KEY_VAULT_URI}secrets/AzureOpenAiApiVersion/)" \
        "AZURE_OPENAI_DEPLOYMENT_NAME_TITLES=gpt-4o" \
        "AZURE_OPENAI_API_VERSION_TITLES=2024-12-01-preview" > /dev/null

echo -e "${GREEN}✓ Function App configured${NC}"

# Configure optional secrets if they exist
if [ -n "$MAPBOX_ACCESS_TOKEN" ]; then
    echo -e "${YELLOW}Configuring Mapbox token...${NC}"
    az webapp config appsettings set \
        --name "$WEB_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --settings "MAPBOX_ACCESS_TOKEN=@Microsoft.KeyVault(SecretUri=${KEY_VAULT_URI}secrets/MapboxAccessToken/)" > /dev/null
    
    az functionapp config appsettings set \
        --name "$FUNCTION_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --settings "MAPBOX_ACCESS_TOKEN=@Microsoft.KeyVault(SecretUri=${KEY_VAULT_URI}secrets/MapboxAccessToken/)" > /dev/null
    echo -e "${GREEN}✓ Mapbox token configured${NC}"
fi

# ==================== SUMMARY ====================
echo ""
echo -e "${GREEN}✓ OpenAI secrets successfully added to Key Vault!${NC}"
echo ""
echo -e "${YELLOW}Summary:${NC}"
echo "- Secrets stored securely in Key Vault: $KEY_VAULT_NAME"
echo "- Web App ($WEB_APP_NAME) updated with Key Vault references"
echo "- Function App ($FUNCTION_APP_NAME) updated with Key Vault references"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Verify secrets in Azure Portal → Key Vault → Secrets"
echo "2. Check app settings in Azure Portal → App Service → Configuration"
echo "3. Restart the Web App and Function App for changes to take effect:"
echo "   az webapp restart --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP"
echo "   az functionapp restart --name $FUNCTION_APP_NAME --resource-group $RESOURCE_GROUP"
echo ""
echo -e "${GREEN}✓ Done!${NC}"
