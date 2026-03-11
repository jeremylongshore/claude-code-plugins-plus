---
name: fireflies-install-auth
description: |
  Install and configure Fireflies.ai SDK/CLI authentication.
  Use when setting up a new Fireflies.ai integration, configuring API keys,
  or initializing Fireflies.ai in your project.
  Trigger with phrases like "install fireflies", "setup fireflies",
  "fireflies auth", "configure fireflies API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Fireflies.ai Install & Auth

## Overview
Set up Fireflies.ai SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Fireflies.ai account with API access
- API key from Fireflies.ai dashboard

## Instructions

### Step 1: Install SDK
```bash
set -euo pipefail
# Node.js
npm install @fireflies/sdk

# Python
pip install fireflies
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export FIREFLIES_API_KEY="your-api-key"

# Or create .env file
echo 'FIREFLIES_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Fireflies.ai dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.fireflies.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { Fireflies.aiClient } from '@fireflies/sdk';

const client = new Fireflies.aiClient({
  apiKey: process.env.FIREFLIES_API_KEY,
});
```

### Python Setup
```python
from fireflies import Fireflies.aiClient

client = Fireflies.aiClient(
    api_key=os.environ.get('FIREFLIES_API_KEY')
)
```

## Resources
- [Fireflies.ai Documentation](https://docs.fireflies.com)
- [Fireflies.ai Dashboard](https://api.fireflies.com)
- [Fireflies.ai Status](https://status.fireflies.com)

## Next Steps
After successful auth, proceed to `fireflies-hello-world` for your first API call.