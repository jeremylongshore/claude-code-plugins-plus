---
name: instantly-install-auth
description: |
  Set up Instantly.ai API v2 authentication and project configuration.
  Use when creating a new Instantly integration, generating API keys,
  or configuring environment variables for the Instantly outreach platform.
  Trigger with phrases like "install instantly", "setup instantly",
  "instantly auth", "configure instantly API key", "instantly credentials".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, instantly, api, authentication, email-outreach]

---
# Instantly Install & Auth

## Overview
Configure Instantly.ai API v2 authentication. Instantly uses Bearer token auth with scoped API keys. There is no official SDK — all integrations use direct REST calls to `https://api.instantly.ai/api/v2/`.

## Prerequisites
- Instantly.ai account on Hypergrowth plan ($97/mo) or higher (required for API v2 access)
- Node.js 18+ or Python 3.10+
- Access to Instantly dashboard at `https://app.instantly.ai`

## Instructions

### Step 1: Generate API Key
1. Log into `https://app.instantly.ai`
2. Navigate to **Settings > Integrations > API**
3. Click **Create New API Key**
4. Select scopes (e.g., `campaigns:read`, `leads:all`, `accounts:read`)
5. Copy the key — it is shown only once

```bash
set -euo pipefail
# Create .env file with your API key
cat > .env << 'ENVEOF'
INSTANTLY_API_KEY=your-api-key-here
INSTANTLY_BASE_URL=https://api.instantly.ai/api/v2
ENVEOF
echo "Created .env with Instantly config"
```

Available API scopes (resource:action format):
| Scope | Access |
|-------|--------|
| `campaigns:read` | List/get campaigns and analytics |
| `campaigns:update` | Create, patch, activate, pause campaigns |
| `campaigns:all` | Full campaign CRUD + analytics |
| `accounts:read` | List/get email accounts |
| `accounts:update` | Create, warmup, pause accounts |
| `leads:read` | List/get leads and lead lists |
| `leads:update` | Create, move, delete leads |
| `leads:all` | Full lead CRUD |
| `all:all` | Unrestricted access (dev only) |

### Step 2: Create API Client Wrapper (TypeScript)
```typescript
// src/instantly.ts
import "dotenv/config";

const BASE = process.env.INSTANTLY_BASE_URL || "https://api.instantly.ai/api/v2";
const API_KEY = process.env.INSTANTLY_API_KEY;

if (!API_KEY) throw new Error("INSTANTLY_API_KEY is required");

export async function instantly<T = unknown>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${BASE}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${API_KEY}`,
      ...options.headers,
    },
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Instantly API ${res.status}: ${body}`);
  }

  return res.json() as Promise<T>;
}
```

### Step 3: Create API Client Wrapper (Python)
```python
# instantly_client.py
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("INSTANTLY_BASE_URL", "https://api.instantly.ai/api/v2")
API_KEY = os.getenv("INSTANTLY_API_KEY")

if not API_KEY:
    raise ValueError("INSTANTLY_API_KEY environment variable is required")

client = httpx.Client(
    base_url=BASE_URL,
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    },
    timeout=30.0,
)

def instantly_get(path: str, params: dict = None):
    r = client.get(path, params=params)
    r.raise_for_status()
    return r.json()

def instantly_post(path: str, json_data: dict = None):
    r = client.post(path, json=json_data)
    r.raise_for_status()
    return r.json()
```

### Step 4: Verify Connection
```typescript
// verify.ts — run with: npx tsx verify.ts
import { instantly } from "./src/instantly";

interface Campaign {
  id: string;
  name: string;
  status: number;
}

async function verify() {
  // List campaigns — if this returns, auth is working
  const campaigns = await instantly<Campaign[]>("/campaigns?limit=1");
  console.log("Auth verified. Campaigns found:", campaigns.length >= 0);

  // List email accounts
  const accounts = await instantly<{ email: string }[]>("/accounts?limit=1");
  console.log("Accounts accessible:", accounts.length >= 0);

  console.log("Instantly API v2 connection is working.");
}

verify().catch((err) => {
  console.error("Auth failed:", err.message);
  process.exit(1);
});
```

## Output
- `.env` file with `INSTANTLY_API_KEY` and `INSTANTLY_BASE_URL`
- Reusable API client wrapper (`src/instantly.ts` or `instantly_client.py`)
- Verified connection to Instantly API v2

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid or expired API key | Regenerate key in Settings > Integrations |
| `403 Forbidden` | Key missing required scope | Edit key scopes or create new key with correct permissions |
| `429 Too Many Requests` | Rate limit exceeded | Implement exponential backoff (see `instantly-rate-limits`) |
| `ECONNREFUSED` | Network/firewall issue | Ensure outbound HTTPS to `api.instantly.ai` is allowed |
| `API key not found` | Key was revoked | Generate a new key from the dashboard |

## Resources
- [Instantly API v2 Docs](https://developer.instantly.ai/)
- [API v1 to v2 Migration Guide](https://developer.instantly.ai/api-v1-docs)
- [Instantly Help Center](https://help.instantly.ai)

## Next Steps
After successful auth, proceed to `instantly-hello-world` for your first API call.
