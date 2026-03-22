---
name: castai-install-auth
description: |
  Install and configure Cast AI SDK/CLI authentication.
  Use when setting up a new Cast AI integration, configuring API keys,
  or initializing Cast AI in your project.
  Trigger with phrases like "install castai", "setup castai",
  "castai auth", "configure castai API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, castai]
---

# Cast AI Install & Auth

## Overview
Set up Cast AI SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Cast AI account with API access
- API key from Cast AI dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @castai/sdk

# Python
pip install castai
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export CASTAI_API_KEY="your-api-key"

# Or create .env file
echo 'CASTAI_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Cast AI dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.castai.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { CastAIClient } from '@castai/sdk';

const client = new CastAIClient({
  apiKey: process.env.CASTAI_API_KEY,
});
```

### Python Setup
```python
from castai import CastAIClient

client = CastAIClient(
    api_key=os.environ.get('CASTAI_API_KEY')
)
```

## Resources
- [Cast AI Documentation](https://docs.castai.com)
- [Cast AI Dashboard](https://api.castai.com)
- [Cast AI Status](https://status.castai.com)

## Next Steps
After successful auth, proceed to `castai-hello-world` for your first API call.