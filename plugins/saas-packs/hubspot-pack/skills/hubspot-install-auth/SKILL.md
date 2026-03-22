---
name: hubspot-install-auth
description: |
  Install and configure HubSpot API client with authentication.
  Use when setting up a new HubSpot integration, configuring private app tokens,
  OAuth 2.0 flows, or initializing the @hubspot/api-client SDK.
  Trigger with phrases like "install hubspot", "setup hubspot auth",
  "hubspot access token", "configure hubspot API", "hubspot private app".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, marketing, hubspot]
compatible-with: claude-code
---

# HubSpot Install & Auth

## Overview

Set up the `@hubspot/api-client` SDK and configure authentication using private app access tokens or OAuth 2.0.

## Prerequisites

- Node.js 18+ or Python 3.10+
- HubSpot account (free or paid)
- Private app created in Settings > Integrations > Private Apps
- Required scopes selected for your private app

## Instructions

### Step 1: Install the SDK

```bash
# Node.js (official SDK)
npm install @hubspot/api-client

# Python
pip install hubspot-api-client
```

### Step 2: Create a Private App in HubSpot

1. Go to Settings > Integrations > Private Apps
2. Click "Create a private app"
3. Name your app and select scopes:
   - `crm.objects.contacts.read` / `crm.objects.contacts.write`
   - `crm.objects.companies.read` / `crm.objects.companies.write`
   - `crm.objects.deals.read` / `crm.objects.deals.write`
   - `crm.objects.custom.read` / `crm.objects.custom.write`
   - `crm.schemas.contacts.read` (for properties)
4. Copy the generated access token

### Step 3: Configure Environment

```bash
# .env file (add to .gitignore)
HUBSPOT_ACCESS_TOKEN=pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# .gitignore
echo '.env' >> .gitignore
echo '.env.local' >> .gitignore
```

### Step 4: Initialize and Verify

```typescript
import * as hubspot from '@hubspot/api-client';

const hubspotClient = new hubspot.Client({
  accessToken: process.env.HUBSPOT_ACCESS_TOKEN,
});

// Verify connection by fetching account info
async function verifyConnection() {
  try {
    const response = await hubspotClient.crm.contacts.basicApi.getPage(
      1, // limit
      undefined, // after
      ['firstname', 'lastname', 'email']
    );
    console.log(`Connected. Found ${response.results.length} contact(s).`);
    return true;
  } catch (error) {
    if (error.code === 401) {
      console.error('Invalid access token. Check HUBSPOT_ACCESS_TOKEN.');
    } else if (error.code === 403) {
      console.error('Missing scopes. Add crm.objects.contacts.read to your private app.');
    } else {
      console.error('Connection failed:', error.message);
    }
    return false;
  }
}
```

### Step 5: OAuth 2.0 Setup (Public Apps)

```typescript
// For public apps distributed to multiple HubSpot portals
const hubspotClient = new hubspot.Client();

// Step 1: Generate authorization URL
const authUrl = hubspotClient.oauth.getAuthorizationUrl(
  'your-client-id',
  'http://localhost:3000/oauth/callback',
  'crm.objects.contacts.read crm.objects.contacts.write'
);
// Redirect user to authUrl

// Step 2: Exchange code for tokens (in callback handler)
const tokenResponse = await hubspotClient.oauth.tokensApi.create(
  'authorization_code',
  code,           // from query param
  redirectUri,
  clientId,
  clientSecret
);

// Step 3: Initialize client with OAuth token
const authedClient = new hubspot.Client({
  accessToken: tokenResponse.accessToken,
});

// Step 4: Refresh tokens before expiry (tokens expire in 30 minutes)
const refreshResponse = await hubspotClient.oauth.tokensApi.create(
  'refresh_token',
  undefined,
  undefined,
  clientId,
  clientSecret,
  refreshToken
);
```

## Output

- `@hubspot/api-client` installed in node_modules
- `.env` file with `HUBSPOT_ACCESS_TOKEN`
- Verified API connection with a test call
- OAuth flow configured (if building a public app)

## Error Handling

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| `401 Unauthorized` | 401 | Invalid or expired token | Regenerate token in Private Apps settings |
| `403 Forbidden` | 403 | Missing required scopes | Add scopes and generate new token |
| `429 Too Many Requests` | 429 | Rate limit exceeded | Implement backoff (see `hubspot-rate-limits`) |
| `MODULE_NOT_FOUND` | -- | Package not installed | Run `npm install @hubspot/api-client` |
| `ECONNREFUSED` | -- | Network blocked | Ensure outbound HTTPS to `api.hubapi.com` |

## Examples

### Python Setup

```python
from hubspot import HubSpot

client = HubSpot(access_token=os.environ.get('HUBSPOT_ACCESS_TOKEN'))

# Verify connection
try:
    contacts = client.crm.contacts.basic_api.get_page(limit=1)
    print(f"Connected. Found {len(contacts.results)} contact(s).")
except Exception as e:
    print(f"Connection failed: {e}")
```

### TypeScript with Strict Typing

```typescript
import * as hubspot from '@hubspot/api-client';
import type {
  SimplePublicObjectWithAssociations
} from '@hubspot/api-client/lib/codegen/crm/contacts';

const client = new hubspot.Client({
  accessToken: process.env.HUBSPOT_ACCESS_TOKEN!,
  numberOfApiCallRetries: 3, // built-in retry support
});
```

## Resources

- [HubSpot Private Apps Guide](https://developers.hubspot.com/docs/guides/apps/private-apps/overview)
- [OAuth 2.0 Guide](https://developers.hubspot.com/docs/guides/apps/authentication/oauth)
- [@hubspot/api-client on npm](https://www.npmjs.com/package/@hubspot/api-client)
- [HubSpot API Scopes Reference](https://developers.hubspot.com/docs/guides/apps/authentication/scopes)

## Next Steps

After successful auth, proceed to `hubspot-hello-world` for your first CRM operations.
