---
name: ramp-install-auth
description: |
  Ramp install auth — corporate card and expense management API integration.
  Use when working with Ramp for card management, expenses, or accounting sync.
  Trigger with phrases like "ramp install auth", "ramp-install-auth", "corporate card API".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ramp, fintech, expenses, corporate-cards]
compatible-with: claude-code, codex, openclaw
---

# Ramp Install Auth

## Overview
Set up Ramp API authentication using OAuth2 client credentials flow with sandbox and production environments.

## Prerequisites
- Ramp account with API access
- Client ID and Client Secret from Ramp Dashboard

## Instructions

### Step 1: Get API Credentials
```text
1. Go to Ramp Dashboard > Settings > Developer
2. Create new API application
3. Copy Client ID and Client Secret
4. Note: Sandbox URL is sandbox-api.ramp.com, Production is api.ramp.com
```

### Step 2: Configure Environment
```bash
# .env
RAMP_CLIENT_ID=your_client_id
RAMP_CLIENT_SECRET=your_client_secret
RAMP_BASE_URL=https://sandbox-api.ramp.com/v1  # Switch to api.ramp.com for prod
```

### Step 3: Obtain Access Token
```python
import os, requests

token_resp = requests.post("https://sandbox-api.ramp.com/v1/token", data={
    "grant_type": "client_credentials",
    "client_id": os.environ["RAMP_CLIENT_ID"],
    "client_secret": os.environ["RAMP_CLIENT_SECRET"],
})
token_resp.raise_for_status()
access_token = token_resp.json()["access_token"]
print(f"Token obtained (expires in {token_resp.json()['expires_in']}s)")
```

### Step 4: Verify Connection
```python
headers = {"Authorization": f"Bearer {access_token}"}
resp = requests.get(f"{os.environ['RAMP_BASE_URL']}/cards", headers=headers)
resp.raise_for_status()
cards = resp.json()["data"]
print(f"Connected! Found {len(cards)} cards")
```

## Output
- OAuth2 access token obtained
- API connectivity verified with card listing

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `invalid_client` | Wrong credentials | Verify client_id/secret in Dashboard |
| `401 Unauthorized` | Token expired | Re-authenticate (tokens expire in 1 hour) |
| Wrong environment | Sandbox vs prod URL | Check RAMP_BASE_URL |

## Resources
- [Ramp Authorization](https://docs.ramp.com/developer-api/v1/authorization)
- [Getting Started](https://docs.ramp.com/developer-api/v1/guides/getting-started)

## Next Steps
First API call: `ramp-hello-world`
