---
name: guidewire-install-auth
description: |
  Install and configure Guidewire SDK/CLI authentication.
  Use when setting up a new Guidewire integration, configuring API keys,
  or initializing Guidewire in your project.
  Trigger with phrases like "install guidewire", "setup guidewire",
  "guidewire auth", "configure guidewire API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, guidewire]
---

# Guidewire Install & Auth

## Overview
Set up Guidewire SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Guidewire account with API access
- API key from Guidewire dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @guidewire/sdk

# Python
pip install guidewire
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export GUIDEWIRE_API_KEY="your-api-key"

# Or create .env file
echo 'GUIDEWIRE_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Guidewire dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.guidewire.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { GuidewireClient } from '@guidewire/sdk';

const client = new GuidewireClient({
  apiKey: process.env.GUIDEWIRE_API_KEY,
});
```

### Python Setup
```python
from guidewire import GuidewireClient

client = GuidewireClient(
    api_key=os.environ.get('GUIDEWIRE_API_KEY')
)
```

## Resources
- [Guidewire Documentation](https://docs.guidewire.com)
- [Guidewire Dashboard](https://api.guidewire.com)
- [Guidewire Status](https://status.guidewire.com)

## Next Steps
After successful auth, proceed to `guidewire-hello-world` for your first API call.