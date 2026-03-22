---
name: remofirst-install-auth
description: |
  Install and configure RemoFirst SDK/CLI authentication.
  Use when setting up a new RemoFirst integration, configuring API keys,
  or initializing RemoFirst in your project.
  Trigger with phrases like "install remofirst", "setup remofirst",
  "remofirst auth", "configure remofirst API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, remofirst]
---

# RemoFirst Install & Auth

## Overview
Set up RemoFirst SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- RemoFirst account with API access
- API key from RemoFirst dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @remofirst/sdk

# Python
pip install remofirst
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export REMOFIRST_API_KEY="your-api-key"

# Or create .env file
echo 'REMOFIRST_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in RemoFirst dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.remofirst.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { RemoFirstClient } from '@remofirst/sdk';

const client = new RemoFirstClient({
  apiKey: process.env.REMOFIRST_API_KEY,
});
```

### Python Setup
```python
from remofirst import RemoFirstClient

client = RemoFirstClient(
    api_key=os.environ.get('REMOFIRST_API_KEY')
)
```

## Resources
- [RemoFirst Documentation](https://docs.remofirst.com)
- [RemoFirst Dashboard](https://api.remofirst.com)
- [RemoFirst Status](https://status.remofirst.com)

## Next Steps
After successful auth, proceed to `remofirst-hello-world` for your first API call.