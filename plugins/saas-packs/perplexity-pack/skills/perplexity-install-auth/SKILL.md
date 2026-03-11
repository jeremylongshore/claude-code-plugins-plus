---
name: perplexity-install-auth
description: |
  Install and configure Perplexity SDK/CLI authentication.
  Use when setting up a new Perplexity integration, configuring API keys,
  or initializing Perplexity in your project.
  Trigger with phrases like "install perplexity", "setup perplexity",
  "perplexity auth", "configure perplexity API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Perplexity Install & Auth

## Overview
Set up Perplexity SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Perplexity account with API access
- API key from Perplexity dashboard

## Instructions

### Step 1: Install SDK
```bash
set -euo pipefail
# Node.js
npm install @perplexity/sdk

# Python
pip install perplexity
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export PERPLEXITY_API_KEY="your-api-key"

# Or create .env file
echo 'PERPLEXITY_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Perplexity dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.perplexity.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { PerplexityClient } from '@perplexity/sdk';

const client = new PerplexityClient({
  apiKey: process.env.PERPLEXITY_API_KEY,
});
```

### Python Setup
```python
from perplexity import PerplexityClient

client = PerplexityClient(
    api_key=os.environ.get('PERPLEXITY_API_KEY')
)
```

## Resources
- [Perplexity Documentation](https://docs.perplexity.com)
- [Perplexity Dashboard](https://api.perplexity.com)
- [Perplexity Status](https://status.perplexity.com)

## Next Steps
After successful auth, proceed to `perplexity-hello-world` for your first API call.