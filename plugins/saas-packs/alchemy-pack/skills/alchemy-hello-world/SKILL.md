---
name: alchemy-hello-world
description: |
  Create a minimal working Alchemy example.
  Use when starting a new Alchemy integration, testing your setup,
  or learning basic Alchemy API patterns.
  Trigger with phrases like "alchemy hello world", "alchemy example",
  "alchemy quick start", "simple alchemy code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, alchemy]
---

# Alchemy Hello World

## Overview

Check your account balance and list recent transactions via Alchemy.


## Prerequisites
- Completed `alchemy-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { AlchemyClient } from '@alchemy/sdk';

const client = new AlchemyClient({

  apiKey: process.env.ALCHEMY_API_KEY,

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
- Working code file with Alchemy client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Alchemy connection is working.
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
import { AlchemyClient } from '@alchemy/sdk';

const client = new AlchemyClient({

  apiKey: process.env.ALCHEMY_API_KEY,

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
from alchemy import AlchemyClient

client = AlchemyClient()

account = client.accounts.get()
print(f"Account: {account.name}")
print(f"Balance: ${account.balance / 100:.2f} {account.currency}")

```

## Resources
- [Alchemy Getting Started](https://docs.alchemy.com/getting-started)
- [Alchemy API Reference](https://docs.alchemy.com/api)
- [Alchemy Examples](https://docs.alchemy.com/examples)

## Next Steps
Proceed to `alchemy-local-dev-loop` for development workflow setup.