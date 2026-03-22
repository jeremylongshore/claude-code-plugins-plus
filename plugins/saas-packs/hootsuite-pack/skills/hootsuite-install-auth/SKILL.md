---
name: hootsuite-install-auth
description: |
  Install and configure Hootsuite SDK/CLI authentication.
  Use when setting up a new Hootsuite integration, configuring API keys,
  or initializing Hootsuite in your project.
  Trigger with phrases like "install hootsuite", "setup hootsuite",
  "hootsuite auth", "configure hootsuite API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, hootsuite]
---

# Hootsuite Install & Auth

## Overview
Set up Hootsuite SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Hootsuite account with API access
- API key from Hootsuite dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @hootsuite/sdk

# Python
pip install hootsuite
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export HOOTSUITE_API_KEY="your-api-key"

# Or create .env file
echo 'HOOTSUITE_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Hootsuite dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.hootsuite.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { HootsuiteClient } from '@hootsuite/sdk';

const client = new HootsuiteClient({
  apiKey: process.env.HOOTSUITE_API_KEY,
});
```

### Python Setup
```python
from hootsuite import HootsuiteClient

client = HootsuiteClient(
    api_key=os.environ.get('HOOTSUITE_API_KEY')
)
```

## Resources
- [Hootsuite Documentation](https://docs.hootsuite.com)
- [Hootsuite Dashboard](https://api.hootsuite.com)
- [Hootsuite Status](https://status.hootsuite.com)

## Next Steps
After successful auth, proceed to `hootsuite-hello-world` for your first API call.