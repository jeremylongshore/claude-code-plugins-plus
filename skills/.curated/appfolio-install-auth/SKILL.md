---
name: appfolio-install-auth
description: 'Configure AppFolio Stack API authentication with OAuth 2.0.

  Use when setting up property management API access, registering as an

  AppFolio Stack partner, or configuring client credentials for API calls.

  Trigger: "install appfolio", "setup appfolio", "appfolio auth", "appfolio API key".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.5.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- property-management
- appfolio
- real-estate
compatibility: Designed for Claude Code
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
# 3. Receive the provider-issued base URL and credential delivery instructions.
# Store the values in the approved secret manager. Commit only this non-secret
# template if local development requires one:
cat > .env.example << 'ENVFILE'
APPFOLIO_CLIENT_ID=
APPFOLIO_CLIENT_SECRET=
APPFOLIO_BASE_URL=
ENVFILE

# .env remains ignored; populate it only through an approved local secret flow.
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
# Quick, redacted diagnostic without putting Basic Auth in argv.
NETRC_FILE="$(mktemp)"
trap 'rm -f "$NETRC_FILE"' EXIT
chmod 600 "$NETRC_FILE"
APPFOLIO_HOST="${APPFOLIO_BASE_URL#https://}"
APPFOLIO_HOST="${APPFOLIO_HOST%%/*}"
printf 'machine %s login %s password %s\n' "$APPFOLIO_HOST" \
  "$APPFOLIO_CLIENT_ID" "$APPFOLIO_CLIENT_SECRET" > "$NETRC_FILE"
curl -s -o /dev/null -w '%{http_code}\n' --netrc-file "$NETRC_FILE" \
  "${APPFOLIO_BASE_URL}/properties"
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

- Provider-issued credentials injected through the approved secret boundary
- TypeScript REST client with Basic Auth
- Redacted connectivity result for the approved safe-read endpoint

## Examples

For a first authentication rehearsal, inject a sandbox credential and the
provider-issued base URL through the local secret mechanism, then make one
read-only request to an approved synthetic property page. Record only the
status code and client configuration verdict; do not print a property payload,
client ID, secret, or full host/path in shared logs. If the contract, base URL,
secret binding, or status result is unverified, stop before any write workflow
and have the credential owner correct the configuration.

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
