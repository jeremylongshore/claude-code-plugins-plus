---
name: canva-install-auth
description: |
  Install and configure Canva SDK/CLI authentication.
  Use when setting up a new Canva integration, configuring API keys,
  or initializing Canva in your project.
  Trigger with phrases like "install canva", "setup canva",
  "canva auth", "configure canva API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, canva]
---

# Canva Install & Auth

## Overview
Set up Canva SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Canva account with API access
- API key from Canva dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @canva/sdk

# Python
pip install canva
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export CANVA_API_KEY="your-api-key"

# Or create .env file
echo 'CANVA_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Canva dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.canva.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { CanvaClient } from '@canva/sdk';

const client = new CanvaClient({
  apiKey: process.env.CANVA_API_KEY,
});
```

### Python Setup
```python
from canva import CanvaClient

client = CanvaClient(
    api_key=os.environ.get('CANVA_API_KEY')
)
```

## Resources
- [Canva Documentation](https://docs.canva.com)
- [Canva Dashboard](https://api.canva.com)
- [Canva Status](https://status.canva.com)

## Next Steps
After successful auth, proceed to `canva-hello-world` for your first API call.