---
name: assemblyai-install-auth
description: |
  Install and configure AssemblyAI SDK/CLI authentication.
  Use when setting up a new AssemblyAI integration, configuring API keys,
  or initializing AssemblyAI in your project.
  Trigger with phrases like "install assemblyai", "setup assemblyai",
  "assemblyai auth", "configure assemblyai API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, assemblyai]
---

# AssemblyAI Install & Auth

## Overview
Set up AssemblyAI SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- AssemblyAI account with API access
- API key from AssemblyAI dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @assemblyai/sdk

# Python
pip install assemblyai
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export ASSEMBLYAI_API_KEY="your-api-key"

# Or create .env file
echo 'ASSEMBLYAI_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in AssemblyAI dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.assemblyai.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { AssemblyAIClient } from '@assemblyai/sdk';

const client = new AssemblyAIClient({
  apiKey: process.env.ASSEMBLYAI_API_KEY,
});
```

### Python Setup
```python
from assemblyai import AssemblyAIClient

client = AssemblyAIClient(
    api_key=os.environ.get('ASSEMBLYAI_API_KEY')
)
```

## Resources
- [AssemblyAI Documentation](https://docs.assemblyai.com)
- [AssemblyAI Dashboard](https://api.assemblyai.com)
- [AssemblyAI Status](https://status.assemblyai.com)

## Next Steps
After successful auth, proceed to `assemblyai-hello-world` for your first API call.