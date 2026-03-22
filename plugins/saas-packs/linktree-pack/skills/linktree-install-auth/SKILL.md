---
name: linktree-install-auth
description: |
  Install and configure Linktree SDK/CLI authentication.
  Use when setting up a new Linktree integration, configuring API keys,
  or initializing Linktree in your project.
  Trigger with phrases like "install linktree", "setup linktree",
  "linktree auth", "configure linktree API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, linktree]
---

# Linktree Install & Auth

## Overview
Set up Linktree SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Linktree account with API access
- API key from Linktree dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @linktree/sdk

# Python
pip install linktree
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export LINKTREE_API_KEY="your-api-key"

# Or create .env file
echo 'LINKTREE_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Linktree dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.linktree.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { LinktreeClient } from '@linktree/sdk';

const client = new LinktreeClient({
  apiKey: process.env.LINKTREE_API_KEY,
});
```

### Python Setup
```python
from linktree import LinktreeClient

client = LinktreeClient(
    api_key=os.environ.get('LINKTREE_API_KEY')
)
```

## Resources
- [Linktree Documentation](https://docs.linktree.com)
- [Linktree Dashboard](https://api.linktree.com)
- [Linktree Status](https://status.linktree.com)

## Next Steps
After successful auth, proceed to `linktree-hello-world` for your first API call.