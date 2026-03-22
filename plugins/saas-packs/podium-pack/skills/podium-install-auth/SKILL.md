---
name: podium-install-auth
description: |
  Install and configure Podium SDK/CLI authentication.
  Use when setting up a new Podium integration, configuring API keys,
  or initializing Podium in your project.
  Trigger with phrases like "install podium", "setup podium",
  "podium auth", "configure podium API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, podium]
---

# Podium Install & Auth

## Overview
Set up Podium SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Podium account with API access
- API key from Podium dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @podium/sdk

# Python
pip install podium
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export PODIUM_API_KEY="your-api-key"

# Or create .env file
echo 'PODIUM_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Podium dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.podium.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { PodiumClient } from '@podium/sdk';

const client = new PodiumClient({
  apiKey: process.env.PODIUM_API_KEY,
});
```

### Python Setup
```python
from podium import PodiumClient

client = PodiumClient(
    api_key=os.environ.get('PODIUM_API_KEY')
)
```

## Resources
- [Podium Documentation](https://docs.podium.com)
- [Podium Dashboard](https://api.podium.com)
- [Podium Status](https://status.podium.com)

## Next Steps
After successful auth, proceed to `podium-hello-world` for your first API call.