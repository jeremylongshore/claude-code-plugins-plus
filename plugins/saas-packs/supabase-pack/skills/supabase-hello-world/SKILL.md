---
name: supabase-hello-world
description: |
  Supabase hello world example - minimal working code. Trigger phrases:
  "supabase hello world", "supabase example", "supabase quick start",
  "simple supabase code", "basic supabase usage".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Hello World

## Overview
Minimal working example demonstrating core Supabase functionality.

## Prerequisites
- Completed `supabase-install-auth` setup
- Valid API credentials configured

## Hello World Example

### TypeScript
```typescript
import { SupabaseClient } from '@supabase/supabase-js';

const client = new SupabaseClient({
  apiKey: process.env.SUPABASE_API_KEY,
});

async function main() {
  const result = await supabase.from('todos').insert({ task: 'Hello!' }).select(); console.log(result.data);
}

main().catch(console.error);
```

### Python
```python
from supabase import SupabaseClient

client = SupabaseClient()

response = supabase.table('todos').insert({'task': 'Hello!'}).execute(); print(response.data)
```

## Expected Output
```
Success! Your Supabase connection is working.
```

## Troubleshooting
- **Import Error**: Verify SDK installation with `npm list` or `pip show`
- **Auth Error**: Check environment variable is set correctly
- **Timeout**: Increase timeout or check network connectivity

## Next Steps
Proceed to `supabase-local-dev-loop` for development workflow setup.