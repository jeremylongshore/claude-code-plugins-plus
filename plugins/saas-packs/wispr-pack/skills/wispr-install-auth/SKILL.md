---
name: wispr-install-auth
description: |
  Install and configure Wispr SDK/CLI authentication.
  Use when setting up a new Wispr integration, configuring API keys,
  or initializing Wispr in your project.
  Trigger with phrases like "install wispr", "setup wispr",
  "wispr auth", "configure wispr API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, wispr]
---

# Wispr Install & Auth

## Overview
Set up Wispr SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Wispr account with API access

- API key from Wispr dashboard (starts with `sk-` or similar prefix)


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @wispr/sdk

# Python
pip install wispr
```

### Step 2: Configure Authentication

```bash
# Set environment variable
export WISPR_API_KEY="your-api-key"

# Or create .env file
echo 'WISPR_API_KEY=your-api-key' >> .env
```


### Step 3: Verify Connection
```typescript
const models = await client.models.list();
console.log(`Connected — ${models.data.length} models available`);

```

## Output
- Installed SDK package in node_modules or site-packages

- Environment variable or .env file with API key
- Successful connection verification output


## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|

| Invalid API Key | Key is missing, expired, or has extra whitespace | Verify key in Wispr dashboard. Check for trailing newlines |
| Rate Limited | Exceeded requests/tokens per minute | Check usage at https://docs.wispr.com/usage |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { WisprClient } from '@wispr/sdk';

const client = new WisprClient({

  apiKey: process.env.WISPR_API_KEY,

});
```

### Python Setup
```python
from wispr import WisprClient

client = WisprClient(

    api_key=os.environ.get('WISPR_API_KEY')

)
```

## Resources
- [Wispr Documentation](https://docs.wispr.com)
- [Wispr Dashboard](https://api.wispr.com)
- [Wispr Status](https://status.wispr.com)

## Next Steps
After successful auth, proceed to `wispr-hello-world` for your first API call.