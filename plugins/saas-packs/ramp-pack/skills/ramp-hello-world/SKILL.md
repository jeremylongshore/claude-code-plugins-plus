---
name: ramp-hello-world
description: |
  Create a minimal working Ramp example.
  Use when starting a new Ramp integration, testing your setup,
  or learning basic Ramp API patterns.
  Trigger with phrases like "ramp hello world", "ramp example",
  "ramp quick start", "simple ramp code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, ramp]
---

# Ramp Hello World

## Overview

Check your account balance and list recent transactions via Ramp.


## Prerequisites
- Completed `ramp-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { RampClient } from '@ramp/sdk';

const client = new RampClient({

  apiKey: process.env.RAMP_API_KEY,

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
- Working code file with Ramp client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Ramp connection is working.
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
import { RampClient } from '@ramp/sdk';

const client = new RampClient({

  apiKey: process.env.RAMP_API_KEY,

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
from ramp import RampClient

client = RampClient()

account = client.accounts.get()
print(f"Account: {account.name}")
print(f"Balance: ${account.balance / 100:.2f} {account.currency}")

```

## Resources
- [Ramp Getting Started](https://docs.ramp.com/getting-started)
- [Ramp API Reference](https://docs.ramp.com/api)
- [Ramp Examples](https://docs.ramp.com/examples)

## Next Steps
Proceed to `ramp-local-dev-loop` for development workflow setup.