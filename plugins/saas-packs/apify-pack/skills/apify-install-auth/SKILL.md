---
name: apify-install-auth
description: |
  Install and configure Apify SDK/CLI authentication.
  Use when setting up a new Apify integration, configuring API keys,
  or initializing Apify in your project.
  Trigger with phrases like "install apify", "setup apify",
  "apify auth", "configure apify API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, apify]
---

# Apify Install & Auth

## Overview
Set up Apify SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Apify account with API access

- API key from Apify dashboard


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @apify/sdk

# Python
pip install apify
```

### Step 2: Configure Authentication

```bash
# Set environment variable
export APIFY_API_KEY="your-api-key"

# Or create .env file
echo 'APIFY_API_KEY=your-api-key' >> .env
```


### Step 3: Verify Connection
```typescript
const user = await client.user.get();
console.log(`Authenticated as ${user.name} (${user.email})`);

```

## Output
- Installed SDK package in node_modules or site-packages

- Environment variable or .env file with API key
- Successful connection verification output


## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|

| Invalid API Key | Incorrect or expired key | Verify key in Apify dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.apify.com |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { ApifyClient } from '@apify/sdk';

const client = new ApifyClient({

  apiKey: process.env.APIFY_API_KEY,

});
```

### Python Setup
```python
from apify import ApifyClient

client = ApifyClient(

    api_key=os.environ.get('APIFY_API_KEY')

)
```

## Resources
- [Apify Documentation](https://docs.apify.com)
- [Apify Dashboard](https://api.apify.com)
- [Apify Status](https://status.apify.com)

## Next Steps
After successful auth, proceed to `apify-hello-world` for your first API call.