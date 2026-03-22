---
name: appfolio-install-auth
description: |
  Configure AppFolio Stack API authentication with OAuth 2.0.
  Use when setting up property management API access, registering as an
  AppFolio Stack partner, or configuring client credentials for API calls.
  Trigger: "install appfolio", "setup appfolio", "appfolio auth", "appfolio API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, property-management, appfolio, real-estate]
compatible-with: claude-code
---

# AppFolio Install & Auth

## Overview

Configure AppFolio Stack API authentication. AppFolio uses HTTP Basic Auth with a client ID and client secret, provided through their Stack partner program. No public npm SDK exists — use direct REST API calls.

## Prerequisites

- AppFolio Stack partner account ([appfolio.com/stack](https://www.appfolio.com/stack/become-a-partner))
- Client ID and Client Secret from AppFolio
- Node.js 18+ or Python 3.10+

## Instructions

### Step 1: Obtain API Credentials

```bash
# AppFolio Stack API credentials come from the partner program
# 1. Apply at appfolio.com/stack/become-a-partner
# 2. Complete integration review
# 3. Receive client_id and client_secret

cat > .env << 'ENVFILE'
APPFOLIO_CLIENT_ID=your-client-id
APPFOLIO_CLIENT_SECRET=your-client-secret
APPFOLIO_BASE_URL=https://your-company.appfolio.com/api/v1
ENVFILE

chmod 600 .env
echo ".env" >> .gitignore
```

### Step 2: Create API Client

```typescript
// src/appfolio-client.ts
import axios, { AxiosInstance } from 'axios';

class AppFolioClient {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: process.env.APPFOLIO_BASE_URL,
      auth: {
        username: process.env.APPFOLIO_CLIENT_ID!,
        password: process.env.APPFOLIO_CLIENT_SECRET!,
      },
      headers: { 'Content-Type': 'application/json' },
      timeout: 30000,
    });
  }

  async verifyConnection(): Promise<boolean> {
    try {
      const response = await this.api.get('/properties');
      console.log(`Connected! Found ${response.data.length} properties`);
      return true;
    } catch (error: any) {
      console.error(`Connection failed: ${error.response?.status} ${error.message}`);
      return false;
    }
  }

  get http(): AxiosInstance { return this.api; }
}

export { AppFolioClient };
```

### Step 3: Verify Connection

```bash
# Quick curl test
curl -u "${APPFOLIO_CLIENT_ID}:${APPFOLIO_CLIENT_SECRET}" \
  "${APPFOLIO_BASE_URL}/properties" | jq '.[0]'
```

## API Endpoints

| Resource | Endpoint | Methods |
|----------|----------|---------|
| Properties | `/api/v1/properties` | GET |
| Units | `/api/v1/units` | GET |
| Tenants | `/api/v1/tenants` | GET |
| Leases | `/api/v1/leases` | GET, POST |
| Bills | `/api/v1/bills` | GET, POST |
| Vendors | `/api/v1/vendors` | GET |
| Owners | `/api/v1/owners` | GET |
| Reports | `/api/v1/reports` | GET |

## Output

- API credentials configured in `.env`
- TypeScript REST client with Basic Auth
- Verified connectivity to AppFolio API

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid credentials | Verify client_id/secret from AppFolio |
| `403 Forbidden` | Not a Stack partner | Complete partner application |
| `404 Not Found` | Wrong base URL | Use `your-company.appfolio.com` format |
| Timeout | Network issue | Check firewall allows HTTPS to appfolio.com |

## Resources

- [AppFolio Stack APIs](https://www.appfolio.com/stack/partners/api)
- [AppFolio Partner Program](https://www.appfolio.com/stack/become-a-partner)
- [AppFolio Engineering Blog](https://engineering.appfolio.com)

## Next Steps

Proceed to `appfolio-hello-world` for your first property query.
