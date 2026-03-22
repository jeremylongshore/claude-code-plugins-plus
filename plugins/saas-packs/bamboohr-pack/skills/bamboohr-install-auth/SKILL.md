---
name: bamboohr-install-auth
description: |
  Install and configure BambooHR SDK/CLI authentication.
  Use when setting up a new BambooHR integration, configuring API keys,
  or initializing BambooHR in your project.
  Trigger with phrases like "install bamboohr", "setup bamboohr",
  "bamboohr auth", "configure bamboohr API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, bamboohr]
---

# BambooHR Install & Auth

## Overview
Set up BambooHR SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- BambooHR account with API access

- OAuth2 access token or personal API token from BambooHR settings


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @bamboohr/sdk

# Python
pip install bamboohr
```

### Step 2: Configure Authentication

```bash
# Set environment variable
export BAMBOOHR_API_KEY="your-api-key"

# Or create .env file
echo 'BAMBOOHR_API_KEY=your-api-key' >> .env
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

| Invalid API Key | Incorrect or expired key | Verify key in BambooHR dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.bamboohr.com |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { BambooHRClient } from '@bamboohr/sdk';

const client = new BambooHRClient({

  apiKey: process.env.BAMBOOHR_API_KEY,

});
```

### Python Setup
```python
from bamboohr import BambooHRClient

client = BambooHRClient(

    api_key=os.environ.get('BAMBOOHR_API_KEY')

)
```

## Resources
- [BambooHR Documentation](https://docs.bamboohr.com)
- [BambooHR Dashboard](https://api.bamboohr.com)
- [BambooHR Status](https://status.bamboohr.com)

## Next Steps
After successful auth, proceed to `bamboohr-hello-world` for your first API call.