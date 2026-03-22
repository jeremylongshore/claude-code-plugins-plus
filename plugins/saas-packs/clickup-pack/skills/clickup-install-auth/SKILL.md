---
name: clickup-install-auth
description: |
  Install and configure ClickUp SDK/CLI authentication.
  Use when setting up a new ClickUp integration, configuring API keys,
  or initializing ClickUp in your project.
  Trigger with phrases like "install clickup", "setup clickup",
  "clickup auth", "configure clickup API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, clickup]
---

# ClickUp Install & Auth

## Overview
Set up ClickUp SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- ClickUp account with API access

- API key from ClickUp dashboard


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @clickup/sdk

# Python
pip install clickup
```

### Step 2: Configure Authentication

```bash
# Set environment variable
export CLICKUP_API_KEY="your-api-key"

# Or create .env file
echo 'CLICKUP_API_KEY=your-api-key' >> .env
```


### Step 3: Verify Connection
```typescript
const workspace = await client.workspace.get();
console.log(`Connected to workspace: ${workspace.name}`);

```

## Output
- Installed SDK package in node_modules or site-packages

- Environment variable or .env file with API key
- Successful connection verification output


## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|

| Invalid API Key | Incorrect or expired key | Verify key in ClickUp dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.clickup.com |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { ClickUpClient } from '@clickup/sdk';

const client = new ClickUpClient({

  apiKey: process.env.CLICKUP_API_KEY,

});
```

### Python Setup
```python
from clickup import ClickUpClient

client = ClickUpClient(

    api_key=os.environ.get('CLICKUP_API_KEY')

)
```

## Resources
- [ClickUp Documentation](https://docs.clickup.com)
- [ClickUp Dashboard](https://api.clickup.com)
- [ClickUp Status](https://status.clickup.com)

## Next Steps
After successful auth, proceed to `clickup-hello-world` for your first API call.