---
name: veeva-install-auth
description: |
  Install and configure Veeva SDK/CLI authentication.
  Use when setting up a new Veeva integration, configuring API keys,
  or initializing Veeva in your project.
  Trigger with phrases like "install veeva", "setup veeva",
  "veeva auth", "configure veeva API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, veeva]
---

# Veeva Install & Auth

## Overview
Set up Veeva SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Veeva account with API access
- API key from Veeva dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @veeva/sdk

# Python
pip install veeva
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export VEEVA_API_KEY="your-api-key"

# Or create .env file
echo 'VEEVA_API_KEY=your-api-key' >> .env
```

### Step 3: Verify Connection
```typescript
// Test connection code here
```

## Output
- Installed SDK package in node_modules or site-packages
- Environment variable or .env file with API key
- Successful connection verification output

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Invalid API Key | Incorrect or expired key | Verify key in Veeva dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.veeva.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { VeevaClient } from '@veeva/sdk';

const client = new VeevaClient({
  apiKey: process.env.VEEVA_API_KEY,
});
```

### Python Setup
```python
from veeva import VeevaClient

client = VeevaClient(
    api_key=os.environ.get('VEEVA_API_KEY')
)
```

## Resources
- [Veeva Documentation](https://docs.veeva.com)
- [Veeva Dashboard](https://api.veeva.com)
- [Veeva Status](https://status.veeva.com)

## Next Steps
After successful auth, proceed to `veeva-hello-world` for your first API call.