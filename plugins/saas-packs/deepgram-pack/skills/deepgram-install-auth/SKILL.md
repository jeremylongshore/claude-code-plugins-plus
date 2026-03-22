---
name: deepgram-install-auth
description: |
  Install and configure Deepgram SDK/CLI authentication.
  Use when setting up a new Deepgram integration, configuring API keys,
  or initializing Deepgram in your project.
  Trigger with phrases like "install deepgram", "setup deepgram",
  "deepgram auth", "configure deepgram API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, deepgram]
---

# Deepgram Install & Auth

## Overview
Set up Deepgram SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Deepgram account with API access
- API key from Deepgram dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @deepgram/sdk

# Python
pip install deepgram
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export DEEPGRAM_API_KEY="your-api-key"

# Or create .env file
echo 'DEEPGRAM_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Deepgram dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.deepgram.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { DeepgramClient } from '@deepgram/sdk';

const client = new DeepgramClient({
  apiKey: process.env.DEEPGRAM_API_KEY,
});
```

### Python Setup
```python
from deepgram import DeepgramClient

client = DeepgramClient(
    api_key=os.environ.get('DEEPGRAM_API_KEY')
)
```

## Resources
- [Deepgram Documentation](https://docs.deepgram.com)
- [Deepgram Dashboard](https://api.deepgram.com)
- [Deepgram Status](https://status.deepgram.com)

## Next Steps
After successful auth, proceed to `deepgram-hello-world` for your first API call.