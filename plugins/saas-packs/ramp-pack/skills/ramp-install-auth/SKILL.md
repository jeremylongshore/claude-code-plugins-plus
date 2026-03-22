---
name: ramp-install-auth
description: |
  Install and configure Ramp SDK/CLI authentication.
  Use when setting up a new Ramp integration, configuring API keys,
  or initializing Ramp in your project.
  Trigger with phrases like "install ramp", "setup ramp",
  "ramp auth", "configure ramp API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, ramp]
---

# Ramp Install & Auth

## Overview
Set up Ramp SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Ramp account with API access

- API key from Ramp dashboard


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @ramp/sdk

# Python
pip install ramp
```

### Step 2: Configure Authentication

```bash
# Set environment variable
export RAMP_API_KEY="your-api-key"

# Or create .env file
echo 'RAMP_API_KEY=your-api-key' >> .env
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

| Invalid API Key | Incorrect or expired key | Verify key in Ramp dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.ramp.com |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { RampClient } from '@ramp/sdk';

const client = new RampClient({

  apiKey: process.env.RAMP_API_KEY,

});
```

### Python Setup
```python
from ramp import RampClient

client = RampClient(

    api_key=os.environ.get('RAMP_API_KEY')

)
```

## Resources
- [Ramp Documentation](https://docs.ramp.com)
- [Ramp Dashboard](https://api.ramp.com)
- [Ramp Status](https://status.ramp.com)

## Next Steps
After successful auth, proceed to `ramp-hello-world` for your first API call.