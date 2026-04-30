---
name: navan-multi-env-setup
description: 'Set up dev/staging/prod environment separation for Navan integrations
  without a sandbox API.

  Use when configuring multiple environments, building CI test pipelines, or setting
  up local development.

  Trigger with "navan environments", "navan multi env", "navan dev setup", "navan
  mock server".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- navan
- travel
compatibility: Designed for Claude Code
---
# Navan Multi-Environment Setup

## Overview
Navan does not offer a sandbox or staging API — every call hits production data with real corporate bookings and expense records. This creates risk for development and testing: a bug in a sync script could modify live itineraries, and CI pipelines cannot safely run integration tests. This skill implements environment isolation using separate OAuth apps, environment variable validation, a local development proxy, and a CI mock server.

## Prerequisites
- Navan admin access to create multiple OAuth apps (Admin > Travel admin > Settings > Integrations)
- Node.js 18+ for proxy and mock server
- Understanding of OAuth 2.0 client credentials flow (see `navan-install-auth`)
- `.env` management tooling (dotenv, direnv, or cloud secret manager)

## Instructions

### Step 1: Create Per-Environment OAuth Apps
Create separate API credentials in the Navan admin dashboard for each environment. This provides natural isolation — the dev app can have read-only scopes while production gets full access.

```bash
# .env.development — read-only scoped OAuth app
NAVAN_ENV=development
NAVAN_CLIENT_ID=dev-client-id-xxxxx
NAVAN_CLIENT_SECRET=dev-client-secret-xxxxx
NAVAN_API_BASE=https://api.navan.com/v1
NAVAN_READ_ONLY=true

# .env.staging — read + limited write, separate audit trail
NAVAN_ENV=staging
NAVAN_CLIENT_ID=stg-client-id-xxxxx
NAVAN_CLIENT_SECRET=stg-client-secret-xxxxx
NAVAN_API_BASE=https://api.navan.com/v1
NAVAN_READ_ONLY=false

# .env.production — full access, rotation-managed
NAVAN_ENV=production
NAVAN_CLIENT_ID=prod-client-id-xxxxx
NAVAN_CLIENT_SECRET=prod-client-secret-xxxxx
NAVAN_API_BASE=https://api.navan.com/v1
NAVAN_READ_ONLY=false
```

### Step 2: Build an Environment-Aware Client
```typescript
import { config } from 'dotenv';

interface NavanConfig {
  env: string;
  clientId: string;
  clientSecret: string;
  apiBase: string;
  readOnly: boolean;
}

function loadConfig(): NavanConfig {
  const envFile = `.env.${process.env.NODE_ENV || 'development'}`;
  config({ path: envFile });

  const required = ['NAVAN_CLIENT_ID', 'NAVAN_CLIENT_SECRET', 'NAVAN_API_BASE'];
  for (const key of required) {
    if (!process.env[key]) {
      throw new Error(`Missing ${key} in ${envFile}`);
    }
  }

  return {
    env: process.env.NAVAN_ENV || 'development',
    clientId: process.env.NAVAN_CLIENT_ID!,
    clientSecret: process.env.NAVAN_CLIENT_SECRET!,
    apiBase: process.env.NAVAN_API_BASE!,
    readOnly: process.env.NAVAN_READ_ONLY === 'true'
  };
}

class NavanClient {
  private config: NavanConfig;
  private accessToken: string | null = null;

  constructor() {
    this.config = loadConfig();
    console.log(`Navan client initialized [${this.config.env}] readOnly=${this.config.readOnly}`);
  }

  async request(method: string, path: string, body?: object): Promise<any> {
    // Block writes in read-only environments
    if (this.config.readOnly && method !== 'GET') {
      throw new Error(`Write operations blocked in ${this.config.env} (read-only mode)`);
    }

    if (!this.accessToken) {
      this.accessToken = await this.authenticate();
    }

    const response = await fetch(`${this.config.apiBase}${path}`, {
      method,
      headers: {
        'Authorization': `Bearer ${this.accessToken}`,
        'Content-Type': 'application/json'
      },
      body: body ? JSON.stringify(body) : undefined
    });

    if (!response.ok) {
      throw new Error(`Navan API error: HTTP ${response.status} on ${method} ${path}`);
    }
    return response.json();
  }

  private async authenticate(): Promise<string> {
    const res = await fetch('https://api.navan.com/ta-auth/oauth/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        grant_type: 'client_credentials',
        client_id: this.config.clientId,
        client_secret: this.config.clientSecret
      })
    });
    const { access_token } = await res.json();
    return access_token;
  }
}
```

### Step 3: Create a Local Development Proxy
```typescript
import express from 'express';

// Proxy that logs all requests and optionally blocks writes
const proxy = express();

proxy.use(express.json());
proxy.all('/navan/*', async (req, res) => {
  const navanPath = req.path.replace('/navan', '');
  const method = req.method;

  // Log every request for debugging
  console.log(`[PROXY] ${method} ${navanPath}`);
  if (req.body && Object.keys(req.body).length > 0) {
    console.log(`[PROXY] Body:`, JSON.stringify(req.body, null, 2));
  }

  // In dev mode, block mutating operations
  if (process.env.NAVAN_READ_ONLY === 'true' && method !== 'GET') {
    console.log(`[PROXY] BLOCKED: ${method} ${navanPath} (read-only mode)`);
    return res.status(403).json({
      error: 'Write operation blocked in development mode',
      method, path: navanPath
    });
  }

  // Forward to real Navan API
  try {
    const response = await fetch(`https://api.navan.com/v1${navanPath}`, {
      method,
      headers: {
        'Authorization': req.headers.authorization as string,
        'Content-Type': 'application/json'
      },
      body: ['POST', 'PUT', 'PATCH'].includes(method)
        ? JSON.stringify(req.body) : undefined
    });

    const data = await response.json();
    console.log(`[PROXY] Response: ${response.status}`);
    res.status(response.status).json(data);
  } catch (err: any) {
    console.error(`[PROXY] Error:`, err.message);
    res.status(502).json({ error: 'Proxy error', message: err.message });
  }
});

proxy.listen(4000, () => console.log('Navan dev proxy on http://localhost:4000'));
```

### Step 4: Build a CI Mock Server
```typescript
import express from 'express';
const mock = express();
mock.use(express.json());

// Mock data store
const mockData = {
  users: [
    { id: 'user-001', email: 'traveler@company.com', role: 'traveler', department: 'engineering' }
  ],
  trips: [
    { id: 'trip-001', traveler_id: 'user-001', status: 'confirmed', total: 450.00 }
  ],
  expenses: [
    { id: 'exp-001', submitter_id: 'user-001', amount: 125.50, status: 'submitted' }
  ]
};

// OAuth token endpoint
mock.post('/ta-auth/oauth/token', (req, res) => {
  res.json({ access_token: 'mock-token-ci', expires_in: 3600, token_type: 'Bearer' });
});

// Users
mock.get('/v1/users', (req, res) => {
  res.json({ data: mockData.users, total: mockData.users.length, has_more: false });
});

// Trips
mock.get('/v1/trips', (req, res) => {
  res.json({ data: mockData.trips, total: mockData.trips.length, has_more: false });
});

// Expenses
mock.get('/v1/expenses', (req, res) => {
  res.json({ data: mockData.expenses, total: mockData.expenses.length, has_more: false });
});

// Catch-all for unimplemented endpoints
mock.all('*', (req, res) => {
  console.log(`[MOCK] Unhandled: ${req.method} ${req.path}`);
  res.status(501).json({ error: 'Not implemented in mock', path: req.path });
});

const port = process.env.MOCK_PORT || 4001;
mock.listen(port, () => console.log(`Navan mock server on http://localhost:${port}`));
```

### Step 5: Wire Mock Server into CI
```yaml
# .github/workflows/test.yml
- name: Start Navan mock server
  run: |
    node navan-mock-server.js &
    sleep 2
  env:
    MOCK_PORT: 4001

- name: Run integration tests
  run: npm test
  env:
    NAVAN_API_BASE: http://localhost:4001/v1
    NAVAN_CLIENT_ID: ci-test-client
    NAVAN_CLIENT_SECRET: ci-test-secret
    NODE_ENV: test
```

## Output
A complete environment isolation strategy for Navan integrations: separate OAuth apps per environment with scoped permissions, an environment-aware client with write protection, a local dev proxy for request logging and mutation blocking, and a CI-ready mock server that eliminates production API dependencies from automated tests.

## Error Handling
| Error | Code | Solution |
|-------|------|----------|
| Missing env vars | N/A | Config loader throws on startup; check the correct `.env.<environment>` file exists |
| Write blocked in read-only | 403 | Expected in dev mode; switch to staging/prod for write operations |
| Mock endpoint not found | 501 | Add the endpoint to mock server; check test expectations match mock data |
| Proxy connection refused | 502 | Ensure the proxy server is running; check port availability |
| Wrong environment loaded | N/A | Verify NODE_ENV matches the intended `.env.<environment>` file |

## Examples

**Validate environment configuration:**
```bash
# Check which environment would load
NODE_ENV=staging node -e "
  require('dotenv').config({ path: '.env.staging' });
  console.log('ENV:', process.env.NAVAN_ENV);
  console.log('READ_ONLY:', process.env.NAVAN_READ_ONLY);
  console.log('CLIENT_ID:', process.env.NAVAN_CLIENT_ID?.slice(0, 8) + '...');
"
```

**Run tests against mock server locally:**
```bash
# Terminal 1: Start mock
MOCK_PORT=4001 node navan-mock-server.js

# Terminal 2: Run tests
NAVAN_API_BASE=http://localhost:4001/v1 npm test
```

## Resources
- [Navan Help Center](https://app.navan.com/app/helpcenter) — API credential creation and management
- [Navan Integrations](https://navan.com/integrations) — Available integration patterns and partners
- [Navan Security](https://navan.com/security) — Data handling and environment security policies
- [dotenv Documentation](https://github.com/motdotla/dotenv) — Environment variable management for Node.js

## Next Steps
After setting up environments, see `navan-security-basics` for credential rotation across all environments, or `navan-ci-integration` for building the full CI/CD pipeline with Navan API tests.
