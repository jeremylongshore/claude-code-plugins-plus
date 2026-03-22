---
name: serpapi-install-auth
description: |
  Install and configure SerpApi SDK/CLI authentication.
  Use when setting up a new SerpApi integration, configuring API keys,
  or initializing SerpApi in your project.
  Trigger with phrases like "install serpapi", "setup serpapi",
  "serpapi auth", "configure serpapi API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, serpapi]
---

# SerpApi Install & Auth

## Overview
Set up SerpApi SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- SerpApi account with API access

- API key from SerpApi dashboard


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @serpapi/sdk

# Python
pip install serpapi
```

### Step 2: Configure Authentication

```bash
# Set environment variable
export SERPAPI_API_KEY="your-api-key"

# Or create .env file
echo 'SERPAPI_API_KEY=your-api-key' >> .env
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

| Invalid API Key | Incorrect or expired key | Verify key in SerpApi dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.serpapi.com |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { SerpApiClient } from '@serpapi/sdk';

const client = new SerpApiClient({

  apiKey: process.env.SERPAPI_API_KEY,

});
```

### Python Setup
```python
from serpapi import SerpApiClient

client = SerpApiClient(

    api_key=os.environ.get('SERPAPI_API_KEY')

)
```

## Resources
- [SerpApi Documentation](https://docs.serpapi.com)
- [SerpApi Dashboard](https://api.serpapi.com)
- [SerpApi Status](https://status.serpapi.com)

## Next Steps
After successful auth, proceed to `serpapi-hello-world` for your first API call.