---
name: alchemy-install-auth
description: |
  Install and configure Alchemy SDK/CLI authentication.
  Use when setting up a new Alchemy integration, configuring API keys,
  or initializing Alchemy in your project.
  Trigger with phrases like "install alchemy", "setup alchemy",
  "alchemy auth", "configure alchemy API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, alchemy]
---

# Alchemy Install & Auth

## Overview
Set up Alchemy SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Alchemy account with API access

- API key from Alchemy dashboard


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @alchemy/sdk

# Python
pip install alchemy
```

### Step 2: Configure Authentication

```bash
# Set environment variable
export ALCHEMY_API_KEY="your-api-key"

# Or create .env file
echo 'ALCHEMY_API_KEY=your-api-key' >> .env
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

| Invalid API Key | Incorrect or expired key | Verify key in Alchemy dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.alchemy.com |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { AlchemyClient } from '@alchemy/sdk';

const client = new AlchemyClient({

  apiKey: process.env.ALCHEMY_API_KEY,

});
```

### Python Setup
```python
from alchemy import AlchemyClient

client = AlchemyClient(

    api_key=os.environ.get('ALCHEMY_API_KEY')

)
```

## Resources
- [Alchemy Documentation](https://docs.alchemy.com)
- [Alchemy Dashboard](https://api.alchemy.com)
- [Alchemy Status](https://status.alchemy.com)

## Next Steps
After successful auth, proceed to `alchemy-hello-world` for your first API call.