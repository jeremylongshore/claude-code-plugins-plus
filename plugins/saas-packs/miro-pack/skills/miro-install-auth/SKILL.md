---
name: miro-install-auth
description: |
  Install and configure Miro SDK/CLI authentication.
  Use when setting up a new Miro integration, configuring API keys,
  or initializing Miro in your project.
  Trigger with phrases like "install miro", "setup miro",
  "miro auth", "configure miro API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, miro]
---

# Miro Install & Auth

## Overview
Set up Miro SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Miro account with API access

- OAuth2 access token or personal API token from Miro settings


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @miro/sdk

# Python
pip install miro
```

### Step 2: Configure Authentication

```bash
# OAuth2: Set access token (get from OAuth flow or personal tokens page)
export MIRO_ACCESS_TOKEN="your-access-token"

# Or create .env file
echo 'MIRO_ACCESS_TOKEN=your-access-token' >> .env
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
import { MiroClient } from '@miro/sdk';

const client = new MiroClient({

  accessToken: process.env.MIRO_ACCESS_TOKEN,

});
```

### Python Setup
```python
from miro import MiroClient

client = MiroClient(

    access_token=os.environ.get('MIRO_ACCESS_TOKEN')

)
```

## Resources
- [Miro Documentation](https://docs.miro.com)
- [Miro Dashboard](https://api.miro.com)
- [Miro Status](https://status.miro.com)

## Next Steps
After successful auth, proceed to `miro-hello-world` for your first API call.