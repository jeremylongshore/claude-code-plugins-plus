---
name: supabase-install-auth
description: |
  Install and configure Supabase SDK/CLI with authentication.
  Use when setting up Supabase integration for the first time.
  Trigger with phrases like "install supabase", "setup supabase",
  "supabase auth", "configure supabase API key".
allowed-tools: Read, Write, Bash(supabase:*), Grep
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
- SDK installed in `node_modules/` or Python site-packages
- Environment variable `SUPABASE_API_KEY` configured
- Successful connection test confirming API access

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Invalid API Key | Key not found or expired | Verify key in Supabase dashboard |
| Rate Limited | Exceeded API quota | Check limits at https://supabase.com/docs |
| Network Error | Firewall blocking | Ensure outbound HTTPS (443) allowed |
| Module Not Found | SDK not installed | Run `npm install @supabase/supabase-js` |

## Examples

### Basic Setup (TypeScript)
```typescript
import { SupabaseClient } from '@supabase/supabase-js';

const client = new SupabaseClient({
  apiKey: process.env.SUPABASE_API_KEY
});
```

### Basic Setup (Python)
```python
import os
from supabase import SupabaseClient

client = SupabaseClient(
    api_key=os.environ.get('SUPABASE_API_KEY')
)
```

## Resources
- [Supabase Documentation](https://supabase.com/docs)
- [API Reference](https://docs.supabase.com/api)
- [SDK Repository](https://github.com/supabase/supabase-sdk)

## Next Steps
After successful auth, proceed to `supabase-hello-world` for your first API call.