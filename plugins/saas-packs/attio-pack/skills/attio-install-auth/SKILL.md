---
name: attio-install-auth
description: |
  Install and configure Attio SDK/CLI authentication.
  Use when setting up a new Attio integration, configuring API keys,
  or initializing Attio in your project.
  Trigger with phrases like "install attio", "setup attio",
  "attio auth", "configure attio API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, attio]
---

# Attio Install & Auth

## Overview
Set up Attio SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Attio account with API access

- OAuth2 access token or personal API token from Attio settings


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @attio/sdk

# Python
pip install attio
```

### Step 2: Configure Authentication

```bash
# Set environment variable
export ATTIO_API_KEY="your-api-key"

# Or create .env file
echo 'ATTIO_API_KEY=your-api-key' >> .env
```


### Step 3: Verify Connection
```typescript
const me = await client.users.me();
console.log(`Authenticated: ${me.name} — ${me.organization.name}`);

```

## Output
- Installed SDK package in node_modules or site-packages

- Environment variable or .env file with API key
- Successful connection verification output


## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|

| Invalid API Key | Incorrect or expired key | Verify key in Attio dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.attio.com |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { AttioClient } from '@attio/sdk';

const client = new AttioClient({

  apiKey: process.env.ATTIO_API_KEY,

});
```

### Python Setup
```python
from attio import AttioClient

client = AttioClient(

    api_key=os.environ.get('ATTIO_API_KEY')

)
```

## Resources
- [Attio Documentation](https://docs.attio.com)
- [Attio Dashboard](https://api.attio.com)
- [Attio Status](https://status.attio.com)

## Next Steps
After successful auth, proceed to `attio-hello-world` for your first API call.