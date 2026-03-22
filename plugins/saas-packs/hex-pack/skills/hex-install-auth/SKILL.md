---
name: hex-install-auth
description: |
  Install and configure Hex SDK/CLI authentication.
  Use when setting up a new Hex integration, configuring API keys,
  or initializing Hex in your project.
  Trigger with phrases like "install hex", "setup hex",
  "hex auth", "configure hex API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, hex]
---

# Hex Install & Auth

## Overview
Set up Hex SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Hex account with API access
- API key from Hex dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @hex/sdk

# Python
pip install hex
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export HEX_API_KEY="your-api-key"

# Or create .env file
echo 'HEX_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Hex dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.hex.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { HexClient } from '@hex/sdk';

const client = new HexClient({
  apiKey: process.env.HEX_API_KEY,
});
```

### Python Setup
```python
from hex import HexClient

client = HexClient(
    api_key=os.environ.get('HEX_API_KEY')
)
```

## Resources
- [Hex Documentation](https://docs.hex.com)
- [Hex Dashboard](https://api.hex.com)
- [Hex Status](https://status.hex.com)

## Next Steps
After successful auth, proceed to `hex-hello-world` for your first API call.