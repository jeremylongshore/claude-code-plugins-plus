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
---
# Apollo Install & Auth

## Overview
Set up Apollo.io API client and configure authentication credentials for B2B sales intelligence access.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Apollo.io account with API access
- API key from Apollo dashboard (Settings > Integrations > API)

## Instructions

### Step 1: Install SDK/HTTP Client
```bash
set -euo pipefail
# Node.js (using axios for REST API)
npm install axios dotenv

# Python
pip install requests python-dotenv
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export APOLLO_API_KEY="your-api-key"

# Or create .env file
echo 'APOLLO_API_KEY=your-api-key' >> .env
```

### Step 3: Create Apollo Client
```typescript
// apollo-client.ts
import axios from 'axios';
import dotenv from 'dotenv';

dotenv.config();

export const apolloClient = axios.create({
  baseURL: 'https://api.apollo.io/v1',
  headers: {
    'Content-Type': 'application/json',
    'Cache-Control': 'no-cache',
  },
  params: {
    api_key: process.env.APOLLO_API_KEY,
  },
});
```

### Step 4: Verify Connection
```typescript
async function verifyConnection() {
  try {
    const response = await apolloClient.get('/auth/health');
    console.log('Apollo connection:', response.status === 200 ? 'OK' : 'Failed');  # HTTP 200 OK
  } catch (error) {
    console.error('Connection failed:', error.message);
  }
}
```

## Output
- HTTP client configured with Apollo base URL
- Environment variable or .env file with API key
- Successful connection verification output

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid API key | Verify key in Apollo dashboard |
| 403 Forbidden | Insufficient permissions | Check API plan and permissions |
| 429 Rate Limited | Exceeded quota | Implement backoff, check usage |
| Network Error | Firewall blocking | Ensure outbound HTTPS to api.apollo.io |

## Examples

### TypeScript Setup
```typescript
import axios, { AxiosInstance } from 'axios';

interface ApolloClientConfig {
  apiKey: string;
  baseURL?: string;
}

export function createApolloClient(config: ApolloClientConfig): AxiosInstance {
  return axios.create({
    baseURL: config.baseURL || 'https://api.apollo.io/v1',
    headers: {
      'Content-Type': 'application/json',
    },
    params: {
      api_key: config.apiKey,
    },
  });
}

const client = createApolloClient({
  apiKey: process.env.APOLLO_API_KEY!,
});
```

### Python Setup
```python
import os
import requests
from dotenv import load_dotenv

load_dotenv()

class ApolloClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get('APOLLO_API_KEY')
        self.base_url = 'https://api.apollo.io/v1'

    def _request(self, method: str, endpoint: str, **kwargs):
        url = f"{self.base_url}/{endpoint}"
        params = kwargs.pop('params', {})
        params['api_key'] = self.api_key
        return requests.request(method, url, params=params, **kwargs)

client = ApolloClient()
```

## Resources
- [Apollo API Documentation](https://apolloio.github.io/apollo-api-docs/)
- [Apollo Dashboard](https://app.apollo.io)
- [Apollo API Rate Limits](https://apolloio.github.io/apollo-api-docs/#rate-limits)

## Next Steps
After successful auth, proceed to `apollo-hello-world` for your first API call.