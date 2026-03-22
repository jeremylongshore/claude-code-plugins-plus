---
name: lokalise-install-auth
description: |
  Install and configure Lokalise SDK/CLI authentication.
  Use when setting up a new Lokalise integration, configuring API keys,
  or initializing Lokalise in your project.
  Trigger with phrases like "install lokalise", "setup lokalise",
  "lokalise auth", "configure lokalise API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, lokalise]
---

# Lokalise Install & Auth

## Overview
Set up Lokalise SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Lokalise account with API access
- API key from Lokalise dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @lokalise/sdk

# Python
pip install lokalise
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export LOKALISE_API_KEY="your-api-key"

# Or create .env file
echo 'LOKALISE_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Lokalise dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.lokalise.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { LokaliseClient } from '@lokalise/sdk';

const client = new LokaliseClient({
  apiKey: process.env.LOKALISE_API_KEY,
});
```

### Python Setup
```python
from lokalise import LokaliseClient

client = LokaliseClient(
    api_key=os.environ.get('LOKALISE_API_KEY')
)
```

## Resources
- [Lokalise Documentation](https://docs.lokalise.com)
- [Lokalise Dashboard](https://api.lokalise.com)
- [Lokalise Status](https://status.lokalise.com)

## Next Steps
After successful auth, proceed to `lokalise-hello-world` for your first API call.