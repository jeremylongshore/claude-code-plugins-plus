---
name: apollo-install-auth
description: |
  Install and configure Apollo.io API authentication.
  Use when setting up a new Apollo integration, configuring API keys,
  or initializing Apollo client in your project.
  Trigger with phrases like "install apollo", "setup apollo api",
  "apollo authentication", "configure apollo api key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, apollo, api, authentication]

---
# Apollo Install & Auth

## Overview
Set up Apollo.io API client and configure authentication credentials. Apollo uses the `x-api-key` HTTP header for authentication against the base URL `https://api.apollo.io/api/v1/`. There is no official SDK — all integrations use the REST API directly.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Apollo.io account with API access (Basic plan or above)
- API key from Apollo dashboard (Settings > Integrations > API Keys)

## Instructions

### Step 1: Install HTTP Client
```bash
set -euo pipefail
# Node.js
npm install axios dotenv

# Python
pip install requests python-dotenv
```

### Step 2: Configure API Key
Apollo supports two API key types:
- **Master API key** — full access to all endpoints (required for contacts, sequences, deals)
- **Standard API key** — limited to search and enrichment only

```bash
# Create .env file (never commit this)
echo 'APOLLO_API_KEY=your-api-key-here' >> .env
echo '.env' >> .gitignore
```

### Step 3: Create Apollo Client (TypeScript)
```typescript
// src/apollo/client.ts
import axios, { AxiosInstance } from 'axios';
import dotenv from 'dotenv';

dotenv.config();

const BASE_URL = 'https://api.apollo.io/api/v1';

export function createApolloClient(apiKey?: string): AxiosInstance {
  const key = apiKey ?? process.env.APOLLO_API_KEY;
  if (!key) throw new Error('APOLLO_API_KEY is not set');

  return axios.create({
    baseURL: BASE_URL,
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'no-cache',
      'x-api-key': key,
    },
    timeout: 30_000,
  });
}

export const apolloClient = createApolloClient();
```

### Step 4: Verify Connection
```typescript
// src/scripts/verify-auth.ts
import { apolloClient } from '../apollo/client';

async function verifyConnection() {
  try {
    // Use the health endpoint to test connectivity
    const response = await apolloClient.get('/auth/health');
    console.log('Apollo connection:', response.data.is_logged_in ? 'OK' : 'Invalid key');
  } catch (error: any) {
    if (error.response?.status === 401) {
      console.error('Invalid API key. Generate a new one at:');
      console.error('  Apollo Dashboard > Settings > Integrations > API Keys');
    } else {
      console.error('Connection failed:', error.message);
    }
  }
}

verifyConnection();
```

### Step 5: Create Apollo Client (Python)
```python
# apollo_client.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

class ApolloClient:
    BASE_URL = 'https://api.apollo.io/api/v1'

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get('APOLLO_API_KEY')
        if not self.api_key:
            raise ValueError('APOLLO_API_KEY is not set')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache',
            'x-api-key': self.api_key,
        })

    def get(self, endpoint: str, **kwargs) -> requests.Response:
        return self.session.get(f'{self.BASE_URL}/{endpoint}', **kwargs)

    def post(self, endpoint: str, json: dict = None, **kwargs) -> requests.Response:
        return self.session.post(f'{self.BASE_URL}/{endpoint}', json=json, **kwargs)

    def verify(self) -> bool:
        resp = self.get('auth/health')
        return resp.json().get('is_logged_in', False)

client = ApolloClient()
print('Connected:', client.verify())
```

## Output
- HTTP client configured with `x-api-key` header authentication
- Environment variable file with `.gitignore` protection
- Successful `/auth/health` verification
- Both TypeScript and Python implementations

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid or missing API key | Verify key in Apollo Dashboard > Settings > Integrations > API Keys |
| 403 Forbidden | Endpoint requires master key | Generate a master API key (not standard) in the dashboard |
| 429 Rate Limited | Too many requests per minute | Implement backoff; see `apollo-rate-limits` |
| Network Error | Firewall blocking outbound HTTPS | Allow outbound to `api.apollo.io` on port 443 |

## Examples

### Quick cURL Verification
```bash
# Test your API key from the command line
curl -s -X GET \
  -H "Content-Type: application/json" \
  -H "Cache-Control: no-cache" \
  -H "x-api-key: $APOLLO_API_KEY" \
  "https://api.apollo.io/api/v1/auth/health" | python3 -m json.tool
```

## Resources
- [Apollo API Documentation](https://docs.apollo.io/)
- [Create API Keys](https://docs.apollo.io/docs/create-api-key)
- [Authentication Reference](https://docs.apollo.io/reference/authentication)
- [Test API Key](https://docs.apollo.io/docs/test-api-key)

## Next Steps
After successful auth, proceed to `apollo-hello-world` for your first API call.
