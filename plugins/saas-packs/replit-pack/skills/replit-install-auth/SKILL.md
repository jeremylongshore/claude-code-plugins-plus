---
name: replit-install-auth
description: |
  Install and configure Replit SDK/CLI authentication.
  Use when setting up a new Replit integration, configuring API keys,
  or initializing Replit in your project.
  Trigger with phrases like "install replit", "setup replit",
  "replit auth", "configure replit API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Replit Install & Auth

## Overview
Set up Replit SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Replit account with API access
- API key from Replit dashboard

## Instructions

### Step 1: Install SDK
```bash
set -euo pipefail
# Node.js
npm install @replit/sdk

# Python
pip install replit
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export REPLIT_API_KEY="your-api-key"

# Or create .env file
echo 'REPLIT_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Replit dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.replit.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { ReplitClient } from '@replit/sdk';

const client = new ReplitClient({
  apiKey: process.env.REPLIT_API_KEY,
});
```

### Python Setup
```python
from replit import ReplitClient

client = ReplitClient(
    api_key=os.environ.get('REPLIT_API_KEY')
)
```

## Resources
- [Replit Documentation](https://docs.replit.com)
- [Replit Dashboard](https://api.replit.com)
- [Replit Status](https://status.replit.com)

## Next Steps
After successful auth, proceed to `replit-hello-world` for your first API call.