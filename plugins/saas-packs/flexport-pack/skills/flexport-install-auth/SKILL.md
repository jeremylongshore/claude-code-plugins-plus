---
name: flexport-install-auth
description: |
  Install and configure Flexport SDK/CLI authentication.
  Use when setting up a new Flexport integration, configuring API keys,
  or initializing Flexport in your project.
  Trigger with phrases like "install flexport", "setup flexport",
  "flexport auth", "configure flexport API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, flexport]
---

# Flexport Install & Auth

## Overview
Set up Flexport SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Flexport account with API access
- API key from Flexport dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @flexport/sdk

# Python
pip install flexport
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export FLEXPORT_API_KEY="your-api-key"

# Or create .env file
echo 'FLEXPORT_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Flexport dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.flexport.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { FlexportClient } from '@flexport/sdk';

const client = new FlexportClient({
  apiKey: process.env.FLEXPORT_API_KEY,
});
```

### Python Setup
```python
from flexport import FlexportClient

client = FlexportClient(
    api_key=os.environ.get('FLEXPORT_API_KEY')
)
```

## Resources
- [Flexport Documentation](https://docs.flexport.com)
- [Flexport Dashboard](https://api.flexport.com)
- [Flexport Status](https://status.flexport.com)

## Next Steps
After successful auth, proceed to `flexport-hello-world` for your first API call.