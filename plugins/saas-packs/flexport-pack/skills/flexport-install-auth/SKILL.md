---
name: flexport-install-auth
description: |
  Install and configure Flexport API authentication with API keys or OAuth credentials.
  Use when setting up a new Flexport logistics integration, configuring bearer tokens,
  or initializing the Flexport REST API client for shipment and supply chain operations.
  Trigger: "install flexport", "setup flexport", "flexport auth", "flexport API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, logistics, flexport]
compatible-with: claude-code
---

# Flexport Install & Auth

## Overview

Configure Flexport API authentication for logistics and supply chain integration. Flexport offers two auth methods: **API Keys** (simple bearer tokens that never expire) and **API Credentials** (client ID/secret pairs that issue JWTs valid for 24 hours). The v2 REST API base URL is `https://api.flexport.com` and speaks JSON.

## Prerequisites

- Flexport account at [flexport.com](https://www.flexport.com)
- API key or credentials from Flexport Portal > Settings > Developer > API Credentials
- Node.js 18+ or Python 3.9+

## Instructions

### Step 1: Obtain API Credentials

Navigate to Flexport Portal > Settings > Developer. Two options:

| Auth Method | Format | Lifetime | Use Case |
|-------------|--------|----------|----------|
| API Key | Bearer token string | Permanent | Simple integrations, scripts |
| API Credentials | Client ID + Secret | JWT, 24h | Production apps, rotating tokens |

### Step 2: Configure Environment Variables

```bash
# .env (NEVER commit — add to .gitignore)
FLEXPORT_API_KEY=your_api_key_here

# OR for OAuth credentials flow:
FLEXPORT_CLIENT_ID=your_client_id
FLEXPORT_CLIENT_SECRET=your_client_secret
FLEXPORT_API_URL=https://api.flexport.com
```

### Step 3: Authenticate with API Key

```typescript
// src/flexport/client.ts
const FLEXPORT_BASE = 'https://api.flexport.com';

async function flexportRequest(path: string, options: RequestInit = {}) {
  const res = await fetch(`${FLEXPORT_BASE}${path}`, {
    ...options,
    headers: {
      'Authorization': `Bearer ${process.env.FLEXPORT_API_KEY}`,
      'Content-Type': 'application/json',
      'Flexport-Version': '2',
      ...options.headers,
    },
  });
  if (!res.ok) throw new Error(`Flexport ${res.status}: ${await res.text()}`);
  return res.json();
}
```

### Step 4: OAuth Credentials Flow (Production)

```typescript
let tokenCache: { token: string; expiresAt: number } | null = null;

async function getAccessToken(): Promise<string> {
  if (tokenCache && Date.now() < tokenCache.expiresAt) return tokenCache.token;

  const res = await fetch('https://api.flexport.com/oauth/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      client_id: process.env.FLEXPORT_CLIENT_ID,
      client_secret: process.env.FLEXPORT_CLIENT_SECRET,
      grant_type: 'client_credentials',
    }),
  });
  const { access_token, expires_in } = await res.json();
  tokenCache = { token: access_token, expiresAt: Date.now() + (expires_in - 60) * 1000 };
  return access_token;
}
```

### Step 5: Verify Connection

```typescript
async function verifyFlexport() {
  const data = await flexportRequest('/shipments?per=1&page=1');
  console.log(`Connected. Shipments found: ${data.data?.records?.length ?? 0}`);
}
await verifyFlexport();
```

## Error Handling

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| `Unauthorized` | 401 | Invalid or expired key | Regenerate in Portal > Developer |
| `Forbidden` | 403 | Insufficient scope | Check key permissions |
| `Token expired` | 401 | JWT past 24h | Re-fetch via client credentials |
| `Rate limit exceeded` | 429 | Too many requests | Exponential backoff |

## Examples

### Python Client

```python
import os, requests

class FlexportClient:
    BASE = 'https://api.flexport.com'

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {os.environ["FLEXPORT_API_KEY"]}',
            'Content-Type': 'application/json',
            'Flexport-Version': '2',
        })

    def get(self, path, params=None):
        r = self.session.get(f'{self.BASE}{path}', params=params)
        r.raise_for_status()
        return r.json()
```

### cURL Verification

```bash
curl -s -H "Authorization: Bearer $FLEXPORT_API_KEY" \
     -H "Flexport-Version: 2" \
     https://api.flexport.com/shipments?per=1 | jq '.data.records | length'
```

## Resources

- [Flexport Developer Portal](https://developers.flexport.com/)
- [API Credentials Tutorial](https://developers.flexport.com/tutorials/using-api-credentials/)
- [Flexport API Reference](https://apidocs.flexport.com/)
- [Logistics API Docs](https://docs.logistics-api.flexport.com/)

## Next Steps

After successful auth, proceed to `flexport-hello-world` for your first shipment query.
