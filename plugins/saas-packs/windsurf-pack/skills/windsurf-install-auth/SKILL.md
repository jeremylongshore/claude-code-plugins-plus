---
name: windsurf-install-auth
description: |
  Install and configure Windsurf SDK/CLI authentication.
  Use when setting up a new Windsurf integration, configuring API keys,
  or initializing Windsurf in your project.
  Trigger with phrases like "install windsurf", "setup windsurf",
  "windsurf auth", "configure windsurf API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Windsurf Install & Auth

## Overview
Set up Windsurf SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Windsurf account with API access
- API key from Windsurf dashboard

## Instructions

### Step 1: Install SDK
```bash
set -euo pipefail
# Node.js
npm install @windsurf/sdk

# Python
pip install windsurf
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export WINDSURF_API_KEY="your-api-key"

# Or create .env file
echo 'WINDSURF_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Windsurf dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.windsurf.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { WindsurfClient } from '@windsurf/sdk';

const client = new WindsurfClient({
  apiKey: process.env.WINDSURF_API_KEY,
});
```

### Python Setup
```python
from windsurf import WindsurfClient

client = WindsurfClient(
    api_key=os.environ.get('WINDSURF_API_KEY')
)
```

## Resources
- [Windsurf Documentation](https://docs.windsurf.com)
- [Windsurf Dashboard](https://api.windsurf.com)
- [Windsurf Status](https://status.windsurf.com)

## Next Steps
After successful auth, proceed to `windsurf-hello-world` for your first API call.