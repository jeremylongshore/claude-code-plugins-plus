---
name: firecrawl-install-auth
description: |
  Install and configure FireCrawl SDK/CLI authentication.
  Use when setting up a new FireCrawl integration, configuring API keys,
  or initializing FireCrawl in your project.
  Trigger with phrases like "install firecrawl", "setup firecrawl",
  "firecrawl auth", "configure firecrawl API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# FireCrawl Install & Auth

## Overview
Set up FireCrawl SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- FireCrawl account with API access
- API key from FireCrawl dashboard

## Instructions

### Step 1: Install SDK
```bash
set -euo pipefail
# Node.js
npm install @firecrawl/sdk

# Python
pip install firecrawl
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export FIRECRAWL_API_KEY="your-api-key"

# Or create .env file
echo 'FIRECRAWL_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in FireCrawl dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.firecrawl.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { FireCrawlClient } from '@firecrawl/sdk';

const client = new FireCrawlClient({
  apiKey: process.env.FIRECRAWL_API_KEY,
});
```

### Python Setup
```python
from firecrawl import FireCrawlClient

client = FireCrawlClient(
    api_key=os.environ.get('FIRECRAWL_API_KEY')
)
```

## Resources
- [FireCrawl Documentation](https://docs.firecrawl.com)
- [FireCrawl Dashboard](https://api.firecrawl.com)
- [FireCrawl Status](https://status.firecrawl.com)

## Next Steps
After successful auth, proceed to `firecrawl-hello-world` for your first API call.