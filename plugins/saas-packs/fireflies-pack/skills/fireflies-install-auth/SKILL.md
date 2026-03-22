---
name: fireflies-install-auth
description: |
  Configure Fireflies.ai GraphQL API authentication and verify connectivity.
  Use when setting up a new Fireflies.ai integration, configuring API keys,
  or initializing the GraphQL client for transcript access.
  Trigger with phrases like "install fireflies", "setup fireflies",
  "fireflies auth", "configure fireflies API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, fireflies, api, authentication]

---
# Fireflies.ai Install & Auth

## Overview
Set up Fireflies.ai GraphQL API authentication. Fireflies uses a single GraphQL endpoint at `https://api.fireflies.ai/graphql` with Bearer token auth. No SDK needed -- all interaction is via HTTP POST with GraphQL queries.

## Prerequisites
- Fireflies.ai account (Pro or higher for API access)
- API key from app.fireflies.ai > Integrations > Fireflies API
- Node.js 18+ or Python 3.10+
- A GraphQL client library (optional but recommended)

## Instructions

### Step 1: Get Your API Key
1. Log in at [app.fireflies.ai](https://app.fireflies.ai)
2. Navigate to **Integrations > Fireflies API**
3. Copy your API key (starts with a long alphanumeric string)
4. Store it securely -- this key grants access to all your meeting data

### Step 2: Configure Environment
```bash
set -euo pipefail
# Create .env file (NEVER commit to git)
echo 'FIREFLIES_API_KEY=your-api-key-here' >> .env

# Add to .gitignore
echo '.env' >> .gitignore
echo '.env.local' >> .gitignore
```

### Step 3: Install GraphQL Client (Optional)
```bash
set -euo pipefail
# Node.js -- graphql-request is lightweight and typed
npm install graphql-request graphql

# Or use plain fetch -- no library needed
# Python -- use requests
pip install requests
```

### Step 4: Verify Connection
```typescript
// verify-fireflies.ts
const FIREFLIES_API = "https://api.fireflies.ai/graphql";

async function verifyConnection() {
  const query = `{ user { name email is_admin } }`;

  const response = await fetch(FIREFLIES_API, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${process.env.FIREFLIES_API_KEY}`,
    },
    body: JSON.stringify({ query }),
  });

  const result = await response.json();

  if (result.errors) {
    throw new Error(`Auth failed: ${result.errors[0].message}`);
  }

  const user = result.data.user;
  console.log(`Connected as: ${user.name} (${user.email})`);
  console.log(`Admin: ${user.is_admin}`);
  return user;
}

verifyConnection().catch(console.error);
```

### Step 5: Verify with cURL
```bash
set -euo pipefail
curl -s -X POST https://api.fireflies.ai/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $FIREFLIES_API_KEY" \
  -d '{"query": "{ user { name email } }"}' | jq .
```

### Python Verification
```python
import os, requests

FIREFLIES_API = "https://api.fireflies.ai/graphql"

def verify_connection():
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ['FIREFLIES_API_KEY']}",
    }
    query = '{ user { name email is_admin } }'
    resp = requests.post(FIREFLIES_API, json={"query": query}, headers=headers)
    data = resp.json()

    if "errors" in data:
        raise Exception(f"Auth failed: {data['errors'][0]['message']}")

    user = data["data"]["user"]
    print(f"Connected as: {user['name']} ({user['email']})")
    return user

verify_connection()
```

## Rate Limits by Plan

| Plan | Limit | Notes |
|------|-------|-------|
| Free / Pro | 50 requests/day | Cannot upload audio on Free |
| Business | 60 requests/min | Full API access |
| Enterprise | 60 requests/min | Super Admin webhooks |

## Error Handling
| Error | Code | Solution |
|-------|------|----------|
| `auth_failed` | 401 | Check API key is valid and not expired |
| `too_many_requests` | 429 | Rate limit hit -- back off and retry |
| `account_cancelled` | 403 | Subscription inactive -- renew plan |
| Network timeout | - | Verify outbound HTTPS to api.fireflies.ai |

## Output
- Environment variable configured with API key
- GraphQL client verified against `https://api.fireflies.ai/graphql`
- User identity confirmed via `user` query

## Resources
- [Fireflies API Documentation](https://docs.fireflies.ai/)
- [Fireflies Quickstart](https://docs.fireflies.ai/getting-started/quickstart)
- [Fireflies API Key](https://app.fireflies.ai) (Integrations > Fireflies API)

## Next Steps
After successful auth, proceed to `fireflies-hello-world` for your first transcript query.
