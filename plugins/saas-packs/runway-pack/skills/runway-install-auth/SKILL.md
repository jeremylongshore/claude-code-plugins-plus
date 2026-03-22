---
name: runway-install-auth
description: |
  Install and configure Runway SDK/CLI authentication.
  Use when setting up a new Runway integration, configuring API keys,
  or initializing Runway in your project.
  Trigger with phrases like "install runway", "setup runway",
  "runway auth", "configure runway API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, runway]
---

# Runway Install & Auth

## Overview
Set up Runway SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Runway account with API access
- API key from Runway dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @runway/sdk

# Python
pip install runway
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export RUNWAY_API_KEY="your-api-key"

# Or create .env file
echo 'RUNWAY_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Runway dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.runway.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { RunwayClient } from '@runway/sdk';

const client = new RunwayClient({
  apiKey: process.env.RUNWAY_API_KEY,
});
```

### Python Setup
```python
from runway import RunwayClient

client = RunwayClient(
    api_key=os.environ.get('RUNWAY_API_KEY')
)
```

## Resources
- [Runway Documentation](https://docs.runway.com)
- [Runway Dashboard](https://api.runway.com)
- [Runway Status](https://status.runway.com)

## Next Steps
After successful auth, proceed to `runway-hello-world` for your first API call.