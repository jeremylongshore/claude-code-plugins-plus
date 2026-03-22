---
name: miro-install-auth
description: |
  Install and configure Miro SDK/CLI authentication.
  Use when setting up a new Miro integration, configuring API keys,
  or initializing Miro in your project.
  Trigger with phrases like "install miro", "setup miro",
  "miro auth", "configure miro API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, miro]
---

# Miro Install & Auth

## Overview
Set up Miro SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Miro account with API access
- API key from Miro dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @miro/sdk

# Python
pip install miro
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export MIRO_API_KEY="your-api-key"

# Or create .env file
echo 'MIRO_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Miro dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.miro.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { MiroClient } from '@miro/sdk';

const client = new MiroClient({
  apiKey: process.env.MIRO_API_KEY,
});
```

### Python Setup
```python
from miro import MiroClient

client = MiroClient(
    api_key=os.environ.get('MIRO_API_KEY')
)
```

## Resources
- [Miro Documentation](https://docs.miro.com)
- [Miro Dashboard](https://api.miro.com)
- [Miro Status](https://status.miro.com)

## Next Steps
After successful auth, proceed to `miro-hello-world` for your first API call.