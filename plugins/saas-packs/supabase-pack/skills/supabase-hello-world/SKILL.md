---
name: supabase-hello-world
description: |
  Create a minimal working Supabase integration example.
  Use when testing Supabase connection or learning the basics.
  Trigger with phrases like "supabase hello world", "test supabase",
  "supabase example", "simple supabase code".
allowed-tools: Read, Write, Edit, Bash(supabase:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Hello World

## Overview
Minimal working example demonstrating core Supabase functionality.

## Prerequisites
- Completed `supabase-install-auth` setup
- Valid API credentials configured in environment
- Node.js 18+ or Python 3.10+

## Instructions

### Step 1: Create Test File
Create a new file named `supabase-test.ts` (or `.py` for Python):

### Step 2: Add Hello World Code

#### TypeScript
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

#### Python
```python
from supabase import SupabaseClient

client = SupabaseClient()

response = supabase.table('todos').insert({'task': 'Hello!'}).execute(); print(response.data)
```

### Step 3: Run the Test
```bash
# TypeScript
npx ts-node supabase-test.ts

# Python
python supabase-test.py
```

## Output
```
Success! Your Supabase connection is working.
```

Expected results:
- Console output showing successful API response
- No authentication errors
- Response data from Supabase API

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Import Error | SDK not installed | Run `npm install @supabase/supabase-js` |
| Auth Error | Invalid API key | Check `SUPABASE_API_KEY` in environment |
| Timeout | Network issue | Increase timeout or check connectivity |
| Rate Limit | Too many requests | Wait and retry with backoff |

## Examples

### Extended Hello World (TypeScript)
```typescript
import { SupabaseClient } from '@supabase/supabase-js';

const client = new SupabaseClient({
  apiKey: process.env.SUPABASE_API_KEY,
});

async function main() {
  try {
    const result = await client.test();
    console.log('✅ Connection successful');
    console.log('Response:', JSON.stringify(result, null, 2));
  } catch (error) {
    console.error('❌ Connection failed:', error.message);
    process.exit(1);
  }
}

main();
```

## Resources
- [Supabase Quickstart Guide](https://supabase.com/docs/quickstart)
- [API Examples](https://supabase.com/docs/examples)
- [SDK Documentation](https://docs.supabase.com/sdk)

## Next Steps
Proceed to `supabase-local-dev-loop` for development workflow setup.