---
name: klaviyo-install-auth
description: |
  Install and configure Klaviyo SDK/CLI authentication.
  Use when setting up a new Klaviyo integration, configuring API keys,
  or initializing Klaviyo in your project.
  Trigger with phrases like "install klaviyo", "setup klaviyo",
  "klaviyo auth", "configure klaviyo API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, klaviyo]
---

# Klaviyo Install & Auth

## Overview
Set up Klaviyo SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Klaviyo account with API access
- API key from Klaviyo dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @klaviyo/sdk

# Python
pip install klaviyo
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export KLAVIYO_API_KEY="your-api-key"

# Or create .env file
echo 'KLAVIYO_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Klaviyo dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.klaviyo.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { KlaviyoClient } from '@klaviyo/sdk';

const client = new KlaviyoClient({
  apiKey: process.env.KLAVIYO_API_KEY,
});
```

### Python Setup
```python
from klaviyo import KlaviyoClient

client = KlaviyoClient(
    api_key=os.environ.get('KLAVIYO_API_KEY')
)
```

## Resources
- [Klaviyo Documentation](https://docs.klaviyo.com)
- [Klaviyo Dashboard](https://api.klaviyo.com)
- [Klaviyo Status](https://status.klaviyo.com)

## Next Steps
After successful auth, proceed to `klaviyo-hello-world` for your first API call.