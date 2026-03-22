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

- Database connection string or API key from ClickHouse dashboard
- Network access to database host (check firewall/VPC rules)


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
# Set connection string (preferred for database platforms)
export CLICKHOUSE_DATABASE_URL="postgresql://user:pass@host:5432/db"

# Or use API key
export CLICKHOUSE_API_KEY="your-api-key"

# Or create .env file
cat >> .env << 'EOF'
CLICKHOUSE_DATABASE_URL=postgresql://user:pass@host:5432/db
CLICKHOUSE_API_KEY=your-api-key
EOF
```


### Step 3: Verify Connection
```typescript
const tables = await client.query("SELECT table_name FROM information_schema.tables LIMIT 5");
console.log(`Connected — ${tables.rows.length} tables found`);

```

## Output
- Installed SDK package in node_modules or site-packages

- Connection string or API key configured in environment
- Successful query execution confirming database connectivity


## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|

| Connection Refused | Wrong host/port or firewall blocking | Check connection string, verify network access |
| Authentication Failed | Wrong password or expired credentials | Reset credentials in ClickHouse dashboard |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { ClickHouseClient } from '@clickhouse/sdk';

const client = new ClickHouseClient({

  connectionString: process.env.CLICKHOUSE_DATABASE_URL,

});
```

### Python Setup
```python
from clickhouse import ClickHouseClient

client = ClickHouseClient(

    connection_string=os.environ.get('CLICKHOUSE_DATABASE_URL')

)
```

## Resources
- [ClickHouse Documentation](https://docs.clickhouse.com)
- [ClickHouse Dashboard](https://api.clickhouse.com)
- [ClickHouse Status](https://status.clickhouse.com)

## Next Steps
After successful auth, proceed to `clickhouse-hello-world` for your first API call.