---
name: palantir-install-auth
description: |
  Install and configure Palantir SDK/CLI authentication.
  Use when setting up a new Palantir integration, configuring API keys,
  or initializing Palantir in your project.
  Trigger with phrases like "install palantir", "setup palantir",
  "palantir auth", "configure palantir API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, palantir]
---

# Palantir Install & Auth

## Overview
Set up Palantir SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Palantir account with API access

- Database connection string or API key from Palantir dashboard
- Network access to database host (check firewall/VPC rules)


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @palantir/sdk

# Python
pip install palantir
```

### Step 2: Configure Authentication

```bash
# Set connection string (preferred for database platforms)
export PALANTIR_DATABASE_URL="postgresql://user:pass@host:5432/db"

# Or use API key
export PALANTIR_API_KEY="your-api-key"

# Or create .env file
cat >> .env << 'EOF'
PALANTIR_DATABASE_URL=postgresql://user:pass@host:5432/db
PALANTIR_API_KEY=your-api-key
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
| Authentication Failed | Wrong password or expired credentials | Reset credentials in Palantir dashboard |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { PalantirClient } from '@palantir/sdk';

const client = new PalantirClient({

  connectionString: process.env.PALANTIR_DATABASE_URL,

});
```

### Python Setup
```python
from palantir import PalantirClient

client = PalantirClient(

    connection_string=os.environ.get('PALANTIR_DATABASE_URL')

)
```

## Resources
- [Palantir Documentation](https://docs.palantir.com)
- [Palantir Dashboard](https://api.palantir.com)
- [Palantir Status](https://status.palantir.com)

## Next Steps
After successful auth, proceed to `palantir-hello-world` for your first API call.