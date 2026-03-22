---
name: notion-install-auth
description: |
  Install and configure Notion SDK/CLI authentication.
  Use when setting up a new Notion integration, configuring API keys,
  or initializing Notion in your project.
  Trigger with phrases like "install notion", "setup notion",
  "notion auth", "configure notion API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, notion]
---

# Notion Install & Auth

## Overview
Set up Notion SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Notion account with API access
- API key from Notion dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @notion/sdk

# Python
pip install notion
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export NOTION_API_KEY="your-api-key"

# Or create .env file
echo 'NOTION_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Notion dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.notion.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { NotionClient } from '@notion/sdk';

const client = new NotionClient({
  apiKey: process.env.NOTION_API_KEY,
});
```

### Python Setup
```python
from notion import NotionClient

client = NotionClient(
    api_key=os.environ.get('NOTION_API_KEY')
)
```

## Resources
- [Notion Documentation](https://docs.notion.com)
- [Notion Dashboard](https://api.notion.com)
- [Notion Status](https://status.notion.com)

## Next Steps
After successful auth, proceed to `notion-hello-world` for your first API call.