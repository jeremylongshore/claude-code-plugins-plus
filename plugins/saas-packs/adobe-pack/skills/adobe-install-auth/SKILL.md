---
name: adobe-install-auth
description: |
  Install and configure Adobe Developer Console OAuth Server-to-Server credentials.
  Use when setting up a new Adobe integration, configuring API credentials,
  or initializing Adobe SDKs (Firefly Services, PDF Services, I/O Runtime).
  Trigger with phrases like "install adobe", "setup adobe",
  "adobe auth", "configure adobe credentials", "adobe developer console".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, adobe]
compatible-with: claude-code
---

# Adobe Install & Auth

## Overview

Set up Adobe Developer Console OAuth Server-to-Server credentials and install the appropriate SDK for your use case. As of January 2025, JWT (Service Account) credentials are deprecated -- all new integrations must use OAuth Server-to-Server.

## Prerequisites

- Node.js 18+ or Python 3.10+
- Adobe Developer Console account (https://developer.adobe.com/console)
- An Adobe organization with API access entitlements
- Admin or Developer role in Adobe Admin Console

## Instructions

### Step 1: Create Project in Adobe Developer Console

1. Go to https://developer.adobe.com/console
2. Click **Create new project** > **Add API**
3. Select the API you need (e.g., Firefly Services, PDF Services, Creative Cloud Libraries)
4. Choose **OAuth Server-to-Server** credential type
5. Select the product profiles to scope access
6. Save your `client_id`, `client_secret`, and `scopes`

### Step 2: Install the SDK for Your Use Case

```bash
# Firefly Services (Photoshop API, Lightroom API, Firefly API)
npm install @adobe/firefly-apis @adobe/photoshop-apis @adobe/lightroom-apis

# PDF Services (create, extract, convert, generate documents)
npm install @adobe/pdfservices-node-sdk

# Adobe I/O Events (webhooks, event-driven)
npm install @adobe/aio-lib-events

# Adobe I/O SDK (App Builder, Runtime actions)
npm install @adobe/aio-sdk

# Adobe I/O CLI (global install for aio commands)
npm install -g @adobe/aio-cli

# Python — PDF Services
pip install pdfservices-sdk
```

### Step 3: Configure OAuth Server-to-Server Credentials

```bash
# .env (NEVER commit — add to .gitignore)
ADOBE_CLIENT_ID=your_client_id_from_console
ADOBE_CLIENT_SECRET=your_client_secret_from_console
ADOBE_SCOPES=openid,AdobeID,read_organizations,firefly_api,ff_apis
ADOBE_IMS_ORG_ID=your_org_id@AdobeOrg
```

### Step 4: Generate Access Token

```typescript
// src/adobe/auth.ts
import 'dotenv/config';

interface AdobeTokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number; // seconds, typically 86400 (24h)
}

let cachedToken: { token: string; expiresAt: number } | null = null;

export async function getAdobeAccessToken(): Promise<string> {
  // Return cached token if still valid (with 5min buffer)
  if (cachedToken && cachedToken.expiresAt > Date.now() + 300_000) {
    return cachedToken.token;
  }

  const response = await fetch('https://ims-na1.adobelogin.com/ims/token/v3', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      client_id: process.env.ADOBE_CLIENT_ID!,
      client_secret: process.env.ADOBE_CLIENT_SECRET!,
      grant_type: 'client_credentials',
      scope: process.env.ADOBE_SCOPES!,
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Adobe auth failed (${response.status}): ${error}`);
  }

  const data: AdobeTokenResponse = await response.json();
  cachedToken = {
    token: data.access_token,
    expiresAt: Date.now() + data.expires_in * 1000,
  };

  return cachedToken.token;
}
```

### Step 5: Verify Connection

```bash
# Quick verification with curl
curl -X POST 'https://ims-na1.adobelogin.com/ims/token/v3' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d "client_id=${ADOBE_CLIENT_ID}&client_secret=${ADOBE_CLIENT_SECRET}&grant_type=client_credentials&scope=${ADOBE_SCOPES}"
```

## Output

- OAuth Server-to-Server credential configured in Adobe Developer Console
- SDK packages installed in `node_modules` or Python site-packages
- `.env` file with credentials (git-ignored)
- Working `getAdobeAccessToken()` function with token caching

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `invalid_client` | Wrong client_id or client_secret | Verify credentials in Developer Console |
| `invalid_scope` | Scopes not entitled to your org | Check product profile assignments in Admin Console |
| `401 Unauthorized` | Expired or revoked credentials | Regenerate client_secret in Developer Console |
| `ENOTFOUND ims-na1.adobelogin.com` | Network/DNS issue | Check firewall allows outbound HTTPS to `*.adobelogin.com` |
| `JWT credentials deprecated` | Using old Service Account (JWT) | Migrate to OAuth Server-to-Server (JWT EOL was June 2025) |

## Examples

### PDF Services SDK Initialization

```typescript
import { ServicePrincipalCredentials, PDFServices } from '@adobe/pdfservices-node-sdk';

const credentials = new ServicePrincipalCredentials({
  clientId: process.env.ADOBE_CLIENT_ID!,
  clientSecret: process.env.ADOBE_CLIENT_SECRET!,
});

const pdfServices = new PDFServices({ credentials });
```

### Firefly Services SDK Initialization

```typescript
import { FireflyClient } from '@adobe/firefly-apis';

const firefly = new FireflyClient({
  clientId: process.env.ADOBE_CLIENT_ID!,
  accessToken: await getAdobeAccessToken(),
});
```

### Python PDF Services Setup

```python
from adobe.pdfservices.operation.auth.service_principal_credentials import ServicePrincipalCredentials
from adobe.pdfservices.operation.pdf_services import PDFServices

credentials = ServicePrincipalCredentials(
    client_id=os.environ["ADOBE_CLIENT_ID"],
    client_secret=os.environ["ADOBE_CLIENT_SECRET"]
)
pdf_services = PDFServices(credentials=credentials)
```

## Resources

- [Adobe Developer Console](https://developer.adobe.com/console)
- [OAuth Server-to-Server Implementation Guide](https://developer.adobe.com/developer-console/docs/guides/authentication/ServerToServerAuthentication/implementation)
- [JWT to OAuth Migration Guide](https://developer.adobe.com/developer-console/docs/guides/authentication/ServerToServerAuthentication/migration)
- [Adobe Status Page](https://status.adobe.com)

## Next Steps

After successful auth, proceed to `adobe-hello-world` for your first API call.
