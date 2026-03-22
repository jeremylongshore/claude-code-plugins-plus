---
name: navan-install-auth
description: |
  Install and configure Navan SDK/CLI authentication.
  Use when setting up a new Navan integration, configuring API keys,
  or initializing Navan in your project.
  Trigger with phrases like "install navan", "setup navan",
  "navan auth", "configure navan API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, navan]
---

# Navan Install & Auth

## Overview
Set up Navan SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Navan account with API access
- API key from Navan dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @navan/sdk

# Python
pip install navan
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export NAVAN_API_KEY="your-api-key"

# Or create .env file
echo 'NAVAN_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Navan dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.navan.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { NavanClient } from '@navan/sdk';

const client = new NavanClient({
  apiKey: process.env.NAVAN_API_KEY,
});
```

### Python Setup
```python
from navan import NavanClient

client = NavanClient(
    api_key=os.environ.get('NAVAN_API_KEY')
)
```

## Resources
- [Navan Documentation](https://docs.navan.com)
- [Navan Dashboard](https://api.navan.com)
- [Navan Status](https://status.navan.com)

## Next Steps
After successful auth, proceed to `navan-hello-world` for your first API call.