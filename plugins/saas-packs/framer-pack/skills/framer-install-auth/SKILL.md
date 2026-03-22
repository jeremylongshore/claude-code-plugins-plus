---
name: framer-install-auth
description: |
  Install and configure Framer SDK/CLI authentication.
  Use when setting up a new Framer integration, configuring API keys,
  or initializing Framer in your project.
  Trigger with phrases like "install framer", "setup framer",
  "framer auth", "configure framer API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, framer]
---

# Framer Install & Auth

## Overview
Set up Framer SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Framer account with API access

- OAuth2 access token or personal API token from Framer settings


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @framer/sdk

# Python
pip install framer
```

### Step 2: Configure Authentication

```bash
# OAuth2: Set access token (get from OAuth flow or personal tokens page)
export FRAMER_ACCESS_TOKEN="your-access-token"

# Or create .env file
echo 'FRAMER_ACCESS_TOKEN=your-access-token' >> .env
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
import { FramerClient } from '@framer/sdk';

const client = new FramerClient({

  accessToken: process.env.FRAMER_ACCESS_TOKEN,

});
```

### Python Setup
```python
from framer import FramerClient

client = FramerClient(

    access_token=os.environ.get('FRAMER_ACCESS_TOKEN')

)
```

## Resources
- [Framer Documentation](https://docs.framer.com)
- [Framer Dashboard](https://api.framer.com)
- [Framer Status](https://status.framer.com)

## Next Steps
After successful auth, proceed to `framer-hello-world` for your first API call.