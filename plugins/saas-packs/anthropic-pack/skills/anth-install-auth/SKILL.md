---
name: anth-install-auth
description: |
  Install and configure Anthropic SDK/CLI authentication.
  Use when setting up a new Anthropic integration, configuring API keys,
  or initializing Anthropic in your project.
  Trigger with phrases like "install anthropic", "setup anthropic",
  "anthropic auth", "configure anthropic API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, anthropic]
compatible-with: claude-code
---

# Anthropic Install & Auth

## Overview
Set up Anthropic SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Anthropic account with API access
- API key from Anthropic dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @anthropic/sdk

# Python
pip install anthropic
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export ANTHROPIC_API_KEY="your-api-key"

# Or create .env file
echo 'ANTHROPIC_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Anthropic dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.anthropic.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { AnthropicClient } from '@anthropic/sdk';

const client = new AnthropicClient({
  apiKey: process.env.ANTHROPIC_API_KEY,
});
```

### Python Setup
```python
from anthropic import AnthropicClient

client = AnthropicClient(
    api_key=os.environ.get('ANTHROPIC_API_KEY')
)
```

## Resources
- [Anthropic Documentation](https://docs.anthropic.com)
- [Anthropic Dashboard](https://api.anthropic.com)
- [Anthropic Status](https://status.anthropic.com)

## Next Steps
After successful auth, proceed to `anthropic-hello-world` for your first API call.