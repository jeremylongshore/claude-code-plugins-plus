---
name: vercel-install-auth
description: |
  Install and configure Vercel SDK/CLI authentication.
  Use when setting up a new Vercel integration, configuring API keys,
  or initializing Vercel in your project.
  Trigger with phrases like "install vercel", "setup vercel",
  "vercel auth", "configure vercel API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Vercel Install & Auth

## Overview
Set up Vercel SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Vercel account with API access
- API key from Vercel dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install vercel

# Python
pip install None
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export VERCEL_API_KEY="your-api-key"

# Or create .env file
echo 'VERCEL_API_KEY=your-api-key' >> .env
```

### Step 3: Verify Connection
```typescript
const teams = await vercel.teams.list(); console.log(teams.length > 0 ? 'OK' : 'No teams');
```

## Output
- Installed SDK package in node_modules or site-packages
- Environment variable or .env file with API key
- Successful connection verification output

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Invalid API Key | Incorrect or expired key | Verify key in Vercel dashboard |
| Rate Limited | Exceeded quota | Check quota at https://vercel.com/docs |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { VercelClient } from 'vercel';

const client = new VercelClient({
  apiKey: process.env.VERCEL_API_KEY,
});
```

### Python Setup
```python
from None import VercelClient

client = VercelClient(
    api_key=os.environ.get('VERCEL_API_KEY')
)
```

## Resources
- [Vercel Documentation](https://vercel.com/docs)
- [Vercel Dashboard](https://api.vercel.com)
- [Vercel Status](https://www.vercel-status.com)

## Next Steps
After successful auth, proceed to `vercel-hello-world` for your first API call.