---
name: finta-hello-world
description: |
  Create a minimal working Finta example.
  Use when starting a new Finta integration, testing your setup,
  or learning basic Finta API patterns.
  Trigger with phrases like "finta hello world", "finta example",
  "finta quick start", "simple finta code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, finta]
---

# Finta Hello World

## Overview

Check your account balance and list recent transactions via Finta.


## Prerequisites
- Completed `finta-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { FintaClient } from '@finta/sdk';

const client = new FintaClient({

  apiKey: process.env.FINTA_API_KEY,

});
```

### Step 3: Make Your First API Call
```typescript
async function main() {
  const account = await client.accounts.get();
console.log(`Account: ${account.name}`);
console.log(`Balance: $${(account.balance / 100).toFixed(2)} ${account.currency}`);

}

main().catch(console.error);
```

## Output
- Working code file with Finta client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Finta connection is working.
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
import { FintaClient } from '@finta/sdk';

const client = new FintaClient({

  apiKey: process.env.FINTA_API_KEY,

});

async function main() {
  const account = await client.accounts.get();
console.log(`Account: ${account.name}`);
console.log(`Balance: $${(account.balance / 100).toFixed(2)} ${account.currency}`);

}

main().catch(console.error);
```

### Python Example
```python
from finta import FintaClient

client = FintaClient()

account = client.accounts.get()
print(f"Account: {account.name}")
print(f"Balance: ${account.balance / 100:.2f} {account.currency}")

```

## Resources
- [Finta Getting Started](https://docs.finta.com/getting-started)
- [Finta API Reference](https://docs.finta.com/api)
- [Finta Examples](https://docs.finta.com/examples)

## Next Steps
Proceed to `finta-local-dev-loop` for development workflow setup.