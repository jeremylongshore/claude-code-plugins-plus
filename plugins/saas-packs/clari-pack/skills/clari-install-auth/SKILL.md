---
name: clari-install-auth
description: |
  Install and configure Clari SDK/CLI authentication.
  Use when setting up a new Clari integration, configuring API keys,
  or initializing Clari in your project.
  Trigger with phrases like "install clari", "setup clari",
  "clari auth", "configure clari API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, clari]
---

# Clari Install & Auth

## Overview
Set up Clari SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Clari account with API access
- API key from Clari dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @clari/sdk

# Python
pip install clari
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export CLARI_API_KEY="your-api-key"

# Or create .env file
echo 'CLARI_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Clari dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.clari.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { ClariClient } from '@clari/sdk';

const client = new ClariClient({
  apiKey: process.env.CLARI_API_KEY,
});
```

### Python Setup
```python
from clari import ClariClient

client = ClariClient(
    api_key=os.environ.get('CLARI_API_KEY')
)
```

## Resources
- [Clari Documentation](https://docs.clari.com)
- [Clari Dashboard](https://api.clari.com)
- [Clari Status](https://status.clari.com)

## Next Steps
After successful auth, proceed to `clari-hello-world` for your first API call.