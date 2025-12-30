---
name: supabase-install-auth
description: |
  Install and configure Supabase SDK/CLI authentication.
  Use when setting up a new Supabase integration, configuring API keys,
  or initializing Supabase in your project.
  Trigger with phrases like "install supabase", "setup supabase",
  "supabase auth", "configure supabase API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Install & Auth

## Overview
Set up Supabase SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Supabase account with API access
- API key from Supabase dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @supabase/supabase-js

# Python
pip install supabase
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export SUPABASE_API_KEY="your-api-key"

# Or create .env file
echo 'SUPABASE_API_KEY=your-api-key' >> .env
```

### Step 3: Verify Connection
```typescript
const result = await supabase.from('_test').select('*').limit(1); console.log(result.error ? 'Failed' : 'OK');
```

## Output
- Installed SDK package in node_modules or site-packages
- Environment variable or .env file with API key
- Successful connection verification output

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Invalid API Key | Incorrect or expired key | Verify key in Supabase dashboard |
| Rate Limited | Exceeded quota | Check quota at https://supabase.com/docs |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { SupabaseClient } from '@supabase/supabase-js';

const client = new SupabaseClient({
  apiKey: process.env.SUPABASE_API_KEY,
});
```

### Python Setup
```python
from supabase import SupabaseClient

client = SupabaseClient(
    api_key=os.environ.get('SUPABASE_API_KEY')
)
```

## Resources
- [Supabase Documentation](https://supabase.com/docs)
- [Supabase Dashboard](https://api.supabase.com)
- [Supabase Status](https://status.supabase.com)

## Next Steps
After successful auth, proceed to `supabase-hello-world` for your first API call.