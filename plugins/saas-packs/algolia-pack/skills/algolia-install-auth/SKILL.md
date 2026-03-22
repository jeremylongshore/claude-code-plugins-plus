---
name: algolia-install-auth
description: |
  Install and configure Algolia SDK/CLI authentication.
  Use when setting up a new Algolia integration, configuring API keys,
  or initializing Algolia in your project.
  Trigger with phrases like "install algolia", "setup algolia",
  "algolia auth", "configure algolia API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, algolia]
---

# Algolia Install & Auth

## Overview
Set up Algolia SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Algolia account with API access
- API key from Algolia dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @algolia/sdk

# Python
pip install algolia
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export ALGOLIA_API_KEY="your-api-key"

# Or create .env file
echo 'ALGOLIA_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Algolia dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.algolia.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { AlgoliaClient } from '@algolia/sdk';

const client = new AlgoliaClient({
  apiKey: process.env.ALGOLIA_API_KEY,
});
```

### Python Setup
```python
from algolia import AlgoliaClient

client = AlgoliaClient(
    api_key=os.environ.get('ALGOLIA_API_KEY')
)
```

## Resources
- [Algolia Documentation](https://docs.algolia.com)
- [Algolia Dashboard](https://api.algolia.com)
- [Algolia Status](https://status.algolia.com)

## Next Steps
After successful auth, proceed to `algolia-hello-world` for your first API call.