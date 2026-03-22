---
name: elevenlabs-install-auth
description: |
  Install and configure ElevenLabs SDK/CLI authentication.
  Use when setting up a new ElevenLabs integration, configuring API keys,
  or initializing ElevenLabs in your project.
  Trigger with phrases like "install elevenlabs", "setup elevenlabs",
  "elevenlabs auth", "configure elevenlabs API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, elevenlabs]
---

# ElevenLabs Install & Auth

## Overview
Set up ElevenLabs SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- ElevenLabs account with API access
- API key from ElevenLabs dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @elevenlabs/sdk

# Python
pip install elevenlabs
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export ELEVENLABS_API_KEY="your-api-key"

# Or create .env file
echo 'ELEVENLABS_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in ElevenLabs dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.elevenlabs.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { ElevenLabsClient } from '@elevenlabs/sdk';

const client = new ElevenLabsClient({
  apiKey: process.env.ELEVENLABS_API_KEY,
});
```

### Python Setup
```python
from elevenlabs import ElevenLabsClient

client = ElevenLabsClient(
    api_key=os.environ.get('ELEVENLABS_API_KEY')
)
```

## Resources
- [ElevenLabs Documentation](https://docs.elevenlabs.com)
- [ElevenLabs Dashboard](https://api.elevenlabs.com)
- [ElevenLabs Status](https://status.elevenlabs.com)

## Next Steps
After successful auth, proceed to `elevenlabs-hello-world` for your first API call.