---
name: maintainx-install-auth
description: |
  Install and configure MaintainX REST API authentication.
  Use when setting up a new MaintainX integration, configuring API keys,
  or initializing MaintainX API access in your project.
  Trigger with phrases like "install maintainx", "setup maintainx",
  "maintainx auth", "configure maintainx API key", "maintainx credentials".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# MaintainX Install & Auth

## Overview

Set up MaintainX REST API authentication and configure your development environment for CMMS integration.

## Prerequisites

- Node.js 18+ or Python 3.10+
- MaintainX account with API access (Professional or Enterprise plan)
- Admin access to generate API keys

## Instructions

### Step 1: Generate API Key

1. Log into MaintainX at https://app.getmaintainx.com
2. Navigate to **Settings** > **Integrations**
3. Click **New Key** > **Generate Key**
4. Copy and securely store your API key (shown only once)

### Step 2: Configure Environment Variables

```bash
# Set environment variable
export MAINTAINX_API_KEY="your-api-key-here"

# Or create .env file
echo 'MAINTAINX_API_KEY=your-api-key' >> .env

# For multi-organization tokens, also set:
export MAINTAINX_ORG_ID="your-organization-id"
```

### Step 3: Create API Client Wrapper

```typescript
// src/maintainx/client.ts
import axios, { AxiosInstance, AxiosError } from 'axios';

export class MaintainXClient {
  private client: AxiosInstance;
  private baseUrl = 'https://api.getmaintainx.com/v1';

  constructor(apiKey?: string, orgId?: string) {
    const key = apiKey || process.env.MAINTAINX_API_KEY;
    if (!key) {
      throw new Error('MAINTAINX_API_KEY is required');
    }

    this.client = axios.create({
      baseURL: this.baseUrl,
      headers: {
        'Authorization': `Bearer ${key}`,
        'Content-Type': 'application/json',
        ...(orgId && { 'X-Organization-Id': orgId }),
      },
    });

    this.client.interceptors.response.use(
      response => response,
      this.handleError
    );
  }

  private handleError(error: AxiosError) {
    if (error.response) {
      const { status, data } = error.response;
      console.error(`MaintainX API Error [${status}]:`, data);
    }
    throw error;
  }

  // Core API methods
  async getWorkOrders(params?: WorkOrderQueryParams) {
    return this.client.get('/workorders', { params });
  }

  async getWorkOrder(id: string) {
    return this.client.get(`/workorders/${id}`);
  }

  async createWorkOrder(data: CreateWorkOrderInput) {
    return this.client.post('/workorders', data);
  }

  async getAssets(params?: AssetQueryParams) {
    return this.client.get('/assets', { params });
  }

  async getLocations(params?: LocationQueryParams) {
    return this.client.get('/locations', { params });
  }

  async getUsers(params?: UserQueryParams) {
    return this.client.get('/users', { params });
  }
}

// Type definitions
interface WorkOrderQueryParams {
  cursor?: string;
  limit?: number;
  status?: 'OPEN' | 'IN_PROGRESS' | 'ON_HOLD' | 'DONE';
}

interface CreateWorkOrderInput {
  title: string;
  description?: string;
  priority?: 'NONE' | 'LOW' | 'MEDIUM' | 'HIGH';
  assignees?: string[];
  assetId?: string;
  locationId?: string;
  dueDate?: string;
}

interface AssetQueryParams {
  cursor?: string;
  limit?: number;
  locationId?: string;
}

interface LocationQueryParams {
  cursor?: string;
  limit?: number;
}

interface UserQueryParams {
  cursor?: string;
  limit?: number;
}
```

### Step 4: Verify Connection

```typescript
// test-connection.ts
import { MaintainXClient } from './maintainx/client';

async function testConnection() {
  const client = new MaintainXClient();

  try {
    const response = await client.getUsers({ limit: 1 });
    console.log('Connection successful!');
    console.log('Organization has users:', response.data.users.length > 0);
    return true;
  } catch (error) {
    console.error('Connection failed:', error);
    return false;
  }
}

testConnection();
```

```bash
# Run test
npx ts-node test-connection.ts
```

### Python Alternative

```python
# maintainx_client.py
import os
import requests
from typing import Optional, Dict, Any

class MaintainXClient:
    BASE_URL = "https://api.getmaintainx.com/v1"

    def __init__(self, api_key: Optional[str] = None, org_id: Optional[str] = None):
        self.api_key = api_key or os.environ.get("MAINTAINX_API_KEY")
        if not self.api_key:
            raise ValueError("MAINTAINX_API_KEY is required")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if org_id:
            self.headers["X-Organization-Id"] = org_id

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.BASE_URL}{endpoint}"
        response = requests.request(method, url, headers=self.headers, **kwargs)
        response.raise_for_status()
        return response.json()

    def get_work_orders(self, **params) -> Dict[str, Any]:
        return self._request("GET", "/workorders", params=params)

    def create_work_order(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/workorders", json=data)

    def get_assets(self, **params) -> Dict[str, Any]:
        return self._request("GET", "/assets", params=params)

    def get_locations(self, **params) -> Dict[str, Any]:
        return self._request("GET", "/locations", params=params)

# Test connection
if __name__ == "__main__":
    client = MaintainXClient()
    users = client._request("GET", "/users", params={"limit": 1})
    print("Connection successful!")
    print(f"Found {len(users.get('users', []))} users")
```

## Output

- Environment variable or `.env` file with API key configured
- MaintainX client wrapper installed and configured
- Successful connection verification output

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid or expired API key | Generate new key in Settings > Integrations |
| 403 Forbidden | Insufficient permissions | Ensure admin role or correct plan tier |
| 404 Not Found | Wrong base URL or endpoint | Use `api.getmaintainx.com/v1` |
| Network Error | Firewall blocking HTTPS | Allow outbound 443 to getmaintainx.com |

## Security Best Practices

1. **Never commit API keys** to version control
2. Use environment variables or secret managers
3. Rotate keys periodically (every 90 days recommended)
4. Use organization-specific keys for multi-tenant setups
5. Limit key scope to required operations only

## Resources

- [MaintainX API Documentation](https://maintainx.dev/)
- [MaintainX Help Center](https://help.getmaintainx.com/)
- [Generating API Keys](https://intercom.help/maintainx/en/articles/5658848-generating-api-key-to-integrate-with-other-systems)

## Next Steps

After successful auth, proceed to `maintainx-hello-world` for your first API call.

## Examples

**Quick test with curl**:

```bash
curl -s https://api.getmaintainx.com/v1/users?limit=1 \
  -H "Authorization: Bearer $MAINTAINX_API_KEY" | jq .
```

**Multi-org setup** (for contractors managing multiple facilities):

```typescript
const clients = {
  plantA: new MaintainXClient(process.env.MAINTAINX_KEY_PLANT_A, 'org-plant-a'),
  plantB: new MaintainXClient(process.env.MAINTAINX_KEY_PLANT_B, 'org-plant-b'),
};
const orders = await clients.plantA.getWorkOrders({ status: 'OPEN' });
```