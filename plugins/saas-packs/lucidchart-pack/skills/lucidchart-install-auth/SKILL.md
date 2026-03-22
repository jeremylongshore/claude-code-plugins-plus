---
name: lucidchart-install-auth
description: |
  Install and configure Lucidchart SDK/CLI authentication.
  Use when setting up a new Lucidchart integration, configuring API keys,
  or initializing Lucidchart in your project.
  Trigger with phrases like "install lucidchart", "setup lucidchart",
  "lucidchart auth", "configure lucidchart API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, lucidchart]
---

# Lucidchart Install & Auth

## Overview
Set up Lucidchart SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Lucidchart account with API access
- API key from Lucidchart dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @lucidchart/sdk

# Python
pip install lucidchart
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export LUCIDCHART_API_KEY="your-api-key"

# Or create .env file
echo 'LUCIDCHART_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Lucidchart dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.lucidchart.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { LucidchartClient } from '@lucidchart/sdk';

const client = new LucidchartClient({
  apiKey: process.env.LUCIDCHART_API_KEY,
});
```

### Python Setup
```python
from lucidchart import LucidchartClient

client = LucidchartClient(
    api_key=os.environ.get('LUCIDCHART_API_KEY')
)
```

## Resources
- [Lucidchart Documentation](https://docs.lucidchart.com)
- [Lucidchart Dashboard](https://api.lucidchart.com)
- [Lucidchart Status](https://status.lucidchart.com)

## Next Steps
After successful auth, proceed to `lucidchart-hello-world` for your first API call.