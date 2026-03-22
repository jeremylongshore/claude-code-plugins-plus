---
name: fondo-install-auth
description: |
  Install and configure Fondo SDK/CLI authentication.
  Use when setting up a new Fondo integration, configuring API keys,
  or initializing Fondo in your project.
  Trigger with phrases like "install fondo", "setup fondo",
  "fondo auth", "configure fondo API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, fondo]
---

# Fondo Install & Auth

## Overview
Set up Fondo SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Fondo account with API access

- API key from Fondo dashboard


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @fondo/sdk

# Python
pip install fondo
```

### Step 2: Configure Authentication

```bash
# Set environment variable
export FONDO_API_KEY="your-api-key"

# Or create .env file
echo 'FONDO_API_KEY=your-api-key' >> .env
```


### Step 3: Verify Connection
```typescript
const status = await client.health.check();
console.log(`API status: ${status.operational ? 'OK' : 'Degraded'}`);

```

## Output
- Installed SDK package in node_modules or site-packages

- Environment variable or .env file with API key
- Successful connection verification output


## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|

| Invalid API Key | Incorrect or expired key | Verify key in Fondo dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.fondo.com |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { FondoClient } from '@fondo/sdk';

const client = new FondoClient({

  apiKey: process.env.FONDO_API_KEY,

});
```

### Python Setup
```python
from fondo import FondoClient

client = FondoClient(

    api_key=os.environ.get('FONDO_API_KEY')

)
```

## Resources
- [Fondo Documentation](https://docs.fondo.com)
- [Fondo Dashboard](https://api.fondo.com)
- [Fondo Status](https://status.fondo.com)

## Next Steps
After successful auth, proceed to `fondo-hello-world` for your first API call.