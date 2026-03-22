---
name: together-install-auth
description: |
  Install and configure Together AI SDK/CLI authentication.
  Use when setting up a new Together AI integration, configuring API keys,
  or initializing Together AI in your project.
  Trigger with phrases like "install together", "setup together",
  "together auth", "configure together API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, together]
---

# Together AI Install & Auth

## Overview
Set up Together AI SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Together AI account with API access
- API key from Together AI dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @together/sdk

# Python
pip install together
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export TOGETHER_API_KEY="your-api-key"

# Or create .env file
echo 'TOGETHER_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Together AI dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.together.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { TogetherAIClient } from '@together/sdk';

const client = new TogetherAIClient({
  apiKey: process.env.TOGETHER_API_KEY,
});
```

### Python Setup
```python
from together import TogetherAIClient

client = TogetherAIClient(
    api_key=os.environ.get('TOGETHER_API_KEY')
)
```

## Resources
- [Together AI Documentation](https://docs.together.com)
- [Together AI Dashboard](https://api.together.com)
- [Together AI Status](https://status.together.com)

## Next Steps
After successful auth, proceed to `together-hello-world` for your first API call.