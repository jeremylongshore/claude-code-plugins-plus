---
name: salesforce-install-auth
description: |
  Install and configure Salesforce SDK/CLI authentication with jsforce or Salesforce CLI.
  Use when setting up a new Salesforce integration, configuring OAuth flows,
  or initializing Salesforce connectivity in your project.
  Trigger with phrases like "install salesforce", "setup salesforce",
  "salesforce auth", "configure salesforce", "jsforce setup", "sf cli login".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Bash(sf:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, salesforce]
compatible-with: claude-code
---

# Salesforce Install & Auth

## Overview
Set up Salesforce connectivity using jsforce (Node.js) or simple-salesforce (Python), and configure one of three OAuth 2.0 authentication flows.

## Prerequisites
- Node.js 18+ or Python 3.10+
- A Salesforce org (Developer Edition free at developer.salesforce.com)
- Connected App configured in Setup > App Manager > New Connected App
- OAuth scopes: `api`, `refresh_token`, `offline_access`

## Instructions

### Step 1: Install SDK

```bash
# Node.js — jsforce (most popular SF client, 3M+ weekly downloads)
npm install jsforce

# Python — simple-salesforce
pip install simple-salesforce

# Salesforce CLI (for metadata, deployment, scratch orgs)
npm install -g @salesforce/cli
```

### Step 2: Choose Authentication Flow

| Flow | Use Case | Requires Browser? |
|------|----------|-------------------|
| Username-Password | Dev/test scripts | No |
| JWT Bearer | CI/CD, server-to-server | No |
| Web Server (Authorization Code) | User-facing apps | Yes |

### Step 3: Configure Credentials

```bash
# .env (NEVER commit — add .env to .gitignore)
SF_LOGIN_URL=https://login.salesforce.com
SF_USERNAME=user@example.com
SF_PASSWORD=yourpassword
SF_SECURITY_TOKEN=yourtoken
SF_CLIENT_ID=your_connected_app_consumer_key
SF_CLIENT_SECRET=your_connected_app_consumer_secret

# For sandbox orgs, use:
# SF_LOGIN_URL=https://test.salesforce.com
```

### Step 4: Connect with Username-Password Flow

```typescript
import jsforce from 'jsforce';

const conn = new jsforce.Connection({
  loginUrl: process.env.SF_LOGIN_URL || 'https://login.salesforce.com',
});

await conn.login(
  process.env.SF_USERNAME!,
  process.env.SF_PASSWORD! + process.env.SF_SECURITY_TOKEN!
);

console.log('Connected to:', conn.instanceUrl);
console.log('User ID:', conn.userInfo?.id);
console.log('Org ID:', conn.userInfo?.organizationId);
```

### Step 5: Connect with JWT Bearer Flow (Production)

```typescript
import jsforce from 'jsforce';
import fs from 'fs';

const conn = new jsforce.Connection({
  loginUrl: process.env.SF_LOGIN_URL,
  // JWT requires a Connected App with a digital certificate
});

await conn.authorize({
  grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer',
  client_id: process.env.SF_CLIENT_ID!,
  username: process.env.SF_USERNAME!,
  privateKeyFile: './server.key', // RSA private key from your certificate
});
```

### Step 6: Connect with OAuth2 Web Server Flow

```typescript
import jsforce from 'jsforce';

const oauth2 = new jsforce.OAuth2({
  loginUrl: process.env.SF_LOGIN_URL,
  clientId: process.env.SF_CLIENT_ID!,
  clientSecret: process.env.SF_CLIENT_SECRET!,
  redirectUri: 'https://yourapp.com/oauth/callback',
});

// Step A: Redirect user to authorization URL
const authUrl = oauth2.getAuthorizationUrl({ scope: 'api refresh_token' });

// Step B: Handle callback — exchange code for tokens
const conn = new jsforce.Connection({ oauth2 });
await conn.authorize(authorizationCode);
// conn.accessToken and conn.refreshToken are now set
```

### Step 7: Verify Connection

```typescript
// Quick verification — query org info
const identity = await conn.identity();
console.log('Username:', identity.username);
console.log('Display Name:', identity.display_name);

// Check API version
const versions = await conn.request('/services/data/');
console.log('Latest API version:', versions[versions.length - 1].version);
```

### Python Setup (simple-salesforce)

```python
from simple_salesforce import Salesforce
import os

# Username-Password flow
sf = Salesforce(
    username=os.environ['SF_USERNAME'],
    password=os.environ['SF_PASSWORD'],
    security_token=os.environ['SF_SECURITY_TOKEN'],
    domain='test' if os.environ.get('SF_SANDBOX') else None  # 'test' for sandbox
)

# Verify connection
print(f"Connected to: {sf.sf_instance}")
result = sf.query("SELECT Id, Name FROM Organization")
print(f"Org: {result['records'][0]['Name']}")
```

## Output
- jsforce or simple-salesforce installed
- Authentication flow configured
- Environment variables set (never hardcoded)
- Connection verified with identity/org query

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `INVALID_LOGIN` | Wrong username/password/token | Verify credentials; reset security token in Setup > My Personal Information |
| `INVALID_CLIENT_ID` | Wrong Connected App consumer key | Check Setup > App Manager > your app |
| `INVALID_GRANT` | JWT cert mismatch or user not pre-authorized | Upload cert to Connected App; pre-authorize user profile |
| `LOGIN_MUST_USE_SECURITY_TOKEN` | Missing security token | Append token to password or whitelist your IP in Setup |
| `API_DISABLED_FOR_ORG` | API not enabled | Requires Enterprise, Unlimited, Developer, or Performance edition |
| `REQUEST_LIMIT_EXCEEDED` | Daily API limit hit | Check Setup > Company Information for remaining calls |

## Resources
- [jsforce Documentation](https://jsforce.github.io/document/)
- [simple-salesforce PyPI](https://pypi.org/project/simple-salesforce/)
- [Salesforce OAuth 2.0 Flows](https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_flows.htm)
- [Connected App Setup](https://help.salesforce.com/s/articleView?id=sf.connected_app_create.htm)
- [JWT Bearer Flow](https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_jwt_flow.htm)

## Next Steps
After successful auth, proceed to `salesforce-hello-world` for your first SOQL query.
