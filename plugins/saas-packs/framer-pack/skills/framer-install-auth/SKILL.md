---
name: framer-install-auth
description: |
  Install and configure Framer SDK/CLI authentication.
  Use when setting up a new Framer integration, configuring API keys,
  or initializing Framer in your project.
  Trigger with phrases like "install framer", "setup framer",
  "framer auth", "configure framer API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, framer]
---

# Framer Install & Auth

## Overview
Set up Framer SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Framer account with API access
- API key from Framer dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @framer/sdk

# Python
pip install framer
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export FRAMER_API_KEY="your-api-key"

# Or create .env file
echo 'FRAMER_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Framer dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.framer.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { FramerClient } from '@framer/sdk';

const client = new FramerClient({
  apiKey: process.env.FRAMER_API_KEY,
});
```

### Python Setup
```python
from framer import FramerClient

client = FramerClient(
    api_key=os.environ.get('FRAMER_API_KEY')
)
```

## Resources
- [Framer Documentation](https://docs.framer.com)
- [Framer Dashboard](https://api.framer.com)
- [Framer Status](https://status.framer.com)

## Next Steps
After successful auth, proceed to `framer-hello-world` for your first API call.