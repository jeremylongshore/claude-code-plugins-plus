---
name: clickhouse-install-auth
description: |
  Install and configure ClickHouse SDK/CLI authentication.
  Use when setting up a new ClickHouse integration, configuring API keys,
  or initializing ClickHouse in your project.
  Trigger with phrases like "install clickhouse", "setup clickhouse",
  "clickhouse auth", "configure clickhouse API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, clickhouse]
---

# ClickHouse Install & Auth

## Overview
Set up ClickHouse SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- ClickHouse account with API access
- API key from ClickHouse dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @clickhouse/sdk

# Python
pip install clickhouse
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export CLICKHOUSE_API_KEY="your-api-key"

# Or create .env file
echo 'CLICKHOUSE_API_KEY=your-api-key' >> .env
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
| Invalid API Key | Incorrect or expired key | Verify key in ClickHouse dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.clickhouse.com |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { ClickHouseClient } from '@clickhouse/sdk';

const client = new ClickHouseClient({
  apiKey: process.env.CLICKHOUSE_API_KEY,
});
```

### Python Setup
```python
from clickhouse import ClickHouseClient

client = ClickHouseClient(
    api_key=os.environ.get('CLICKHOUSE_API_KEY')
)
```

## Resources
- [ClickHouse Documentation](https://docs.clickhouse.com)
- [ClickHouse Dashboard](https://api.clickhouse.com)
- [ClickHouse Status](https://status.clickhouse.com)

## Next Steps
After successful auth, proceed to `clickhouse-hello-world` for your first API call.