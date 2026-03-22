---
name: anima-install-auth
description: |
  Install and configure Anima SDK/CLI authentication.
  Use when setting up a new Anima integration, configuring API keys,
  or initializing Anima in your project.
  Trigger with phrases like "install anima", "setup anima",
  "anima auth", "configure anima API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, anima]
---

# Anima Install & Auth

## Overview
Set up Anima SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Anima account with API access

- OAuth2 access token or personal API token from Anima settings


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @anima/sdk

# Python
pip install anima
```

### Step 2: Configure Authentication

```bash
# OAuth2: Set access token (get from OAuth flow or personal tokens page)
export ANIMA_ACCESS_TOKEN="your-access-token"

# Or create .env file
echo 'ANIMA_ACCESS_TOKEN=your-access-token' >> .env
```

> **Note:** OAuth tokens expire. For production, implement the refresh token flow.
> Personal access tokens (if available) are simpler for development.


### Step 3: Verify Connection
```typescript
const me = await client.users.me();
console.log(`Authenticated as ${me.name} — ${me.email}`);

```

## Output
- Installed SDK package in node_modules or site-packages

- OAuth access token configured in environment
- Successful API call confirming file/project access


## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|

| Token Expired | OAuth access token past lifetime | Refresh token or generate new personal access token |
| Insufficient Scope | Token missing required permissions | Re-authorize with correct OAuth scopes |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { AnimaClient } from '@anima/sdk';

const client = new AnimaClient({

  accessToken: process.env.ANIMA_ACCESS_TOKEN,

});
```

### Python Setup
```python
from anima import AnimaClient

client = AnimaClient(

    access_token=os.environ.get('ANIMA_ACCESS_TOKEN')

)
```

## Resources
- [Anima Documentation](https://docs.anima.com)
- [Anima Dashboard](https://api.anima.com)
- [Anima Status](https://status.anima.com)

## Next Steps
After successful auth, proceed to `anima-hello-world` for your first API call.