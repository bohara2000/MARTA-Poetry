# MARTA-Poetry Azure Deployment Guide

Complete step-by-step instructions for deploying the MARTA-Poetry application to Azure from scratch.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Setup](#local-setup)
3. [Azure Infrastructure Deployment](#azure-infrastructure-deployment)
4. [Configuration & Secrets](#configuration--secrets)
5. [Data Migration](#data-migration)
6. [Application Deployment](#application-deployment)
7. [Frontend Deployment](#frontend-deployment)
8. [Testing & Verification](#testing--verification)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools

- **Azure CLI** (v2.50+)
  ```bash
  # Install: https://learn.microsoft.com/en-us/cli/azure/install-azure-cli
  # Verify installation
  az --version
  ```

- **Python 3.9+**
  ```bash
  python3 --version
  ```

- **Git**
  ```bash
  git clone https://github.com/bohara2000/MARTA-Poetry.git
  cd MARTA-Poetry
  ```

### Azure Subscription

- Active Azure subscription with sufficient credits/budget
- Owner or Contributor role in the subscription
- Ability to create resource groups

### API Keys & Credentials

You'll need these before starting (get from their respective services):

- **Azure OpenAI** (or OpenAI API key)
  - Endpoint URL
  - API Key
  - Deployment name

- **Mapbox** (optional, for mapping features)
  - Access token

- **MARTA Transit Data** (optional)
  - GTFS API key
  - Real-time API credentials

---

## Local Setup

### 1. Clone & Install Dependencies

```bash
# Clone the repository
git clone https://github.com/bohara2000/MARTA-Poetry.git
cd MARTA-Poetry

# Set up Python virtual environment
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Configure Local Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your local values
# For local development, you can use:
# - Azure resources if already deployed
# - Cosmos DB Emulator (download from Azure)
# - Placeholder values for testing

nano .env  # or your favorite editor
```

**Key variables to configure:**

```bash
# If using live Azure resources
COSMOS_ENDPOINT=https://your-account.documents.azure.com:443/
COSMOS_KEY=your-primary-key
COSMOS_DATABASE=PoetryDatabase

# If using Cosmos DB Emulator (for local dev)
COSMOS_ENDPOINT=https://localhost:8081/
COSMOS_KEY=C2y6yDjf5/R+ob0N8A7Cgv30ESCV8QrQrF+jV7rIcgI=

# API keys
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment
```

### 3. Test Local Setup

```bash
# From backend directory (with venv activated)
python3 -c "from services.cosmos_db_client import CosmosDBClient; print('✓ Cosmos DB client imports successfully')"

# Try running the app
python3 app.py  # Should start on localhost:8000
```

---

## Azure Infrastructure Deployment

### 1. Authenticate with Azure

```bash
# Login to Azure
az login

# Set your subscription (if you have multiple)
az account set --subscription "your-subscription-id"

# Verify your account
az account show
```

### 2. Deploy Infrastructure via Bicep

```bash
# Go to project root
cd /path/to/MARTA-Poetry

# Run the deployment script
bash scripts/deploy.sh

# You'll be prompted for:
# - Azure region (default: eastus)
# - Your Azure AD object ID (auto-detected or enter manually)
# - Confirmation before creating resources
```

**What gets deployed:**

- **Resource Group**: `MartaPoetryRG`
- **Cosmos DB**: Database with 4 containers (poems, routes, personalities, graph)
- **Storage Account**: For audio files
- **Key Vault**: For secure secret storage
- **App Service**: For hosting the backend API
- **Function App**: For Azure Functions (optional)

### 3. Verify Infrastructure

```bash
# List deployed resources
az resource list --resource-group MartaPoetryRG --output table

# Check Cosmos DB
az cosmosdb show --name martadb --resource-group MartaPoetryRG

# Check Storage Account
az storage account show --name martalogicalstorage --resource-group MartaPoetryRG

# Check Key Vault
az keyvault show --name martakeyvault-* --resource-group MartaPoetryRG
```

---

## Configuration & Secrets

### 1. Add Secrets to Key Vault

Two helper scripts automate this:

#### Script 1: Add OpenAI & Third-Party Secrets

```bash
# Make sure .env has all your API keys
# Then run:
bash scripts/add_openai_secrets_to_keyvault.sh

# This stores in Key Vault:
# - Azure OpenAI credentials
# - OpenAI API key (if using direct API)
# - Mapbox token
# - MARTA API keys
```

#### Script 2: Add Configuration Variables

```bash
bash scripts/add_config_variables.sh

# This sets 23+ environment variables on:
# - App Service
# - Function App
# Including:
# - Feature flags (NWS_ENABLED, MAPBOX_ENABLED, etc.)
# - Default values (coordinates, TTL settings)
# - API URLs (Wikipedia, Wikidata, etc.)
```

### 2. Configure Managed Identities

```bash
# This enables passwordless authentication
bash scripts/configure_keyvault_references.sh

# This:
# - Enables system-assigned managed identities
# - Grants Key Vault access permissions
# - Sets up Key Vault references in app settings
```

### 3. Verify Configuration

```bash
# Check Web App settings
az webapp config appsettings list \
  --name marta-poetry-app \
  --resource-group MartaPoetryRG

# Check Function App settings
az functionapp config appsettings list \
  --name marta-poetry-functions \
  --resource-group MartaPoetryRG

# Verify Key Vault secrets
az keyvault secret list \
  --vault-name martakeyvault-* \
  --resource-group MartaPoetryRG
```

---

## Data Migration

### 1. Migrate JSON Data to Cosmos DB

```bash
# Make sure your .env has valid COSMOS_ENDPOINT and COSMOS_KEY
# The script will read from:
# - backend/data/poetry_graph.json
# - backend/data/route_personalities.json

cd /path/to/MARTA-Poetry
python3 scripts/migrate_to_cosmos.py

# Expected output:
# ✓ Connected to Cosmos DB
# ✓ Migrated 586 nodes to 'graph' container
# ✓ Migrated routes to 'routes' container
# ✓ Migrated personalities to 'personalities' container
```

### 2. Verify Migration

```bash
# Use Cosmos DB Data Explorer in Azure Portal:
# Portal → Cosmos DB → Data Explorer → select container → "Items"
# 
# Or use Azure CLI:
az cosmosdb sql query \
  --name martadb \
  --resource-group MartaPoetryRG \
  --database-name PoetryDatabase \
  --container-name graph \
  --query "SELECT COUNT(1) as count FROM c"
```

### 3. Upload Audio Files (Optional)

If you have audio files to store:

```bash
# Using Azure CLI
STORAGE_ACCOUNT=$(az storage account list --resource-group MartaPoetryRG --query "[0].name" -o tsv)

# Get storage key
STORAGE_KEY=$(az storage account keys list --account-name $STORAGE_ACCOUNT --resource-group MartaPoetryRG --query "[0].value" -o tsv)

# Upload audio files
az storage blob upload-batch \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY \
  --destination audio \
  --source backend/audio/
```

---

## Application Deployment

### Option A: One-Command Deploy & Verify (Recommended)

**Fastest option:** Zips code, deploys to App Service, and validates health in one command.

```bash
# From project root
bash scripts/deploy_and_verify.sh
```

This script:
- ✅ Creates deployment package (`backend/app.zip`)
- ✅ Uploads to App Service
- ✅ Waits for processing
- ✅ Validates endpoints respond (up to 3 minutes)
- ✅ Shows access URLs on success

**With custom resource names:**
```bash
APP_NAME=my-app RESOURCE_GROUP=my-rg bash scripts/deploy_and_verify.sh
```

### Option B: Manual ZIP Deploy

If you prefer step-by-step control:

```bash
# Create deployment package
cd backend
rm -rf __pycache__ poetry/__pycache__
zip -r app.zip . -x "venv/*" ".env" "__pycache__/*"

# Deploy via Azure CLI
az webapp deployment source config-zip \
  --name marta-poetry-app \
  --resource-group MartaPoetryRG \
  --src app.zip

# Verify health (in root directory)
bash scripts/post_deploy_health_check.sh
```

### Option C: Deploy via GitHub Actions (CI/CD)

See `.github/workflows/deploy.yml` for automated deployment on push to main.

### Option D: Deploy from VS Code

```bash
# Install Azure App Service extension
# Command Palette → "Deploy to App Service"
# Select: marta-poetry-app
```

---

## Frontend Deployment

The frontend is deployed separately to **Azure Static Web Apps** (free tier available).

### Prerequisites for Frontend

- Node.js 16+ installed locally
- Frontend directory: `frontend/`
- Backend already deployed (needed for API endpoint)

### Option A: Automatic Deployment via GitHub Actions (Recommended)

Static Web Apps integrates with GitHub for automatic deployments.

**One-time Setup:**

1. **Create Static Web App resource** (if not already created):
   ```bash
   az staticwebapp create \
     --name marta-poetry-frontend \
     --resource-group MartaPoetryRG \
     --location eastus2 \
     --sku free
   ```

2. **Get the deployment token:**
   ```bash
   DEPLOYMENT_TOKEN=$(az staticwebapp secrets list \
     --name marta-poetry-frontend \
     --resource-group MartaPoetryRG \
     --query "properties.apiKey" -o tsv)
   
   echo "Deployment Token:"
   echo $DEPLOYMENT_TOKEN
   ```

3. **Add GitHub secret** (one-time per repository):
   - Go to: https://github.com/bohara2000/MARTA-Poetry/settings/secrets/actions
   - Click "New repository secret"
   - Fill in:
     - **Name:** `AZURE_STATIC_WEB_APPS_API_TOKEN`
     - **Value:** (paste the token from step 2)
   - Click "Add secret"

4. **Push to main** to trigger first deployment:
   ```bash
   git push origin main
   ```

**From now on:** Every push to `main` automatically:
- Installs dependencies
- Builds the React app
- Deploys to Static Web Apps
- Configures API endpoint

Monitor the deployment in the **GitHub Actions** tab of your repository.

**Note for team members:** The deployment token is stored as a GitHub secret, not in the repo. Only maintainers with repo access need to set it up once.

### Option B: Build and Deploy Locally

If you prefer to control deployment manually:

```bash
# Build the frontend
cd frontend
npm install
npm run build

# This creates optimized files in frontend/dist/

# Deploy using Azure CLI
az staticwebapp upload \
  --name marta-poetry-frontend \
  --source-path ./dist
```

### Option C: Use Deploy Script

```bash
# Builds frontend and shows deployment options
bash scripts/deploy_frontend.sh
```

### Verify Frontend Deployment

```bash
# Get the Static Web App URL
az staticwebapp show \
  --name marta-poetry-frontend \
  --resource-group MartaPoetryRG \
  --query "properties.defaultHostname" -o tsv

# Visit the URL in your browser
# The app will automatically connect to the backend API
```

### Configure API Endpoint

The frontend automatically connects to the backend:

- **Development**: Uses `http://localhost:8000` (Vite dev server proxy)
- **Production**: Uses the backend App Service URL

Environment variables in `frontend/.env.local`:

```bash
# For local development
VITE_API_URL=http://localhost:8000

# For production (set automatically by Static Web Apps)
# VITE_API_URL=https://marta-poetry-app.azurewebsites.net
```

---

## Testing & Verification

### 1. Automatic Health Validation

After deployment, the app runs an automated health check:

```bash
# This runs automatically with Option A deployment
# Or run manually anytime:
bash scripts/post_deploy_health_check.sh
```

Validates:
- ✅ `/openapi.json` endpoint returns 200 OK
- ✅ `/` root endpoint returns 200 OK
- ✅ App responded within 3 minutes (18 retries × 10s)

On failure, displays diagnostics: app state, startup command, recent logs.

### 2. Test App Service

```bash
# Get the app URL
APP_URL=$(az webapp show --name marta-poetry-app --resource-group MartaPoetryRG --query "hostNames[0]" -o tsv)

# Test the health endpoint
curl https://$APP_URL/

# Test OpenAPI docs
curl https://$APP_URL/docs

# Expected response: 200 OK
```

### 3. Test Cosmos DB Connection

```bash
# SSH into App Service and test
az webapp remote-connection create \
  --name marta-poetry-app \
  --resource-group MartaPoetryRG

# Or check logs
az webapp log tail --name marta-poetry-app --resource-group MartaPoetryRG
```

### 4. Test Key Vault Access

```bash
# Get the managed identity object ID
WEB_APP_IDENTITY=$(az webapp identity show \
  --name marta-poetry-app \
  --resource-group MartaPoetryRG \
  --query principalId -o tsv)

# Verify Key Vault permissions
az keyvault get-policy \
  --vault-name martakeyvault-* \
  --object-id $WEB_APP_IDENTITY
```

### 5. Test API Endpoints

```bash
# After deployment, test key endpoints:

# Generate a poem
curl -X POST https://$APP_URL/api/poem/generate \
  -H "Content-Type: application/json" \
  -d '{"route": "MARTA_5", "story_influence": 0.7}'

# Get poem by ID
curl https://$APP_URL/api/poem/{poem_id}

# List all poems
curl https://$APP_URL/api/poems
```

---

## Troubleshooting

### Issue: "Outputs should not contain secrets" Warning

**Solution**: Already fixed in Bicep templates. Key Vault retrieves secrets internally, not in outputs.

### Issue: Cosmos DB Connection Failed

```bash
# Check if credentials are correct
az cosmosdb keys list --name martadb --resource-group MartaPoetryRG

# Verify connection string format
COSMOS_ENDPOINT=https://martadb.documents.azure.com:443/
COSMOS_KEY=<primary-key>

# Test connection locally
python3 -c "
from azure.cosmos import CosmosClient
client = CosmosClient('COSMOS_ENDPOINT', 'COSMOS_KEY')
print('✓ Connected')
"
```

### Issue: Key Vault Access Denied

```bash
# Ensure managed identity has permissions
az keyvault set-policy \
  --name martakeyvault-* \
  --object-id <managed-identity-id> \
  --secret-permissions get list

# Restart the app
az webapp restart --name marta-poetry-app --resource-group MartaPoetryRG
```

### Issue: Missing Environment Variables

```bash
# Re-run configuration scripts
bash scripts/configure_keyvault_references.sh
bash scripts/add_openai_secrets_to_keyvault.sh
bash scripts/add_config_variables.sh

# Restart the app
az webapp restart --name marta-poetry-app --resource-group MartaPoetryRG
```

### Issue: Data Not Appearing in Cosmos DB

```bash
# Check if migration script ran successfully
python3 scripts/migrate_to_cosmos.py

# View Cosmos DB logs
az cosmosdb logs tail --name martadb --resource-group MartaPoetryRG

# Check container exists
az cosmosdb sql container list \
  --account-name martadb \
  --database-name PoetryDatabase \
  --resource-group MartaPoetryRG
```

---

## Cost Optimization

### Production Recommendations

1. **Cosmos DB**: Adjust RU/s based on actual usage (currently 400 RU/s)
2. **App Service**: Use B2 or B3 for production, B1 for testing
3. **Storage Account**: Use Cool tier for audio files (less frequent access)
4. **Key Vault**: Standard tier is usually sufficient

### Cost Monitoring

```bash
# Set up billing alerts
az cost management budget create \
  --budget-name "MARTA-Poetry-Budget" \
  --amount 50 \
  --time-period "Monthly"

# View current costs
az costmanagement query --timeframe "MonthToDate" --output table
```

---

## Next Steps

1. ✅ **Complete**: Infrastructure deployed
2. ✅ **Complete**: Secrets configured in Key Vault
3. ✅ **Complete**: Data migrated to Cosmos DB
4. **TODO**: Deploy application code
5. **TODO**: Set up CI/CD pipeline
6. **TODO**: Configure custom domain & SSL
7. **TODO**: Set up monitoring & alerts
8. **TODO**: Implement API authentication (if needed)

---

## Support & Resources

- **Azure Documentation**: https://learn.microsoft.com/en-us/azure/
- **Cosmos DB**: https://learn.microsoft.com/en-us/azure/cosmos-db/
- **Bicep**: https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/
- **MARTA API**: https://www.itsmarta.com/developers/

---

## Quick Reference: All Scripts

| Script | Purpose | When to Run |
|--------|---------|------------|
| `scripts/deploy.sh` | Deploy infrastructure (Bicep → Azure) | Initial setup |
| `scripts/migrate_to_cosmos.py` | Migrate JSON data to Cosmos DB | After infrastructure ready |
| `scripts/add_openai_secrets_to_keyvault.sh` | Store API keys in Key Vault | After configuration |
| `scripts/add_config_variables.sh` | Set app settings on App Service/Functions | After secrets in Key Vault |
| `scripts/configure_keyvault_references.sh` | Enable managed identities & Key Vault references | After infrastructure ready |

---

**Last Updated**: March 1, 2026
**Project**: MARTA-Poetry
**Repository**: https://github.com/bohara2000/MARTA-Poetry
