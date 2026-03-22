---
name: lindy-install-auth
description: |
  Install and configure Lindy SDK/CLI authentication.
  Use when setting up a new Lindy integration, configuring API keys,
  or initializing Lindy in your project.
  Trigger with phrases like "install lindy", "setup lindy",
  "lindy auth", "configure lindy API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, lindy]
---

# Lindy Install & Auth

## Overview
Set up Lindy SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Lindy account with API access
- API key from Lindy dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @lindy/sdk

# Python
pip install lindy
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export LINDY_API_KEY="your-api-key"

# Or create .env file
echo 'LINDY_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Lindy dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.lindy.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { LindyClient } from '@lindy/sdk';

const client = new LindyClient({
  apiKey: process.env.LINDY_API_KEY,
});
```

### Python Setup
```python
from lindy import LindyClient

client = LindyClient(
    api_key=os.environ.get('LINDY_API_KEY')
)
```

## Resources
- [Lindy Documentation](https://docs.lindy.com)
- [Lindy Dashboard](https://api.lindy.com)
- [Lindy Status](https://status.lindy.com)

## Next Steps
After successful auth, proceed to `lindy-hello-world` for your first API call.