---
name: databricks-install-auth
description: |
  Install and configure Databricks SDK/CLI authentication.
  Use when setting up a new Databricks integration, configuring API keys,
  or initializing Databricks in your project.
  Trigger with phrases like "install databricks", "setup databricks",
  "databricks auth", "configure databricks API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, databricks]
---

# Databricks Install & Auth

## Overview
Set up Databricks SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Databricks account with API access
- API key from Databricks dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @databricks/sdk

# Python
pip install databricks
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export DATABRICKS_API_KEY="your-api-key"

# Or create .env file
echo 'DATABRICKS_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Databricks dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.databricks.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { DatabricksClient } from '@databricks/sdk';

const client = new DatabricksClient({
  apiKey: process.env.DATABRICKS_API_KEY,
});
```

### Python Setup
```python
from databricks import DatabricksClient

client = DatabricksClient(
    api_key=os.environ.get('DATABRICKS_API_KEY')
)
```

## Resources
- [Databricks Documentation](https://docs.databricks.com)
- [Databricks Dashboard](https://api.databricks.com)
- [Databricks Status](https://status.databricks.com)

## Next Steps
After successful auth, proceed to `databricks-hello-world` for your first API call.