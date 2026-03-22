---
name: fathom-install-auth
description: |
  Install and configure Fathom SDK/CLI authentication.
  Use when setting up a new Fathom integration, configuring API keys,
  or initializing Fathom in your project.
  Trigger with phrases like "install fathom", "setup fathom",
  "fathom auth", "configure fathom API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, fathom]
---

# Fathom Install & Auth

## Overview
Set up Fathom SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Fathom account with API access
- API key from Fathom dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @fathom/sdk

# Python
pip install fathom
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export FATHOM_API_KEY="your-api-key"

# Or create .env file
echo 'FATHOM_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Fathom dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.fathom.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { FathomClient } from '@fathom/sdk';

const client = new FathomClient({
  apiKey: process.env.FATHOM_API_KEY,
});
```

### Python Setup
```python
from fathom import FathomClient

client = FathomClient(
    api_key=os.environ.get('FATHOM_API_KEY')
)
```

## Resources
- [Fathom Documentation](https://docs.fathom.com)
- [Fathom Dashboard](https://api.fathom.com)
- [Fathom Status](https://status.fathom.com)

## Next Steps
After successful auth, proceed to `fathom-hello-world` for your first API call.