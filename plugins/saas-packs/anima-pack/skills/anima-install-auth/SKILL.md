---
name: anima-install-auth
description: |
  Install and configure Anima SDK/CLI authentication.
  Use when setting up a new Anima integration, configuring API keys,
  or initializing Anima in your project.
  Trigger with phrases like "install anima", "setup anima",
  "anima auth", "configure anima API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, anima]
---

# Anima Install & Auth

## Overview
Set up Anima SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Anima account with API access
- API key from Anima dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @anima/sdk

# Python
pip install anima
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export ANIMA_API_KEY="your-api-key"

# Or create .env file
echo 'ANIMA_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Anima dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.anima.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { AnimaClient } from '@anima/sdk';

const client = new AnimaClient({
  apiKey: process.env.ANIMA_API_KEY,
});
```

### Python Setup
```python
from anima import AnimaClient

client = AnimaClient(
    api_key=os.environ.get('ANIMA_API_KEY')
)
```

## Resources
- [Anima Documentation](https://docs.anima.com)
- [Anima Dashboard](https://api.anima.com)
- [Anima Status](https://status.anima.com)

## Next Steps
After successful auth, proceed to `anima-hello-world` for your first API call.