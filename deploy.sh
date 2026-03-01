#!/bin/bash

# MARTA Poetry Azure Deployment Script
# Deploys Cosmos DB, Storage Account, and Key Vault using Bicep templates

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
RESOURCE_GROUP="MartaPoetryRG"
LOCATION="eastus"
BICEP_DIR="bicep"
MAIN_TEMPLATE="${BICEP_DIR}/main.bicep"

echo -e "${YELLOW}Starting MARTA Poetry Azure Deployment${NC}"
echo "========================================"

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}Azure CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if user is logged in
if ! az account show &> /dev/null; then
    echo -e "${YELLOW}You are not logged in to Azure. Logging in...${NC}"
    az login
fi

# Display current subscription
CURRENT_SUB=$(az account show --query name -o tsv)
echo -e "${GREEN}Current subscription: ${CURRENT_SUB}${NC}"

# Get the object ID of the current user
echo -e "${YELLOW}Retrieving your Azure object ID...${NC}"
OBJECT_ID=$(az ad signed-in-user show --query id -o tsv 2>/dev/null)
if [ -z "$OBJECT_ID" ]; then
    echo -e "${YELLOW}Could not automatically retrieve object ID. Attempting alternative method...${NC}"
    OBJECT_ID=$(az account show --query user.objectId -o tsv 2>/dev/null)
fi
if [ -z "$OBJECT_ID" ]; then
    echo -e "${YELLOW}Could not automatically retrieve object ID.${NC}"
    echo -e "${YELLOW}Please provide your Azure object ID manually.${NC}"
    echo -e "${YELLOW}You can find it by running: az ad signed-in-user show --query id${NC}"
    read -p "Enter your Azure object ID: " OBJECT_ID
    if [ -z "$OBJECT_ID" ]; then
        echo -e "${RED}Object ID is required. Exiting.${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}Object ID: ${OBJECT_ID}${NC}"

# Check if resource group exists
if ! az group exists --name "$RESOURCE_GROUP" | grep -q true; then
    echo -e "${YELLOW}Resource group '${RESOURCE_GROUP}' does not exist. Creating...${NC}"
    az group create \
        --name "$RESOURCE_GROUP" \
        --location "$LOCATION"
    echo -e "${GREEN}Resource group created.${NC}"
else
    echo -e "${GREEN}Resource group '${RESOURCE_GROUP}' already exists.${NC}"
fi

# Validate Bicep template
echo -e "${YELLOW}Validating Bicep template...${NC}"
az deployment group validate \
    --resource-group "$RESOURCE_GROUP" \
    --template-file "$MAIN_TEMPLATE" \
    --parameters keyVaultObjectId="$OBJECT_ID"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Template validation passed.${NC}"
else
    echo -e "${RED}Template validation failed.${NC}"
    exit 1
fi

# Deploy the resources
echo -e "${YELLOW}Deploying resources... This may take several minutes.${NC}"
DEPLOYMENT_OUTPUT=$(az deployment group create \
    --resource-group "$RESOURCE_GROUP" \
    --template-file "$MAIN_TEMPLATE" \
    --parameters keyVaultObjectId="$OBJECT_ID" \
    --output json)

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Deployment completed successfully!${NC}"
    
    # Extract outputs
    echo -e "${YELLOW}Deployment Outputs:${NC}"
    echo "$DEPLOYMENT_OUTPUT" | jq -r '.properties.outputs | to_entries[] | "\(.key): \(.value.value)"' 2>/dev/null || echo "Could not parse outputs."
    
    # Get resource information
    echo -e "${YELLOW}Deployed Resources:${NC}"
    az resource list \
        --resource-group "$RESOURCE_GROUP" \
        --query "[].{Name:name, Type:type}" \
        --output table
    
    # Instructions for next steps
    echo -e "${GREEN}Next Steps:${NC}"
    echo "1. Update your .env file with the Cosmos DB and Storage Account credentials"
    echo "2. Activate your Python virtual environment (e.g., 'source backend/venv/bin/activate')"
    echo "3. Update backend/services/cosmos_db_client.py with your Cosmos DB credentials"
    echo "4. Run database migration scripts to populate Cosmos DB with your graph data"
    echo "5. After code deploy, run: bash scripts/post_deploy_health_check.sh"
    
else
    echo -e "${RED}Deployment failed.${NC}"
    exit 1
fi

echo -e "${GREEN}Deployment script completed!${NC}"
