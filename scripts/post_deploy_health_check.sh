#!/bin/bash

# Post-deploy health check for App Service
# Fails fast if deployed app is not serving FastAPI endpoints.

set -euo pipefail

RESOURCE_GROUP="${RESOURCE_GROUP:-MartaPoetryRG}"
WEB_APP_NAME="${WEB_APP_NAME:-marta-poetry-app}"
MAX_RETRIES="${MAX_RETRIES:-18}"   # 18 * 10s = 3 minutes
SLEEP_SECONDS="${SLEEP_SECONDS:-10}"

echo "Running post-deploy health checks for ${WEB_APP_NAME}..."

HOSTNAME=$(az webapp show \
  --name "$WEB_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query defaultHostName -o tsv)

if [[ -z "$HOSTNAME" ]]; then
  echo "ERROR: Could not resolve app hostname."
  exit 1
fi

BASE_URL="https://${HOSTNAME}"
OPENAPI_URL="${BASE_URL}/openapi.json"
ROOT_URL="${BASE_URL}/"

echo "App URL: ${BASE_URL}"

for ((i=1; i<=MAX_RETRIES; i++)); do
  OPENAPI_STATUS=$(curl -sS -o /tmp/marta_openapi.json -w "%{http_code}" --max-time 20 "$OPENAPI_URL" || true)
  ROOT_STATUS=$(curl -sS -o /tmp/marta_root.txt -w "%{http_code}" --max-time 20 "$ROOT_URL" || true)

  if [[ "$OPENAPI_STATUS" == "200" ]]; then
    if grep -q '"openapi"' /tmp/marta_openapi.json; then
      echo "✓ Health check passed on attempt ${i}/${MAX_RETRIES}."
      echo "  openapi.json: HTTP ${OPENAPI_STATUS}"
      echo "  root: HTTP ${ROOT_STATUS}"
      exit 0
    fi
  fi

  echo "Attempt ${i}/${MAX_RETRIES} failed: /openapi.json HTTP ${OPENAPI_STATUS}, / HTTP ${ROOT_STATUS}"
  sleep "$SLEEP_SECONDS"
done

echo "✗ Health check failed after ${MAX_RETRIES} attempts."
echo "Recent diagnostics:"

echo "- App state:"
az webapp show --name "$WEB_APP_NAME" --resource-group "$RESOURCE_GROUP" --query "{state:state,kind:kind,linuxFxVersion:siteConfig.linuxFxVersion,startup:siteConfig.appCommandLine}" -o json || true

echo "- Last 30s log tail:"
timeout 30s az webapp log tail --name "$WEB_APP_NAME" --resource-group "$RESOURCE_GROUP" || true

exit 1
