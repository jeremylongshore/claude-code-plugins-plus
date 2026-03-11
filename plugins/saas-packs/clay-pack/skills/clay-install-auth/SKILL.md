---
name: clay-install-auth
description: |
  Install and configure Clay SDK/CLI authentication.
  Use when setting up a new Clay integration, configuring API keys,
  or initializing Clay in your project.
  Trigger with phrases like "install clay", "setup clay",
  "clay auth", "configure clay API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Clay Install & Auth

## Overview
Set up Clay SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Clay account with API access
- API key from Clay dashboard

## Instructions

### Step 1: Install SDK
```bash
set -euo pipefail
# Node.js
npm install @clay/sdk

# Python
pip install clay
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export CLAY_API_KEY="your-api-key"

# Or create .env file
echo 'CLAY_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Clay dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.clay.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { ClayClient } from '@clay/sdk';

const client = new ClayClient({
  apiKey: process.env.CLAY_API_KEY,
});
```

### Python Setup
```python
from clay import ClayClient

client = ClayClient(
    api_key=os.environ.get('CLAY_API_KEY')
)
```

## Resources
- [Clay Documentation](https://docs.clay.com)
- [Clay Dashboard](https://api.clay.com)
- [Clay Status](https://status.clay.com)

## Next Steps
After successful auth, proceed to `clay-hello-world` for your first API call.