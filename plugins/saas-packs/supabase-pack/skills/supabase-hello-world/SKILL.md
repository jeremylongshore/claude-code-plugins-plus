---
name: supabase-hello-world
description: |
  Create a minimal working Supabase example.
  Use when starting a new Supabase integration, testing your setup,
  or learning basic Supabase API patterns.
  Trigger with phrases like "supabase hello world", "supabase example",
  "supabase quick start", "simple supabase code".
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
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { SupabaseClient } from '@supabase/supabase-js';

const client = new SupabaseClient({
  apiKey: process.env.SUPABASE_API_KEY,
});
```

### Step 3: Make Your First API Call
```typescript
async function main() {
  const result = await supabase.from('todos').insert({ task: 'Hello!' }).select(); console.log(result.data);
}

main().catch(console.error);
```

## Output
- Working code file with Supabase client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Supabase connection is working.
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Import Error | SDK not installed | Verify with `npm list` or `pip show` |
| Auth Error | Invalid credentials | Check environment variable is set |
| Timeout | Network issues | Increase timeout or check connectivity |
| Rate Limit | Too many requests | Wait and retry with exponential backoff |

## Examples

### TypeScript Example
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

### Python Example
```python
from supabase import SupabaseClient

client = SupabaseClient()

response = supabase.table('todos').insert({'task': 'Hello!'}).execute(); print(response.data)
```

## Resources
- [Supabase Getting Started](https://supabase.com/docs/getting-started)
- [Supabase API Reference](https://supabase.com/docs/api)
- [Supabase Examples](https://supabase.com/docs/examples)

## Next Steps
Proceed to `supabase-local-dev-loop` for development workflow setup.