---
name: linear-install-auth
description: |
  Install and configure Linear SDK/CLI authentication.
  Use when setting up a new Linear integration, configuring API keys,
  or initializing Linear in your project.
  Trigger with phrases like "install linear", "setup linear",
  "linear auth", "configure linear API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, linear]
---

# Linear Install & Auth

## Overview
Set up Linear SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Linear account with API access
- API key from Linear dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @linear/sdk

# Python
pip install linear
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export LINEAR_API_KEY="your-api-key"

# Or create .env file
echo 'LINEAR_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Linear dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.linear.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { LinearClient } from '@linear/sdk';

const client = new LinearClient({
  apiKey: process.env.LINEAR_API_KEY,
});
```

### Python Setup
```python
from linear import LinearClient

client = LinearClient(
    api_key=os.environ.get('LINEAR_API_KEY')
)
```

## Resources
- [Linear Documentation](https://docs.linear.com)
- [Linear Dashboard](https://api.linear.com)
- [Linear Status](https://status.linear.com)

## Next Steps
After successful auth, proceed to `linear-hello-world` for your first API call.