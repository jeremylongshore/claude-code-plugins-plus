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

- Database connection string or API key from Snowflake dashboard
- Network access to database host (check firewall/VPC rules)


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
# Set connection string (preferred for database platforms)
export SNOWFLAKE_DATABASE_URL="postgresql://user:pass@host:5432/db"

# Or use API key
export SNOWFLAKE_API_KEY="your-api-key"

# Or create .env file
cat >> .env << 'EOF'
SNOWFLAKE_DATABASE_URL=postgresql://user:pass@host:5432/db
SNOWFLAKE_API_KEY=your-api-key
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
| Authentication Failed | Wrong password or expired credentials | Reset credentials in Snowflake dashboard |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { SnowflakeClient } from '@snowflake/sdk';

const client = new SnowflakeClient({

  connectionString: process.env.SNOWFLAKE_DATABASE_URL,

});
```

### Python Setup
```python
from snowflake import SnowflakeClient

client = SnowflakeClient(

    connection_string=os.environ.get('SNOWFLAKE_DATABASE_URL')

)
```

## Resources
- [Snowflake Documentation](https://docs.snowflake.com)
- [Snowflake Dashboard](https://api.snowflake.com)
- [Snowflake Status](https://status.snowflake.com)

## Next Steps
After successful auth, proceed to `snowflake-hello-world` for your first API call.