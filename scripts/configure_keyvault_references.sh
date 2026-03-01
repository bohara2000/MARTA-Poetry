#!/bin/bash

# Configure Key Vault references in App Service and Function App
# This allows apps to automatically pull secrets from Key Vault

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

RESOURCE_GROUP="MartaPoetryRG"
WEB_APP_NAME="marta-poetry-app"
FUNCTION_APP_NAME="marta-poetry-functions"

echo -e "${YELLOW}Configuring Key Vault References${NC}"
echo "===================================="

# Get Key Vault name
echo -e "${YELLOW}Finding Key Vault...${NC}"
KEY_VAULT_NAME=$(az keyvault list --resource-group "$RESOURCE_GROUP" --query "[0].name" -o tsv)

if [ -z "$KEY_VAULT_NAME" ]; then
    echo -e "${RED}No Key Vault found in resource group.${NC}"
    exit 1
fi

echo -e "${GREEN}Key Vault: ${KEY_VAULT_NAME}${NC}"

# Get Key Vault URI
KEY_VAULT_URI=$(az keyvault show --name "$KEY_VAULT_NAME" --resource-group "$RESOURCE_GROUP" --query "properties.vaultUri" -o tsv)
echo -e "${GREEN}Key Vault URI: ${KEY_VAULT_URI}${NC}"

# Enable system-assigned managed identity for Web App
echo -e "${YELLOW}Enabling managed identity for Web App...${NC}"
WEB_APP_IDENTITY=$(az webapp identity assign \
    --name "$WEB_APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query principalId -o tsv)

if [ -z "$WEB_APP_IDENTITY" ]; then
    echo -e "${RED}Failed to enable managed identity for Web App.${NC}"
    exit 1
fi
echo -e "${GREEN}Web App Identity: ${WEB_APP_IDENTITY}${NC}"

# Enable system-assigned managed identity for Function App
echo -e "${YELLOW}Enabling managed identity for Function App...${NC}"
FUNCTION_APP_IDENTITY=$(az functionapp identity assign \
    --name "$FUNCTION_APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query principalId -o tsv)

if [ -z "$FUNCTION_APP_IDENTITY" ]; then
    echo -e "${RED}Failed to enable managed identity for Function App.${NC}"
    exit 1
fi
echo -e "${GREEN}Function App Identity: ${FUNCTION_APP_IDENTITY}${NC}"

# Grant Key Vault access to Web App
echo -e "${YELLOW}Granting Key Vault access to Web App...${NC}"
az keyvault set-policy \
    --name "$KEY_VAULT_NAME" \
    --object-id "$WEB_APP_IDENTITY" \
    --secret-permissions get list

# Grant Key Vault access to Function App
echo -e "${YELLOW}Granting Key Vault access to Function App...${NC}"
az keyvault set-policy \
    --name "$KEY_VAULT_NAME" \
    --object-id "$FUNCTION_APP_IDENTITY" \
    --secret-permissions get list

# Configure Web App settings with Key Vault references
echo -e "${YELLOW}Configuring Web App settings with Key Vault references...${NC}"
az webapp config appsettings set \
    --name "$WEB_APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --settings \
        "COSMOS_ENDPOINT=@Microsoft.KeyVault(SecretUri=${KEY_VAULT_URI}secrets/CosmosDbEndpoint/)" \
        "COSMOS_KEY=@Microsoft.KeyVault(SecretUri=${KEY_VAULT_URI}secrets/CosmosDbKey/)" \
        "COSMOS_DATABASE=PoetryDatabase" \
        "COSMOS_CONTAINER_POEMS=poems" \
        "COSMOS_CONTAINER_ROUTES=routes" \
        "COSMOS_CONTAINER_PERSONALITIES=personalities" \
        "COSMOS_CONTAINER_GRAPH=graph" \
        "COSMOS_CONTAINER=poems" \
        "STORAGE_ACCOUNT_NAME=@Microsoft.KeyVault(SecretUri=${KEY_VAULT_URI}secrets/StorageAccountName/)" \
        "STORAGE_ACCOUNT_KEY=@Microsoft.KeyVault(SecretUri=${KEY_VAULT_URI}secrets/StorageAccountKey/)" \
        "STORAGE_CONNECTION_STRING=@Microsoft.KeyVault(SecretUri=${KEY_VAULT_URI}secrets/StorageAccountConnectionString/)" \
        "AUDIO_CONTAINER_NAME=audio"

# Configure Function App settings with Key Vault references
echo -e "${YELLOW}Configuring Function App settings with Key Vault references...${NC}"
az functionapp config appsettings set \
    --name "$FUNCTION_APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --settings \
        "COSMOS_ENDPOINT=@Microsoft.KeyVault(SecretUri=${KEY_VAULT_URI}secrets/CosmosDbEndpoint/)" \
        "COSMOS_KEY=@Microsoft.KeyVault(SecretUri=${KEY_VAULT_URI}secrets/CosmosDbKey/)" \
        "COSMOS_DATABASE=PoetryDatabase" \
        "COSMOS_CONTAINER_POEMS=poems" \
        "COSMOS_CONTAINER_ROUTES=routes" \
        "COSMOS_CONTAINER_PERSONALITIES=personalities" \
        "COSMOS_CONTAINER_GRAPH=graph" \
        "COSMOS_CONTAINER=poems" \
        "STORAGE_ACCOUNT_NAME=@Microsoft.KeyVault(SecretUri=${KEY_VAULT_URI}secrets/StorageAccountName/)" \
        "STORAGE_ACCOUNT_KEY=@Microsoft.KeyVault(SecretUri=${KEY_VAULT_URI}secrets/StorageAccountKey/)" \
        "STORAGE_CONNECTION_STRING=@Microsoft.KeyVault(SecretUri=${KEY_VAULT_URI}secrets/StorageAccountConnectionString/)" \
        "AUDIO_CONTAINER_NAME=audio"

echo -e "${GREEN}Key Vault references configured successfully!${NC}"
echo ""
echo -e "${YELLOW}Verification:${NC}"
echo "1. Web App and Function App now have managed identities"
echo "2. Both identities have 'get' and 'list' permissions on Key Vault secrets"
echo "3. App settings use Key Vault references for COSMOS_ENDPOINT and COSMOS_KEY"
echo "4. Non-secret values (database/container names) are set directly"
echo ""
echo -e "${GREEN}Apps will now automatically pull secrets from Key Vault at runtime!${NC}"
