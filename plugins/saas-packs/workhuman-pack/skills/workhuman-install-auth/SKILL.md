---
name: workhuman-install-auth
description: |
  Workhuman install auth for employee recognition and rewards API.
  Use when integrating Workhuman Social Recognition,
  or building recognition workflows with HRIS systems.
  Trigger: "workhuman install auth".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hr, recognition, workhuman]
compatible-with: claude-code
---

# Workhuman Install & Auth

## Overview

Configure Workhuman API access for Social Recognition, rewards, and HRIS integration. Workhuman uses OAuth 2.0 for API authentication. The API enables programmatic recognition nominations, reward redemption, and employee data sync.

## Prerequisites

- Workhuman enterprise account with API access enabled
- OAuth client credentials from Workhuman admin portal
- HTTPS endpoint for redirect URI (if using auth code flow)

## Instructions

### Step 1: Configure OAuth Credentials

```bash
# .env
WORKHUMAN_CLIENT_ID=your-client-id
WORKHUMAN_CLIENT_SECRET=your-client-secret
WORKHUMAN_BASE_URL=https://api.workhuman.com
WORKHUMAN_TENANT_ID=your-tenant-id
```

### Step 2: Obtain Access Token (Client Credentials)

```typescript
import axios from 'axios';

async function getWorkhmanToken(): Promise<string> {
  const { data } = await axios.post(
    `${process.env.WORKHUMAN_BASE_URL}/oauth/token`,
    new URLSearchParams({
      grant_type: 'client_credentials',
      client_id: process.env.WORKHUMAN_CLIENT_ID!,
      client_secret: process.env.WORKHUMAN_CLIENT_SECRET!,
    }),
    { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } },
  );
  return data.access_token;
}
```

### Step 3: Verify Connection

```typescript
const token = await getWorkhmanToken();
const api = axios.create({
  baseURL: process.env.WORKHUMAN_BASE_URL,
  headers: { Authorization: `Bearer ${token}` },
});

const { data } = await api.get('/api/v1/users/me');
console.log(`Connected as: ${data.displayName}`);
```

### Step 4: Python Client

```python
import requests, os

class WorkhumanClient:
    def __init__(self):
        self.base = os.environ["WORKHUMAN_BASE_URL"]
        self.token = self._authenticate()

    def _authenticate(self):
        resp = requests.post(f"{self.base}/oauth/token", data={
            "grant_type": "client_credentials",
            "client_id": os.environ["WORKHUMAN_CLIENT_ID"],
            "client_secret": os.environ["WORKHUMAN_CLIENT_SECRET"],
        })
        return resp.json()["access_token"]

    def get(self, endpoint, **params):
        return requests.get(f"{self.base}{endpoint}",
            headers={"Authorization": f"Bearer {self.token}"}, params=params).json()
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid credentials | Check client_id/secret |
| `403 Forbidden` | Insufficient permissions | Contact Workhuman admin |
| `invalid_grant` | Wrong grant type | Use client_credentials |

## Resources

- [Workhuman Platform](https://www.workhuman.com/)
- [Workhuman Integrations](https://www.workhuman.com/capabilities/integrations/)

## Next Steps

Proceed to `workhuman-hello-world` for your first recognition nomination.
