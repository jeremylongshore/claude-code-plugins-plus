---
name: groq-install-auth
description: |
  Install and configure Groq SDK/CLI authentication.
  Use when setting up a new Groq integration, configuring API keys,
  or initializing Groq in your project.
  Trigger with phrases like "install groq", "setup groq",
  "groq auth", "configure groq API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Groq Install & Auth

## Overview
Set up Groq SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Groq account with API access
- API key from Groq dashboard

## Instructions

### Step 1: Install SDK
```bash
set -euo pipefail
# Node.js
npm install @groq/sdk

# Python
pip install groq
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export GROQ_API_KEY="your-api-key"

# Or create .env file
echo 'GROQ_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Groq dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.groq.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { GroqClient } from '@groq/sdk';

const client = new GroqClient({
  apiKey: process.env.GROQ_API_KEY,
});
```

### Python Setup
```python
from groq import GroqClient

client = GroqClient(
    api_key=os.environ.get('GROQ_API_KEY')
)
```

## Resources
- [Groq Documentation](https://docs.groq.com)
- [Groq Dashboard](https://api.groq.com)
- [Groq Status](https://status.groq.com)

## Next Steps
After successful auth, proceed to `groq-hello-world` for your first API call.