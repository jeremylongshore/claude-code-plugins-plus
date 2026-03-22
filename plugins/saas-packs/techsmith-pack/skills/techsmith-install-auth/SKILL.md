---
name: techsmith-install-auth
description: |
  Install and configure TechSmith SDK/CLI authentication.
  Use when setting up a new TechSmith integration, configuring API keys,
  or initializing TechSmith in your project.
  Trigger with phrases like "install techsmith", "setup techsmith",
  "techsmith auth", "configure techsmith API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, techsmith]
---

# TechSmith Install & Auth

## Overview
Set up TechSmith SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- TechSmith account with API access

- OAuth2 access token or personal API token from TechSmith settings


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @techsmith/sdk

# Python
pip install techsmith
```

### Step 2: Configure Authentication

```bash
# OAuth2: Set access token (get from OAuth flow or personal tokens page)
export TECHSMITH_ACCESS_TOKEN="your-access-token"

# Or create .env file
echo 'TECHSMITH_ACCESS_TOKEN=your-access-token' >> .env
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
import { TechSmithClient } from '@techsmith/sdk';

const client = new TechSmithClient({

  accessToken: process.env.TECHSMITH_ACCESS_TOKEN,

});
```

### Python Setup
```python
from techsmith import TechSmithClient

client = TechSmithClient(

    access_token=os.environ.get('TECHSMITH_ACCESS_TOKEN')

)
```

## Resources
- [TechSmith Documentation](https://docs.techsmith.com)
- [TechSmith Dashboard](https://api.techsmith.com)
- [TechSmith Status](https://status.techsmith.com)

## Next Steps
After successful auth, proceed to `techsmith-hello-world` for your first API call.