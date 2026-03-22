---
name: juicebox-install-auth
description: |
  Install and configure Juicebox SDK/CLI authentication.
  Use when setting up a new Juicebox integration, configuring API keys,
  or initializing Juicebox in your project.
  Trigger with phrases like "install juicebox", "setup juicebox",
  "juicebox auth", "configure juicebox API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, juicebox]
---

# Juicebox Install & Auth

## Overview
Set up Juicebox SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Juicebox account with API access

- OAuth2 access token or personal API token from Juicebox settings


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @juicebox/sdk

# Python
pip install juicebox
```

### Step 2: Configure Authentication

```bash
# Set environment variable
export JUICEBOX_API_KEY="your-api-key"

# Or create .env file
echo 'JUICEBOX_API_KEY=your-api-key' >> .env
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

| Invalid API Key | Incorrect or expired key | Verify key in Juicebox dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.juicebox.com |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { JuiceboxClient } from '@juicebox/sdk';

const client = new JuiceboxClient({

  apiKey: process.env.JUICEBOX_API_KEY,

});
```

### Python Setup
```python
from juicebox import JuiceboxClient

client = JuiceboxClient(

    api_key=os.environ.get('JUICEBOX_API_KEY')

)
```

## Resources
- [Juicebox Documentation](https://docs.juicebox.com)
- [Juicebox Dashboard](https://api.juicebox.com)
- [Juicebox Status](https://status.juicebox.com)

## Next Steps
After successful auth, proceed to `juicebox-hello-world` for your first API call.