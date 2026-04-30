---
name: navan-install-auth
description: 'Set up OAuth 2.0 authentication for the Navan REST API.

  Use when configuring a new Navan integration or rotating API credentials.

  Trigger with "install navan", "setup navan auth", "navan credentials", "navan oauth".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- navan
- travel
compatibility: Designed for Claude Code
---
# Navan Install & Auth

## Overview

Configure OAuth 2.0 client credentials for the Navan REST API. Navan has **no public SDK** — all API access uses raw REST calls with bearer tokens obtained via the client_credentials grant.

**Purpose:** Obtain a working OAuth 2.0 bearer token for calling Navan API endpoints.

## Prerequisites

- **Navan admin access** — you need the Admin or Travel Admin role
- **Node.js 18+** (for TypeScript) or **Python 3.8+** (for Python)
- A `.env`-aware project (dotenv for Node, python-dotenv for Python)
- Navan Business tier or higher (free for up to 300 employees)

## Instructions

### Step 1: Create OAuth Credentials in Navan Dashboard

Navigate to: **Admin > Travel admin > Settings > Integrations > Navan API Credentials > Create New**

Save the `client_id` and `client_secret` immediately — credentials are **only viewable once**. If lost, you must revoke and regenerate.

### Step 2: Store Credentials Securely

Create a `.env` file in your project root:

```bash
# .env — NEVER commit this file
NAVAN_CLIENT_ID="your-client-id-here"
NAVAN_CLIENT_SECRET="your-client-secret-here"
NAVAN_BASE_URL="https://api.navan.com"
```

Ensure `.env` is in your `.gitignore`:

```bash
echo ".env" >> .gitignore
```

### Step 3: Token Exchange (TypeScript)

Install dependencies and implement the OAuth 2.0 client credentials flow:

```bash
npm install dotenv
```

```typescript
import 'dotenv/config';

interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

async function getNavanToken(): Promise<string> {
  const response = await fetch(`${process.env.NAVAN_BASE_URL}/ta-auth/oauth/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'client_credentials',
      client_id: process.env.NAVAN_CLIENT_ID!,
      client_secret: process.env.NAVAN_CLIENT_SECRET!,
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Auth failed (${response.status}): ${error}`);
  }

  const data: TokenResponse = await response.json();
  return data.access_token;
}

// Verify connection
const token = await getNavanToken();
console.log('Auth successful — token acquired');
```

### Step 4: Token Exchange (Python)

```bash
pip install requests python-dotenv
```

```python
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def get_navan_token() -> str:
    """Exchange client credentials for an OAuth 2.0 bearer token."""
    response = requests.post(
        f"{os.environ['NAVAN_BASE_URL']}/ta-auth/oauth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": os.environ["NAVAN_CLIENT_ID"],
            "client_secret": os.environ["NAVAN_CLIENT_SECRET"],
        },
    )
    response.raise_for_status()
    return response.json()["access_token"]

token = get_navan_token()
print("Auth successful — token acquired")
```

### Step 5: Verify Connection

Make an authenticated API call to confirm credentials work:

```typescript
const bookings = await fetch(`${process.env.NAVAN_BASE_URL}/v1/bookings?page=0&size=50`, {
  headers: { Authorization: `Bearer ${token}` },
});

if (bookings.ok) {
  const { data } = await bookings.json();
  console.log(`Connection verified — retrieved ${data.length} bookings`);
} else {
  console.error(`Verification failed: ${bookings.status}`);
}
```

## Output

Successful completion produces:
- OAuth 2.0 `client_id` and `client_secret` stored in `.env`
- A `getNavanToken()` function (TypeScript or Python) returning a bearer token
- A verified connection to the Navan API confirmed by a successful GET request

## Error Handling

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| Invalid credentials | 401 | Wrong client_id or client_secret | Regenerate credentials in Admin > Integrations |
| Insufficient permissions | 403 | Account lacks API access or wrong tier | Contact Navan support to enable API access |
| Rate limited | 429 | Too many auth requests | Implement token caching (see navan-local-dev-loop) |
| Endpoint not found | 404 | Wrong base URL or path | Verify NAVAN_BASE_URL is `https://api.navan.com` |
| Server error | 500 | Navan service issue | Retry after 30 seconds; check Navan status page |
| Service unavailable | 503 | Navan maintenance window | Wait and retry; check for scheduled maintenance |

## Examples

**Minimal auth check script:**

```bash
# Quick credential test with curl
curl -s -X POST https://api.navan.com/ta-auth/oauth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=$NAVAN_CLIENT_ID&client_secret=$NAVAN_CLIENT_SECRET" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if 'access_token' in d else 'FAIL')"
```

## Resources

- [Navan Help Center](https://app.navan.com/app/helpcenter) — primary documentation hub
- [Navan TMC API Documentation](https://app.navan.com/app/helpcenter/articles/travel/admin/other-integrations/navan-tmc-api-integration-documentation) — API integration guide
- [Navan Integrations](https://navan.com/integrations) — available integration partners
- [Navan Security & Compliance](https://navan.com/security) — SOC 2 Type II, ISO 27001, PCI DSS Level 1

## Next Steps

After authentication is working, proceed to `navan-hello-world` to make your first API call, or see `navan-sdk-patterns` to build a reusable typed wrapper.
