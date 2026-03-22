---
name: grammarly-install-auth
description: |
  Install and configure Grammarly SDK/CLI authentication.
  Use when setting up a new Grammarly integration, configuring API keys,
  or initializing Grammarly in your project.
  Trigger with phrases like "install grammarly", "setup grammarly",
  "grammarly auth", "configure grammarly API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, grammarly]
---

# Grammarly Install & Auth

## Overview
Set up Grammarly SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Grammarly account with API access
- API key from Grammarly dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @grammarly/sdk

# Python
pip install grammarly
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export GRAMMARLY_API_KEY="your-api-key"

# Or create .env file
echo 'GRAMMARLY_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Grammarly dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.grammarly.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { GrammarlyClient } from '@grammarly/sdk';

const client = new GrammarlyClient({
  apiKey: process.env.GRAMMARLY_API_KEY,
});
```

### Python Setup
```python
from grammarly import GrammarlyClient

client = GrammarlyClient(
    api_key=os.environ.get('GRAMMARLY_API_KEY')
)
```

## Resources
- [Grammarly Documentation](https://docs.grammarly.com)
- [Grammarly Dashboard](https://api.grammarly.com)
- [Grammarly Status](https://status.grammarly.com)

## Next Steps
After successful auth, proceed to `grammarly-hello-world` for your first API call.