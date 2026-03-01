#!/bin/bash

# Add remaining configuration variables to App Service and Function App
# This script configures feature flags, URLs, and other app-level settings

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

echo -e "${YELLOW}Adding Configuration Variables to App Services${NC}"
echo "================================================="

# ==================== LOAD .ENV FILE ====================
echo -e "${YELLOW}Loading configuration from .env...${NC}"

if [ ! -f "$BACKEND_DIR/.env" ]; then
    echo -e "${RED}Error: .env file not found at $BACKEND_DIR/.env${NC}"
    exit 1
fi

# Extract configuration values from .env
POETRY_MODE=$(grep "^POETRY_MODE=" "$BACKEND_DIR/.env" | cut -d '=' -f 2-)
DEFAULT_STORY_INFLUENCE=$(grep "^DEFAULT_STORY_INFLUENCE=" "$BACKEND_DIR/.env" | cut -d '=' -f 2-)
DEFAULT_LATITUDE=$(grep "^DEFAULT_LATITUDE=" "$BACKEND_DIR/.env" | cut -d '=' -f 2-)
DEFAULT_LONGITUDE=$(grep "^DEFAULT_LONGITUDE=" "$BACKEND_DIR/.env" | cut -d '=' -f 2-)
NWS_ENABLED=$(grep "^NWS_ENABLED=" "$BACKEND_DIR/.env" | cut -d '=' -f 2-)
NWS_WEATHER_TTL_SECONDS=$(grep "^NWS_WEATHER_TTL_SECONDS=" "$BACKEND_DIR/.env" | cut -d '=' -f 2-)
GTFS_RT_ENABLED=$(grep "^GTFS_RT_ENABLED=" "$BACKEND_DIR/.env" | cut -d '=' -f 2-)
GTFS_RT_VEHICLE_POSITIONS_URL=$(grep "^GTFS_RT_VEHICLE_POSITIONS_URL=" "$BACKEND_DIR/.env" | cut -d '=' -f 2-)
GTFS_RT_API_KEY=$(grep "^GTFS_RT_API_KEY=" "$BACKEND_DIR/.env" | cut -d '=' -f 2-)
GTFS_API_KEY=$(grep "^GTFS_API_KEY=" "$BACKEND_DIR/.env" | cut -d '=' -f 2-)
RAIL_RT_ENABLED=$(grep "^RAIL_RT_ENABLED=" "$BACKEND_DIR/.env" | cut -d '=' -f 2-)
RAIL_RT_URL=$(grep "^RAIL_RT_URL=" "$BACKEND_DIR/.env" | cut -d '=' -f 2-)
MAPBOX_ENABLED=$(grep "^MAPBOX_ENABLED=" "$BACKEND_DIR/.env" | cut -d '=' -f 2-)
MAPBOX_GEOCODE_BASE_URL=$(grep "^MAPBOX_GEOCODE_BASE_URL=" "$BACKEND_DIR/.env" | cut -d '=' -f 2-)
MAPBOX_GEOCODE_LIMIT=$(grep "^MAPBOX_GEOCODE_LIMIT=" "$BACKEND_DIR/.env" | cut -d '=' -f 2-)
MAPBOX_TRAFFIC_ENABLED=$(grep "^MAPBOX_TRAFFIC_ENABLED=" "$BACKEND_DIR/.env" | cut -d '=' -f 2-)
MAPBOX_DIRECTIONS_BASE_URL=$(grep "^MAPBOX_DIRECTIONS_BASE_URL=" "$BACKEND_DIR/.env" | cut -d '=' -f 2-)
MAPBOX_TRAFFIC_TTL_SECONDS=$(grep "^MAPBOX_TRAFFIC_TTL_SECONDS=" "$BACKEND_DIR/.env" | cut -d '=' -f 2-)
SOLAR_EVENTS_ENABLED=$(grep "^SOLAR_EVENTS_ENABLED=" "$BACKEND_DIR/.env" | cut -d '=' -f 2-)
SOLAR_EVENTS_TTL_SECONDS=$(grep "^SOLAR_EVENTS_TTL_SECONDS=" "$BACKEND_DIR/.env" | cut -d '=' -f 2-)
HISTORY_CONTEXT_ENABLED=$(grep "^HISTORY_CONTEXT_ENABLED=" "$BACKEND_DIR/.env" | cut -d '=' -f 2-)
HISTORY_CONTEXT_MAX_ITEMS=$(grep "^HISTORY_CONTEXT_MAX_ITEMS=" "$BACKEND_DIR/.env" | cut -d '=' -f 2-)
HISTORY_CONTEXT_LOCATION_HINT=$(grep "^HISTORY_CONTEXT_LOCATION_HINT=" "$BACKEND_DIR/.env" | cut -d '=' -f 2-)
WIKIPEDIA_SUMMARY_BASE_URL=$(grep "^WIKIPEDIA_SUMMARY_BASE_URL=" "$BACKEND_DIR/.env" | cut -d '=' -f 2-)
WIKIDATA_SEARCH_URL=$(grep "^WIKIDATA_SEARCH_URL=" "$BACKEND_DIR/.env" | cut -d '=' -f 2-)

echo -e "${GREEN}✓ Configuration loaded${NC}"

# ==================== GET KEY VAULT ====================
echo -e "${YELLOW}Finding Key Vault for secrets...${NC}"
KEY_VAULT_NAME=$(az keyvault list --resource-group "$RESOURCE_GROUP" --query "[0].name" -o tsv)

if [ -z "$KEY_VAULT_NAME" ]; then
    echo -e "${RED}No Key Vault found in resource group.${NC}"
    exit 1
fi

echo -e "${GREEN}Key Vault: ${KEY_VAULT_NAME}${NC}"

KEY_VAULT_URI=$(az keyvault show --name "$KEY_VAULT_NAME" --resource-group "$RESOURCE_GROUP" --query "properties.vaultUri" -o tsv)

# ==================== ADD SECRETS TO KEY VAULT ====================
echo ""
echo -e "${YELLOW}Storing API keys in Key Vault...${NC}"

# Add API keys to Key Vault (if they have values)
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

# ==================== UPDATE WEB APP SETTINGS ====================
echo ""
echo -e "${YELLOW}Configuring Web App settings...${NC}"

WEB_APP_SETTINGS=(
    "POETRY_MODE=$POETRY_MODE"
    "DEFAULT_STORY_INFLUENCE=$DEFAULT_STORY_INFLUENCE"
    "DEFAULT_LATITUDE=$DEFAULT_LATITUDE"
    "DEFAULT_LONGITUDE=$DEFAULT_LONGITUDE"
    "NWS_ENABLED=$NWS_ENABLED"
    "NWS_WEATHER_TTL_SECONDS=$NWS_WEATHER_TTL_SECONDS"
    "GTFS_RT_ENABLED=$GTFS_RT_ENABLED"
    "GTFS_RT_VEHICLE_POSITIONS_URL=$GTFS_RT_VEHICLE_POSITIONS_URL"
    "RAIL_RT_ENABLED=$RAIL_RT_ENABLED"
    "RAIL_RT_URL=$RAIL_RT_URL"
    "MAPBOX_ENABLED=$MAPBOX_ENABLED"
    "MAPBOX_GEOCODE_BASE_URL=$MAPBOX_GEOCODE_BASE_URL"
    "MAPBOX_GEOCODE_LIMIT=$MAPBOX_GEOCODE_LIMIT"
    "MAPBOX_TRAFFIC_ENABLED=$MAPBOX_TRAFFIC_ENABLED"
    "MAPBOX_DIRECTIONS_BASE_URL=$MAPBOX_DIRECTIONS_BASE_URL"
    "MAPBOX_TRAFFIC_TTL_SECONDS=$MAPBOX_TRAFFIC_TTL_SECONDS"
    "SOLAR_EVENTS_ENABLED=$SOLAR_EVENTS_ENABLED"
    "SOLAR_EVENTS_TTL_SECONDS=$SOLAR_EVENTS_TTL_SECONDS"
    "HISTORY_CONTEXT_ENABLED=$HISTORY_CONTEXT_ENABLED"
    "HISTORY_CONTEXT_MAX_ITEMS=$HISTORY_CONTEXT_MAX_ITEMS"
    "HISTORY_CONTEXT_LOCATION_HINT=$HISTORY_CONTEXT_LOCATION_HINT"
    "WIKIPEDIA_SUMMARY_BASE_URL=$WIKIPEDIA_SUMMARY_BASE_URL"
    "WIKIDATA_SEARCH_URL=$WIKIDATA_SEARCH_URL"
)

# Add API key references if they exist
if [ -n "$GTFS_API_KEY" ]; then
    WEB_APP_SETTINGS+=("GTFS_API_KEY=@Microsoft.KeyVault(SecretUri=${KEY_VAULT_URI}secrets/GtfsApiKey/)")
fi

if [ -n "$GTFS_RT_API_KEY" ]; then
    WEB_APP_SETTINGS+=("GTFS_RT_API_KEY=@Microsoft.KeyVault(SecretUri=${KEY_VAULT_URI}secrets/GtfsRtApiKey/)")
fi

az webapp config appsettings set \
    --name "$WEB_APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --settings "${WEB_APP_SETTINGS[@]}" > /dev/null

echo -e "${GREEN}✓ Web App configured with ${#WEB_APP_SETTINGS[@]} settings${NC}"

# ==================== UPDATE FUNCTION APP SETTINGS ====================
echo -e "${YELLOW}Configuring Function App settings...${NC}"

FUNCTION_APP_SETTINGS=(
    "POETRY_MODE=$POETRY_MODE"
    "DEFAULT_STORY_INFLUENCE=$DEFAULT_STORY_INFLUENCE"
    "DEFAULT_LATITUDE=$DEFAULT_LATITUDE"
    "DEFAULT_LONGITUDE=$DEFAULT_LONGITUDE"
    "NWS_ENABLED=$NWS_ENABLED"
    "NWS_WEATHER_TTL_SECONDS=$NWS_WEATHER_TTL_SECONDS"
    "GTFS_RT_ENABLED=$GTFS_RT_ENABLED"
    "GTFS_RT_VEHICLE_POSITIONS_URL=$GTFS_RT_VEHICLE_POSITIONS_URL"
    "RAIL_RT_ENABLED=$RAIL_RT_ENABLED"
    "RAIL_RT_URL=$RAIL_RT_URL"
    "MAPBOX_ENABLED=$MAPBOX_ENABLED"
    "MAPBOX_GEOCODE_BASE_URL=$MAPBOX_GEOCODE_BASE_URL"
    "MAPBOX_GEOCODE_LIMIT=$MAPBOX_GEOCODE_LIMIT"
    "MAPBOX_TRAFFIC_ENABLED=$MAPBOX_TRAFFIC_ENABLED"
    "MAPBOX_DIRECTIONS_BASE_URL=$MAPBOX_DIRECTIONS_BASE_URL"
    "MAPBOX_TRAFFIC_TTL_SECONDS=$MAPBOX_TRAFFIC_TTL_SECONDS"
    "SOLAR_EVENTS_ENABLED=$SOLAR_EVENTS_ENABLED"
    "SOLAR_EVENTS_TTL_SECONDS=$SOLAR_EVENTS_TTL_SECONDS"
    "HISTORY_CONTEXT_ENABLED=$HISTORY_CONTEXT_ENABLED"
    "HISTORY_CONTEXT_MAX_ITEMS=$HISTORY_CONTEXT_MAX_ITEMS"
    "HISTORY_CONTEXT_LOCATION_HINT=$HISTORY_CONTEXT_LOCATION_HINT"
    "WIKIPEDIA_SUMMARY_BASE_URL=$WIKIPEDIA_SUMMARY_BASE_URL"
    "WIKIDATA_SEARCH_URL=$WIKIDATA_SEARCH_URL"
)

# Add API key references if they exist
if [ -n "$GTFS_API_KEY" ]; then
    FUNCTION_APP_SETTINGS+=("GTFS_API_KEY=@Microsoft.KeyVault(SecretUri=${KEY_VAULT_URI}secrets/GtfsApiKey/)")
fi

if [ -n "$GTFS_RT_API_KEY" ]; then
    FUNCTION_APP_SETTINGS+=("GTFS_RT_API_KEY=@Microsoft.KeyVault(SecretUri=${KEY_VAULT_URI}secrets/GtfsRtApiKey/)")
fi

az functionapp config appsettings set \
    --name "$FUNCTION_APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --settings "${FUNCTION_APP_SETTINGS[@]}" > /dev/null

echo -e "${GREEN}✓ Function App configured with ${#FUNCTION_APP_SETTINGS[@]} settings${NC}"

# ==================== SUMMARY ====================
echo ""
echo -e "${GREEN}✓ Configuration variables successfully added!${NC}"
echo ""
echo -e "${YELLOW}Summary:${NC}"
echo "- Web App ($WEB_APP_NAME): ${#WEB_APP_SETTINGS[@]} settings"
echo "- Function App ($FUNCTION_APP_NAME): ${#FUNCTION_APP_SETTINGS[@]} settings"
echo ""
echo -e "${YELLOW}Configuration categories:${NC}"
echo "- Poetry Mode & Defaults"
echo "- NWS (National Weather Service)"
echo "- GTFS Real-Time (Bus & Rail)"
echo "- Mapbox (Geocoding & Directions)"
echo "- Solar Events, History Context"
echo "- Wikipedia & Wikidata APIs"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Review settings in Azure Portal → App Service → Configuration"
echo "2. Restart the apps for changes to take effect:"
echo "   az webapp restart --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP"
echo "   az functionapp restart --name $FUNCTION_APP_NAME --resource-group $RESOURCE_GROUP"
echo ""
echo -e "${GREEN}✓ Done!${NC}"
