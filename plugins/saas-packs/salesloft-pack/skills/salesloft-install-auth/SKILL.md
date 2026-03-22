---
name: salesloft-install-auth
description: |
  Install and configure Salesloft SDK/CLI authentication.
  Use when setting up a new Salesloft integration, configuring API keys,
  or initializing Salesloft in your project.
  Trigger with phrases like "install salesloft", "setup salesloft",
  "salesloft auth", "configure salesloft API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, salesloft]
---

# Salesloft Install & Auth

## Overview
Set up Salesloft SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Salesloft account with API access
- API key from Salesloft dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @salesloft/sdk

# Python
pip install salesloft
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export SALESLOFT_API_KEY="your-api-key"

# Or create .env file
echo 'SALESLOFT_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Salesloft dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.salesloft.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { SalesloftClient } from '@salesloft/sdk';

const client = new SalesloftClient({
  apiKey: process.env.SALESLOFT_API_KEY,
});
```

### Python Setup
```python
from salesloft import SalesloftClient

client = SalesloftClient(
    api_key=os.environ.get('SALESLOFT_API_KEY')
)
```

## Resources
- [Salesloft Documentation](https://docs.salesloft.com)
- [Salesloft Dashboard](https://api.salesloft.com)
- [Salesloft Status](https://status.salesloft.com)

## Next Steps
After successful auth, proceed to `salesloft-hello-world` for your first API call.