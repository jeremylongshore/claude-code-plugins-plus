---
name: abridge-install-auth
description: |
  Install and configure Abridge SDK/CLI authentication.
  Use when setting up a new Abridge integration, configuring API keys,
  or initializing Abridge in your project.
  Trigger with phrases like "install abridge", "setup abridge",
  "abridge auth", "configure abridge API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, abridge]
---

# Abridge Install & Auth

## Overview
Set up Abridge SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Abridge account with API access

- API key from Abridge dashboard (starts with `sk-` or similar prefix)


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @abridge/sdk

# Python
pip install abridge
```

### Step 2: Configure Authentication

```bash
# Set environment variable
export ABRIDGE_API_KEY="your-api-key"

# Or create .env file
echo 'ABRIDGE_API_KEY=your-api-key' >> .env
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

| Invalid API Key | Key is missing, expired, or has extra whitespace | Verify key in Abridge dashboard. Check for trailing newlines |
| Rate Limited | Exceeded requests/tokens per minute | Check usage at https://docs.abridge.com/usage |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { AbridgeClient } from '@abridge/sdk';

const client = new AbridgeClient({

  apiKey: process.env.ABRIDGE_API_KEY,

});
```

### Python Setup
```python
from abridge import AbridgeClient

client = AbridgeClient(

    api_key=os.environ.get('ABRIDGE_API_KEY')

)
```

## Resources
- [Abridge Documentation](https://docs.abridge.com)
- [Abridge Dashboard](https://api.abridge.com)
- [Abridge Status](https://status.abridge.com)

## Next Steps
After successful auth, proceed to `abridge-hello-world` for your first API call.