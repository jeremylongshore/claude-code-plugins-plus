---
name: procore-install-auth
description: |
  Procore install auth — construction management platform integration.
  Use when working with Procore API for project management, RFIs, or submittals.
  Trigger with phrases like "procore install auth", "procore-install-auth".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Bash(curl:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, procore, construction, project-management]
compatible-with: claude-code, codex, openclaw
---

# Procore Install Auth

## Overview
Set up Procore API authentication using OAuth2 client credentials flow. Procore uses OAuth2 with separate endpoints for production and sandbox.

## Prerequisites
- Procore Developer account at developers.procore.com
- App credentials (client_id, client_secret)
- A Procore company to authorize against

## Instructions

### Step 1: Register Application
```text
1. Go to developers.procore.com > My Apps > Create App
2. Set redirect URI: http://localhost:3000/callback
3. Copy client_id and client_secret
```

### Step 2: Configure Environment
```bash
# .env
PROCORE_CLIENT_ID=your_client_id
PROCORE_CLIENT_SECRET=your_client_secret
PROCORE_BASE_URL=https://api.procore.com
# For sandbox: https://sandbox.procore.com
```

### Step 3: Client Credentials Flow
```python
import os, requests

token_resp = requests.post("https://login.procore.com/oauth/token", data={
    "grant_type": "client_credentials",
    "client_id": os.environ["PROCORE_CLIENT_ID"],
    "client_secret": os.environ["PROCORE_CLIENT_SECRET"],
})
token_resp.raise_for_status()
access_token = token_resp.json()["access_token"]

# Verify — list companies
headers = {"Authorization": f"Bearer {access_token}"}
companies = requests.get("https://api.procore.com/rest/v1.0/companies", headers=headers)
companies.raise_for_status()
for co in companies.json():
    print(f"Company: {co['name']} (ID: {co['id']})")
```

## Output
- OAuth2 tokens obtained via client credentials
- API connectivity verified with company listing

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `invalid_client` | Wrong credentials | Verify in developer portal |
| `401 Unauthorized` | Expired token | Re-authenticate |
| Sandbox vs production | Wrong base URL | Use login-sandbox-monthly.procore.com for sandbox |

## Resources
- [Procore OAuth Endpoints](https://developers.procore.com/documentation/oauth-endpoints)
- [Client Credentials](https://developers.procore.com/documentation/oauth-client-credentials)

## Next Steps
First API call: `procore-hello-world`
