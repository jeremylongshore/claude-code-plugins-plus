---
name: maintainx-install-auth
description: |
  Install and configure MaintainX SDK/CLI authentication.
  Use when setting up a new MaintainX integration, configuring API keys,
  or initializing MaintainX in your project.
  Trigger with phrases like "install maintainx", "setup maintainx",
  "maintainx auth", "configure maintainx API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, maintainx]
---

# MaintainX Install & Auth

## Overview
Set up MaintainX SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- MaintainX account with API access

- OAuth2 access token or personal API token from MaintainX settings


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @maintainx/sdk

# Python
pip install maintainx
```

### Step 2: Configure Authentication

```bash
# Set environment variable
export MAINTAINX_API_KEY="your-api-key"

# Or create .env file
echo 'MAINTAINX_API_KEY=your-api-key' >> .env
```


### Step 3: Verify Connection
```typescript
const org = await client.organization.get();
console.log(`Connected: ${org.name} (${org.plan} plan)`);

```

## Output
- Installed SDK package in node_modules or site-packages

- Environment variable or .env file with API key
- Successful connection verification output


## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|

| Invalid API Key | Incorrect or expired key | Verify key in MaintainX dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.maintainx.com |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { MaintainXClient } from '@maintainx/sdk';

const client = new MaintainXClient({

  apiKey: process.env.MAINTAINX_API_KEY,

});
```

### Python Setup
```python
from maintainx import MaintainXClient

client = MaintainXClient(

    api_key=os.environ.get('MAINTAINX_API_KEY')

)
```

## Resources
- [MaintainX Documentation](https://docs.maintainx.com)
- [MaintainX Dashboard](https://api.maintainx.com)
- [MaintainX Status](https://status.maintainx.com)

## Next Steps
After successful auth, proceed to `maintainx-hello-world` for your first API call.