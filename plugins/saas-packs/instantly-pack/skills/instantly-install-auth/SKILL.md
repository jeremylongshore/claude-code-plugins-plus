---
name: instantly-install-auth
description: |
  Install and configure Instantly SDK/CLI authentication.
  Use when setting up a new Instantly integration, configuring API keys,
  or initializing Instantly in your project.
  Trigger with phrases like "install instantly", "setup instantly",
  "instantly auth", "configure instantly API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Instantly Install & Auth

## Overview
Set up Instantly SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Instantly account with API access
- API key from Instantly dashboard

## Instructions

### Step 1: Install SDK
```bash
set -euo pipefail
# Node.js
npm install @instantly/sdk

# Python
pip install instantly
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export INSTANTLY_API_KEY="your-api-key"

# Or create .env file
echo 'INSTANTLY_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Instantly dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.instantly.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { InstantlyClient } from '@instantly/sdk';

const client = new InstantlyClient({
  apiKey: process.env.INSTANTLY_API_KEY,
});
```

### Python Setup
```python
from instantly import InstantlyClient

client = InstantlyClient(
    api_key=os.environ.get('INSTANTLY_API_KEY')
)
```

## Resources
- [Instantly Documentation](https://docs.instantly.com)
- [Instantly Dashboard](https://api.instantly.com)
- [Instantly Status](https://status.instantly.com)

## Next Steps
After successful auth, proceed to `instantly-hello-world` for your first API call.