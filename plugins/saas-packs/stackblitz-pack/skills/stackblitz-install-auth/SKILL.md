---
name: stackblitz-install-auth
description: |
  Install and configure StackBlitz SDK/CLI authentication.
  Use when setting up a new StackBlitz integration, configuring API keys,
  or initializing StackBlitz in your project.
  Trigger with phrases like "install stackblitz", "setup stackblitz",
  "stackblitz auth", "configure stackblitz API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, stackblitz]
---

# StackBlitz Install & Auth

## Overview
Set up StackBlitz SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- StackBlitz account with API access
- API key from StackBlitz dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @stackblitz/sdk

# Python
pip install stackblitz
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export STACKBLITZ_API_KEY="your-api-key"

# Or create .env file
echo 'STACKBLITZ_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in StackBlitz dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.stackblitz.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { StackBlitzClient } from '@stackblitz/sdk';

const client = new StackBlitzClient({
  apiKey: process.env.STACKBLITZ_API_KEY,
});
```

### Python Setup
```python
from stackblitz import StackBlitzClient

client = StackBlitzClient(
    api_key=os.environ.get('STACKBLITZ_API_KEY')
)
```

## Resources
- [StackBlitz Documentation](https://docs.stackblitz.com)
- [StackBlitz Dashboard](https://api.stackblitz.com)
- [StackBlitz Status](https://status.stackblitz.com)

## Next Steps
After successful auth, proceed to `stackblitz-hello-world` for your first API call.