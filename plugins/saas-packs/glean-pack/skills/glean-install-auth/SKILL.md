---
name: glean-install-auth
description: |
  Install and configure Glean SDK/CLI authentication.
  Use when setting up a new Glean integration, configuring API keys,
  or initializing Glean in your project.
  Trigger with phrases like "install glean", "setup glean",
  "glean auth", "configure glean API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, glean]
---

# Glean Install & Auth

## Overview
Set up Glean SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Glean account with API access
- API key from Glean dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @glean/sdk

# Python
pip install glean
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export GLEAN_API_KEY="your-api-key"

# Or create .env file
echo 'GLEAN_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Glean dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.glean.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { GleanClient } from '@glean/sdk';

const client = new GleanClient({
  apiKey: process.env.GLEAN_API_KEY,
});
```

### Python Setup
```python
from glean import GleanClient

client = GleanClient(
    api_key=os.environ.get('GLEAN_API_KEY')
)
```

## Resources
- [Glean Documentation](https://docs.glean.com)
- [Glean Dashboard](https://api.glean.com)
- [Glean Status](https://status.glean.com)

## Next Steps
After successful auth, proceed to `glean-hello-world` for your first API call.