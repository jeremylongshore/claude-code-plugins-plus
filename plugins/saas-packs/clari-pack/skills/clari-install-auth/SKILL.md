---
name: clari-install-auth
description: |
  Configure Clari API authentication with API key and set up export access.
  Use when connecting to the Clari API, generating API tokens,
  or configuring forecast data exports.
  Trigger with phrases like "install clari", "setup clari api",
  "clari auth", "clari api key", "configure clari".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, revenue-intelligence, forecasting, clari]
compatible-with: claude-code
---

# Clari Install & Auth

## Overview

Set up Clari API access for exporting forecast data, pipeline snapshots, and revenue intelligence to your data warehouse. Clari uses API key authentication via the `apikey` header, with the primary API at `api.clari.com/v4/`.

## Prerequisites

- Clari enterprise account with API access enabled
- Admin or RevOps role for API key generation
- Target data warehouse (Snowflake, BigQuery, or Redshift) for exports

## Instructions

### Step 1: Generate API Token

1. Log in to Clari at https://app.clari.com
2. Navigate to **User Settings** > **API Token**
3. Click **Generate New API Token**
4. Copy and store the token securely

```bash
# Store securely -- never commit
export CLARI_API_KEY="your-api-token-here"

# Verify the key works
curl -s -H "apikey: ${CLARI_API_KEY}" \
  https://api.clari.com/v4/export/forecast/list \
  | jq '.forecasts | length'
```

### Step 2: Configure Environment

```bash
# .env -- NEVER commit this file
CLARI_API_KEY=your-api-token
CLARI_BASE_URL=https://api.clari.com/v4
CLARI_ORG_ID=your-org-id

# .gitignore
.env
.env.local
```

### Step 3: Test API Connectivity

```python
import requests
import os

api_key = os.environ["CLARI_API_KEY"]
headers = {"apikey": api_key, "Content-Type": "application/json"}

# List available forecasts
response = requests.get(
    "https://api.clari.com/v4/export/forecast/list",
    headers=headers,
)
response.raise_for_status()

forecasts = response.json()["forecasts"]
for fc in forecasts:
    print(f"  {fc['forecastName']} (ID: {fc['forecastId']})")
```

### Step 4: Copilot API Setup (Optional)

Clari Copilot (conversation intelligence) has a separate API:

```bash
# Copilot uses OAuth2 -- different from the forecast API
# Register at https://api-doc.copilot.clari.com

export CLARI_COPILOT_CLIENT_ID="your-client-id"
export CLARI_COPILOT_CLIENT_SECRET="your-client-secret"

# Get access token
curl -X POST https://api.copilot.clari.com/oauth/token \
  -d "grant_type=client_credentials" \
  -d "client_id=${CLARI_COPILOT_CLIENT_ID}" \
  -d "client_secret=${CLARI_COPILOT_CLIENT_SECRET}"
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid or expired token | Regenerate at User Settings > API Token |
| `403 Forbidden` | Insufficient permissions | Contact Clari admin for API access |
| `404 Not Found` | Wrong API version or endpoint | Use `/v4/` prefix |
| Connection refused | IP allowlist | Check with IT for API access from your network |

## Resources

- [Clari Developer Portal](https://developer.clari.com)
- [Clari API Reference](https://developer.clari.com/documentation/external_spec)
- [Clari Copilot API](https://api-doc.copilot.clari.com)
- [Clari Community - API Guide](https://community.clari.com/product-q-a-6/clari-api-all-you-need-to-know-556)

## Next Steps

Proceed to `clari-hello-world` to export your first forecast.
