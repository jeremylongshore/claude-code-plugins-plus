---
name: gamma-install-auth
description: |
  Install and configure Gamma SDK/CLI authentication.
  Use when setting up a new Gamma integration, configuring API keys,
  or initializing Gamma in your project.
  Trigger with phrases like "install gamma", "setup gamma",
  "gamma auth", "configure gamma API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, gamma]
---

# Gamma Install & Auth

## Overview
Set up Gamma SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Gamma account with API access
- API key from Gamma dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @gamma/sdk

# Python
pip install gamma
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export GAMMA_API_KEY="your-api-key"

# Or create .env file
echo 'GAMMA_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Gamma dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.gamma.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { GammaClient } from '@gamma/sdk';

const client = new GammaClient({
  apiKey: process.env.GAMMA_API_KEY,
});
```

### Python Setup
```python
from gamma import GammaClient

client = GammaClient(
    api_key=os.environ.get('GAMMA_API_KEY')
)
```

## Resources
- [Gamma Documentation](https://docs.gamma.com)
- [Gamma Dashboard](https://api.gamma.com)
- [Gamma Status](https://status.gamma.com)

## Next Steps
After successful auth, proceed to `gamma-hello-world` for your first API call.