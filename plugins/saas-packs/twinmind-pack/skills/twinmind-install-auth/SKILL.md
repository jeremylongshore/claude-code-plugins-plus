---
name: twinmind-install-auth
description: |
  Install and configure TwinMind SDK/CLI authentication.
  Use when setting up a new TwinMind integration, configuring API keys,
  or initializing TwinMind in your project.
  Trigger with phrases like "install twinmind", "setup twinmind",
  "twinmind auth", "configure twinmind API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, twinmind]
---

# TwinMind Install & Auth

## Overview
Set up TwinMind SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- TwinMind account with API access
- API key from TwinMind dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @twinmind/sdk

# Python
pip install twinmind
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export TWINMIND_API_KEY="your-api-key"

# Or create .env file
echo 'TWINMIND_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in TwinMind dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.twinmind.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { TwinMindClient } from '@twinmind/sdk';

const client = new TwinMindClient({
  apiKey: process.env.TWINMIND_API_KEY,
});
```

### Python Setup
```python
from twinmind import TwinMindClient

client = TwinMindClient(
    api_key=os.environ.get('TWINMIND_API_KEY')
)
```

## Resources
- [TwinMind Documentation](https://docs.twinmind.com)
- [TwinMind Dashboard](https://api.twinmind.com)
- [TwinMind Status](https://status.twinmind.com)

## Next Steps
After successful auth, proceed to `twinmind-hello-world` for your first API call.