---
name: gamma-install-auth
description: |
  Set up Gamma API v1.0 authentication and first request.
  Use when configuring API keys, setting up X-API-KEY header,
  or initializing Gamma REST API access in a project.
  Trigger: "install gamma", "setup gamma API", "gamma auth",
  "gamma API key", "configure gamma".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(npm:*), Bash(pip:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, gamma, api, authentication]

---
# Gamma Install & Auth

## Overview

Configure authentication for the Gamma Generate API v1.0 (GA since Nov 2025). Gamma uses a REST API at `https://public-api.gamma.app/v1.0/` — there is no official SDK package. All requests authenticate via the `X-API-KEY` header.

## Prerequisites

- Gamma Pro account or higher (API access requires Pro+)
- Node.js 18+ or Python 3.10+ for wrapper code
- `curl` or HTTP client library

## Instructions

### Step 1: Generate API Key

1. Log in at [gamma.app](https://gamma.app)
2. Navigate to **Settings and Members** (dropdown, upper-left)
3. Select the **API key** tab
4. Click **Create API key**
5. Copy and securely store the key — it will not be shown again

### Step 2: Configure Environment

```bash
# Set environment variable (add to .env or shell profile)
export GAMMA_API_KEY="gma_your_api_key_here"

# .env file approach
echo 'GAMMA_API_KEY=gma_your_api_key_here' >> .env
```

### Step 3: Verify Connection

```bash
# Quick verification with curl
curl -s -o /dev/null -w "%{http_code}" \
  -H "X-API-KEY: ${GAMMA_API_KEY}" \
  https://public-api.gamma.app/v1.0/themes
# 200 = authenticated, 401 = invalid key
```

### Step 4: First API Call (Node.js)

```typescript
// gamma-client.ts — thin wrapper around the REST API
const GAMMA_BASE = "https://public-api.gamma.app/v1.0";

interface GammaConfig {
  apiKey: string;
  baseUrl?: string;
}

export function createGammaClient(config: GammaConfig) {
  const headers = {
    "X-API-KEY": config.apiKey,
    "Content-Type": "application/json",
  };
  const base = config.baseUrl ?? GAMMA_BASE;

  return {
    async listThemes() {
      const res = await fetch(`${base}/themes`, { headers });
      if (!res.ok) throw new Error(`Gamma API ${res.status}: ${await res.text()}`);
      return res.json();
    },
    async listFolders() {
      const res = await fetch(`${base}/folders`, { headers });
      if (!res.ok) throw new Error(`Gamma API ${res.status}: ${await res.text()}`);
      return res.json();
    },
  };
}

// Verify connection
const gamma = createGammaClient({ apiKey: process.env.GAMMA_API_KEY! });
const themes = await gamma.listThemes();
console.log(`Connected — ${themes.length} workspace themes available`);
```

### Step 5: First API Call (Python)

```python
import os, requests

GAMMA_BASE = "https://public-api.gamma.app/v1.0"
HEADERS = {
    "X-API-KEY": os.environ["GAMMA_API_KEY"],
    "Content-Type": "application/json",
}

# Verify connection
resp = requests.get(f"{GAMMA_BASE}/themes", headers=HEADERS)
resp.raise_for_status()
themes = resp.json()
print(f"Connected — {len(themes)} workspace themes available")
```

## API Key Security

| Practice | Implementation |
|----------|---------------|
| Never commit keys | Add `GAMMA_API_KEY` to `.gitignore` and `.env` |
| Rotate regularly | Regenerate in Settings > API key tab |
| Scope per environment | Separate keys for dev/staging/prod workspaces |
| Audit usage | Monitor credit consumption at gamma.app/settings/billing |

## Error Handling

| HTTP Status | Meaning | Fix |
|-------------|---------|-----|
| 401 Unauthorized | Invalid or missing API key | Verify `X-API-KEY` header value |
| 403 Forbidden | Account not on Pro+ plan | Upgrade at gamma.app/pricing |
| 429 Too Many Requests | Rate limit exceeded | Implement backoff; contact Gamma support for higher limits |
| 5xx Server Error | Gamma service issue | Retry with exponential backoff |

## Important Notes

- **No SDK**: Gamma does not publish an npm/pip package. Use `fetch`/`requests` directly.
- **Header format**: Use `X-API-KEY`, not `Authorization: Bearer`.
- **API v0.2 sunset**: v0.2 was deprecated Jan 2026. Use v1.0 only.
- **Credit system**: API calls consume credits based on image model tier (Standard 2-15, Advanced 20-33, Premium 34-75, Ultra 30-125 credits/image).

## Resources

- [Gamma Developer Docs](https://developers.gamma.app/)
- [Getting Started Guide](https://developers.gamma.app/docs/getting-started)
- [Access and Pricing](https://developers.gamma.app/docs/get-access)
- [API Key Management](https://gamma.app/settings)

## Next Steps

Proceed to `gamma-hello-world` for your first presentation generation.
