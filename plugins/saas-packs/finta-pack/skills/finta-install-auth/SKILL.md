---
name: finta-install-auth
description: |
  Install and configure Finta SDK/CLI authentication.
  Use when setting up a new Finta integration, configuring API keys,
  or initializing Finta in your project.
  Trigger with phrases like "install finta", "setup finta",
  "finta auth", "configure finta API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, finta]
---

# Finta Install & Auth

## Overview
Set up Finta SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Finta account with API access
- API key from Finta dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @finta/sdk

# Python
pip install finta
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export FINTA_API_KEY="your-api-key"

# Or create .env file
echo 'FINTA_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Finta dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.finta.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { FintaClient } from '@finta/sdk';

const client = new FintaClient({
  apiKey: process.env.FINTA_API_KEY,
});
```

### Python Setup
```python
from finta import FintaClient

client = FintaClient(
    api_key=os.environ.get('FINTA_API_KEY')
)
```

## Resources
- [Finta Documentation](https://docs.finta.com)
- [Finta Dashboard](https://api.finta.com)
- [Finta Status](https://status.finta.com)

## Next Steps
After successful auth, proceed to `finta-hello-world` for your first API call.