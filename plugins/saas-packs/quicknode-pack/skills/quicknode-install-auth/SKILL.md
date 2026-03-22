---
name: quicknode-install-auth
description: |
  Install and configure QuickNode SDK/CLI authentication.
  Use when setting up a new QuickNode integration, configuring API keys,
  or initializing QuickNode in your project.
  Trigger with phrases like "install quicknode", "setup quicknode",
  "quicknode auth", "configure quicknode API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, quicknode]
---

# QuickNode Install & Auth

## Overview
Set up QuickNode SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- QuickNode account with API access

- API key from QuickNode dashboard


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @quicknode/sdk

# Python
pip install quicknode
```

### Step 2: Configure Authentication

```bash
# Set environment variable
export QUICKNODE_API_KEY="your-api-key"

# Or create .env file
echo 'QUICKNODE_API_KEY=your-api-key' >> .env
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

| Invalid API Key | Incorrect or expired key | Verify key in QuickNode dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.quicknode.com |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { QuickNodeClient } from '@quicknode/sdk';

const client = new QuickNodeClient({

  apiKey: process.env.QUICKNODE_API_KEY,

});
```

### Python Setup
```python
from quicknode import QuickNodeClient

client = QuickNodeClient(

    api_key=os.environ.get('QUICKNODE_API_KEY')

)
```

## Resources
- [QuickNode Documentation](https://docs.quicknode.com)
- [QuickNode Dashboard](https://api.quicknode.com)
- [QuickNode Status](https://status.quicknode.com)

## Next Steps
After successful auth, proceed to `quicknode-hello-world` for your first API call.