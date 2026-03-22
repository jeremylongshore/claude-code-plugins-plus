---
name: snowflake-install-auth
description: |
  Install and configure Snowflake SDK/CLI authentication.
  Use when setting up a new Snowflake integration, configuring API keys,
  or initializing Snowflake in your project.
  Trigger with phrases like "install snowflake", "setup snowflake",
  "snowflake auth", "configure snowflake API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, snowflake]
---

# Snowflake Install & Auth

## Overview
Set up Snowflake SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Snowflake account with API access
- API key from Snowflake dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @snowflake/sdk

# Python
pip install snowflake
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export SNOWFLAKE_API_KEY="your-api-key"

# Or create .env file
echo 'SNOWFLAKE_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in Snowflake dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.snowflake.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { SnowflakeClient } from '@snowflake/sdk';

const client = new SnowflakeClient({
  apiKey: process.env.SNOWFLAKE_API_KEY,
});
```

### Python Setup
```python
from snowflake import SnowflakeClient

client = SnowflakeClient(
    api_key=os.environ.get('SNOWFLAKE_API_KEY')
)
```

## Resources
- [Snowflake Documentation](https://docs.snowflake.com)
- [Snowflake Dashboard](https://api.snowflake.com)
- [Snowflake Status](https://status.snowflake.com)

## Next Steps
After successful auth, proceed to `snowflake-hello-world` for your first API call.