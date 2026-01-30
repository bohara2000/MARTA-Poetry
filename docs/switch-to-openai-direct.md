# Migration Guide: Azure OpenAI to OpenAI API Direct

## Overview

This guide provides step-by-step instructions for switching from Azure OpenAI API to OpenAI API direct. This change will reduce monthly costs from ~$6+ to ~$21 (including Pro subscription), while maintaining the same functionality.

---

## Prerequisites

- OpenAI Pro subscription ($20/month) - provides higher rate limits
- OpenAI API key (generate at https://platform.openai.com/api-keys)
- No code changes required beyond environment variables and imports

---

## Step-by-Step Migration

### Step 1: Set Up OpenAI API Key

1. **Get your API key**:
   - Go to https://platform.openai.com/api-keys
   - Click "Create new secret key"
   - Copy the key (starts with `sk-`)
   - **Never commit this to version control**

2. **Add to `.env` file** in `/backend/.env`:
   ```
   OPENAI_API_KEY=sk-your-api-key-here
   ```

3. **Verify it's in `.gitignore`**:
   - Confirm `.env` is listed in `.gitignore` to prevent accidental commits

### Step 2: Update `config.py`

**Current state**: Loads Azure OpenAI credentials
```python
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
```

**After migration**: Will use OpenAI direct credentials
- `OPENAI_API_KEY` is already in the config file (used for fallback)
- Add a new config variable for API provider selection:
  ```python
  AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")  # "openai" or "azure"
  ```

### Step 3: Update `route_agent.py`

**Current imports**:
```python
from openai import AzureOpenAI
```

**After migration**: Use conditional imports based on provider
```python
from config import AI_PROVIDER, OPENAI_API_KEY, AZURE_OPENAI_API_KEY, ...
if AI_PROVIDER == "openai":
    from openai import OpenAI
else:
    from openai import AzureOpenAI
```

**Current client initialization**:
```python
client = AzureOpenAI(    
    api_key=subscription_key,
    api_version=api_version,
    azure_endpoint=endpoint
)
```

**After migration**: Use conditional initialization
```python
if AI_PROVIDER == "openai":
    client = OpenAI(api_key=OPENAI_API_KEY)
else:
    client = AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT
    )
```

**API call remains nearly identical**:
```python
response = client.chat.completions.create(                
    messages=messages,
    model="gpt-3.5-turbo",  # Changed from deployment variable
)
```

### Step 4: Update `app.py` (if necessary)

Check if `app.py` has any Azure-specific configuration. If it initializes any Azure clients, add similar conditional logic.

### Step 5: Install/Verify Dependencies

**Check current dependencies** in `requirements.txt`:
```
openai>=1.0.0
python-dotenv
```

The OpenAI library supports both Azure and direct API, so no new packages are needed.

### Step 6: Test the Migration

**In development**:
```bash
# Update .env with new OpenAI API key
OPENAI_API_KEY=sk-your-key-here
AI_PROVIDER=openai

# Start the server
python -m uvicorn app:app --reload --port 8000

# Test an endpoint
curl "http://localhost:8000/api/poetry?route=27339&story_influence=0.5&route_type=bus&time_of_day=late_night&location=Tokyo%20Valentino&passenger_count=medium"
```

**Expected result**: Poem generates successfully with OpenAI API instead of Azure

### Step 7: Rollback Plan

If issues occur, keep Azure credentials in `.env` and simply change:
```
AI_PROVIDER=azure
```

This allows quick fallback without code changes.

---

## Configuration Changes Summary

### `.env` File (Backend)

**Before (Azure OpenAI)**:
```
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name
AZURE_OPENAI_API_VERSION=2024-12-01-preview
```

**After (OpenAI Direct)**:
```
OPENAI_API_KEY=sk-your-openai-key
AI_PROVIDER=openai
```

**Optional (Keep for rollback)**:
```
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name
AZURE_OPENAI_API_VERSION=2024-12-01-preview
```

---

## Code Changes Required

### `config.py`
- Add `AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")`

### `route_agent.py`
- Change import from `AzureOpenAI` to conditional (OpenAI or AzureOpenAI)
- Change client initialization to conditional based on `AI_PROVIDER`
- Change model parameter from `deployment` variable to hardcoded `"gpt-3.5-turbo"` (or `"gpt-4"`)

### Other files
- Search for any other OpenAI client initialization or usage
- Apply same conditional pattern if found

---

## Model Selection

### Recommended: GPT-3.5-turbo
- **Cost**: ~$0.0005/1K input, $0.0015/1K output
- **Quality**: Good for poetry generation
- **Speed**: Fast
- **Estimated daily cost for 70 routes**: ~$0.04/day

### Alternative: GPT-4 (Higher Quality)
- **Cost**: ~$0.03/1K input, $0.06/1K output
- **Quality**: Superior poetic output
- **Speed**: Slower
- **Estimated daily cost for 70 routes**: ~$1.40/day

---

## Cost Verification

After migration, verify cost savings:

1. **Check OpenAI usage dashboard**: https://platform.openai.com/account/usage/overview
2. **Compare to Azure costs**: Previous Azure OpenAI bill

**Expected savings**: ~$180-200/month (if previously using Azure)

---

## Troubleshooting

### Error: "Invalid API key"
- Verify API key is correct (starts with `sk-`)
- Check it's in `.env` and `.env` is loaded before imports
- Ensure no trailing whitespace in `.env`

### Error: "Model not found"
- OpenAI direct uses model names like `gpt-3.5-turbo`, not deployment names
- Remove any reference to `deployment` variable

### Error: "Rate limit exceeded"
- OpenAI Pro subscription provides higher limits
- Implement exponential backoff retry logic
- Consider adding request queuing for batch operations

### Azure still being used
- Verify `AI_PROVIDER=openai` in `.env`
- Check that code changes were applied correctly
- Look for hardcoded Azure references

---

## Rollback Procedure

If issues arise:

1. **Switch back to Azure**:
   ```
   AI_PROVIDER=azure
   ```

2. **Restart application**:
   ```bash
   python -m uvicorn app:app --reload
   ```

3. **No code changes needed** if conditional logic is implemented correctly

---

## Performance Expectations

| Metric | Azure OpenAI | OpenAI Direct |
|--------|--------------|---------------|
| Latency | ~1-2 seconds | ~1-2 seconds |
| Rate Limits | Standard | Higher (Pro) |
| Monthly Cost (70 routes) | ~$6-10 | ~$21 |
| Uptime | 99.9% | 99.99% |
| Support | Enterprise | Community + Docs |

---

## Next Steps

1. Generate OpenAI API key
2. Update `.env` with new key
3. Implement conditional client initialization
4. Test in development environment
5. Verify poems generate correctly
6. Monitor costs on OpenAI dashboard
7. Clean up Azure configuration if fully migrated

---

## References

- OpenAI API Documentation: https://platform.openai.com/docs/api-reference
- OpenAI Python Library: https://github.com/openai/openai-python
- Pricing: https://openai.com/api/pricing/
- API Status: https://status.openai.com/
