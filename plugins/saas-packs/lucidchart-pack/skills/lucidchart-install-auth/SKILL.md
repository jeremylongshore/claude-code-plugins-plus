---
name: lucidchart-install-auth
description: |
  Install and configure Lucidchart SDK/CLI authentication.
  Use when setting up a new Lucidchart integration, configuring API keys,
  or initializing Lucidchart in your project.
  Trigger with phrases like "install lucidchart", "setup lucidchart",
  "lucidchart auth", "configure lucidchart API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, lucidchart]
---

# Lucidchart Install & Auth

## Overview
Set up Lucidchart SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Lucidchart account with API access

- OAuth2 access token or personal API token from Lucidchart settings


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @lucidchart/sdk

# Python
pip install lucidchart
```

### Step 2: Configure Authentication

```bash
# OAuth2: Set access token (get from OAuth flow or personal tokens page)
export LUCIDCHART_ACCESS_TOKEN="your-access-token"

# Or create .env file
echo 'LUCIDCHART_ACCESS_TOKEN=your-access-token' >> .env
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
import { LucidchartClient } from '@lucidchart/sdk';

const client = new LucidchartClient({

  accessToken: process.env.LUCIDCHART_ACCESS_TOKEN,

});
```

### Python Setup
```python
from lucidchart import LucidchartClient

client = LucidchartClient(

    access_token=os.environ.get('LUCIDCHART_ACCESS_TOKEN')

)
```

## Resources
- [Lucidchart Documentation](https://docs.lucidchart.com)
- [Lucidchart Dashboard](https://api.lucidchart.com)
- [Lucidchart Status](https://status.lucidchart.com)

## Next Steps
After successful auth, proceed to `lucidchart-hello-world` for your first API call.