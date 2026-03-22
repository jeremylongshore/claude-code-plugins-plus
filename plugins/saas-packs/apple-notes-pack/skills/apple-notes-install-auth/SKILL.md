---
name: apple-notes-install-auth
description: |
  Install and configure Apple Notes SDK/CLI authentication.
  Use when setting up a new Apple Notes integration, configuring API keys,
  or initializing Apple Notes in your project.
  Trigger with phrases like "install apple-notes", "setup apple-notes",
  "apple-notes auth", "configure apple-notes API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, apple-notes]
---

# Apple Notes Install & Auth

## Overview
Set up Apple Notes SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Apple Notes account with API access
- API key from Apple Notes dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @apple-notes/sdk

# Python
pip install apple-notes
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export APPLE-NOTES_API_KEY="your-api-key"

# Or create .env file
echo 'APPLE-NOTES_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Apple Notes dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.apple-notes.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { AppleNotesClient } from '@apple-notes/sdk';

const client = new AppleNotesClient({
  apiKey: process.env.APPLE-NOTES_API_KEY,
});
```

### Python Setup
```python
from apple-notes import AppleNotesClient

client = AppleNotesClient(
    api_key=os.environ.get('APPLE-NOTES_API_KEY')
)
```

## Resources
- [Apple Notes Documentation](https://docs.apple-notes.com)
- [Apple Notes Dashboard](https://api.apple-notes.com)
- [Apple Notes Status](https://status.apple-notes.com)

## Next Steps
After successful auth, proceed to `apple-notes-hello-world` for your first API call.