---
name: mistral-install-auth
description: |
  Install and configure Mistral AI SDK/CLI authentication.
  Use when setting up a new Mistral AI integration, configuring API keys,
  or initializing Mistral AI in your project.
  Trigger with phrases like "install mistral", "setup mistral",
  "mistral auth", "configure mistral API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, mistral]
---

# Mistral AI Install & Auth

## Overview
Set up Mistral AI SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Mistral AI account with API access
- API key from Mistral AI dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @mistral/sdk

# Python
pip install mistral
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export MISTRAL_API_KEY="your-api-key"

# Or create .env file
echo 'MISTRAL_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Mistral AI dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.mistral.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { MistralAIClient } from '@mistral/sdk';

const client = new MistralAIClient({
  apiKey: process.env.MISTRAL_API_KEY,
});
```

### Python Setup
```python
from mistral import MistralAIClient

client = MistralAIClient(
    api_key=os.environ.get('MISTRAL_API_KEY')
)
```

## Resources
- [Mistral AI Documentation](https://docs.mistral.com)
- [Mistral AI Dashboard](https://api.mistral.com)
- [Mistral AI Status](https://status.mistral.com)

## Next Steps
After successful auth, proceed to `mistral-hello-world` for your first API call.