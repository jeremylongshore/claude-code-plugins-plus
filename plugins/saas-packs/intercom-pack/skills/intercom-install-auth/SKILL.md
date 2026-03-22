---
name: intercom-install-auth
description: |
  Install and configure Intercom SDK/CLI authentication.
  Use when setting up a new Intercom integration, configuring API keys,
  or initializing Intercom in your project.
  Trigger with phrases like "install intercom", "setup intercom",
  "intercom auth", "configure intercom API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, intercom]
---

# Intercom Install & Auth

## Overview
Set up Intercom SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Intercom account with API access
- API key from Intercom dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @intercom/sdk

# Python
pip install intercom
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export INTERCOM_API_KEY="your-api-key"

# Or create .env file
echo 'INTERCOM_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Intercom dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.intercom.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { IntercomClient } from '@intercom/sdk';

const client = new IntercomClient({
  apiKey: process.env.INTERCOM_API_KEY,
});
```

### Python Setup
```python
from intercom import IntercomClient

client = IntercomClient(
    api_key=os.environ.get('INTERCOM_API_KEY')
)
```

## Resources
- [Intercom Documentation](https://docs.intercom.com)
- [Intercom Dashboard](https://api.intercom.com)
- [Intercom Status](https://status.intercom.com)

## Next Steps
After successful auth, proceed to `intercom-hello-world` for your first API call.