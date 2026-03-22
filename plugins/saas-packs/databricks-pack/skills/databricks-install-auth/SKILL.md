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

- Database connection string or API key from Databricks dashboard
- Network access to database host (check firewall/VPC rules)


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
# Set connection string (preferred for database platforms)
export DATABRICKS_DATABASE_URL="postgresql://user:pass@host:5432/db"

# Or use API key
export DATABRICKS_API_KEY="your-api-key"

# Or create .env file
cat >> .env << 'EOF'
DATABRICKS_DATABASE_URL=postgresql://user:pass@host:5432/db
DATABRICKS_API_KEY=your-api-key
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
| Authentication Failed | Wrong password or expired credentials | Reset credentials in Databricks dashboard |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { DatabricksClient } from '@databricks/sdk';

const client = new DatabricksClient({

  connectionString: process.env.DATABRICKS_DATABASE_URL,

});
```

### Python Setup
```python
from databricks import DatabricksClient

client = DatabricksClient(

    connection_string=os.environ.get('DATABRICKS_DATABASE_URL')

)
```

## Resources
- [Databricks Documentation](https://docs.databricks.com)
- [Databricks Dashboard](https://api.databricks.com)
- [Databricks Status](https://status.databricks.com)

## Next Steps
After successful auth, proceed to `databricks-hello-world` for your first API call.