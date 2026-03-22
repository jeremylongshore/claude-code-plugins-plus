---
name: quicknode-hello-world
description: |
  Create a minimal working QuickNode example.
  Use when starting a new QuickNode integration, testing your setup,
  or learning basic QuickNode API patterns.
  Trigger with phrases like "quicknode hello world", "quicknode example",
  "quicknode quick start", "simple quicknode code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, quicknode]
---

# QuickNode Hello World

## Overview

Check your account balance and list recent transactions via QuickNode.


## Prerequisites
- Completed `quicknode-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { QuickNodeClient } from '@quicknode/sdk';

const client = new QuickNodeClient({

  apiKey: process.env.QUICKNODE_API_KEY,

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
- Working code file with QuickNode client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your QuickNode connection is working.
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
import { QuickNodeClient } from '@quicknode/sdk';

const client = new QuickNodeClient({

  apiKey: process.env.QUICKNODE_API_KEY,

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
from quicknode import QuickNodeClient

client = QuickNodeClient()

account = client.accounts.get()
print(f"Account: {account.name}")
print(f"Balance: ${account.balance / 100:.2f} {account.currency}")

```

## Resources
- [QuickNode Getting Started](https://docs.quicknode.com/getting-started)
- [QuickNode API Reference](https://docs.quicknode.com/api)
- [QuickNode Examples](https://docs.quicknode.com/examples)

## Next Steps
Proceed to `quicknode-local-dev-loop` for development workflow setup.