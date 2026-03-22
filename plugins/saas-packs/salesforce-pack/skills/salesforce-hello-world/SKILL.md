---
name: salesforce-hello-world
description: |
  Create a minimal working Salesforce example.
  Use when starting a new Salesforce integration, testing your setup,
  or learning basic Salesforce API patterns.
  Trigger with phrases like "salesforce hello world", "salesforce example",
  "salesforce quick start", "simple salesforce code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, salesforce]
---

# Salesforce Hello World

## Overview

Pull your first contacts from Salesforce and display them.


## Prerequisites
- Completed `salesforce-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { SalesforceClient } from '@salesforce/sdk';

const client = new SalesforceClient({

  apiKey: process.env.SALESFORCE_API_KEY,

});
```

### Step 3: Make Your First API Call
```typescript
async function main() {
  const contacts = await client.contacts.list({ limit: 5 });
console.log(`Found ${contacts.total} contacts. First 5:`);
contacts.data.forEach(c => console.log(`  - ${c.name} <${c.email}> (${c.company})`));

}

main().catch(console.error);
```

## Output
- Working code file with Salesforce client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Salesforce connection is working.
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
import { SalesforceClient } from '@salesforce/sdk';

const client = new SalesforceClient({

  apiKey: process.env.SALESFORCE_API_KEY,

});

async function main() {
  const contacts = await client.contacts.list({ limit: 5 });
console.log(`Found ${contacts.total} contacts. First 5:`);
contacts.data.forEach(c => console.log(`  - ${c.name} <${c.email}> (${c.company})`));

}

main().catch(console.error);
```

### Python Example
```python
from salesforce import SalesforceClient

client = SalesforceClient()

contacts = client.contacts.list(limit=5)
print(f"Found {contacts.total} contacts. First 5:")
for c in contacts.data:
    print(f"  - {c.name} <{c.email}> ({c.company})")

```

## Resources
- [Salesforce Getting Started](https://docs.salesforce.com/getting-started)
- [Salesforce API Reference](https://docs.salesforce.com/api)
- [Salesforce Examples](https://docs.salesforce.com/examples)

## Next Steps
Proceed to `salesforce-local-dev-loop` for development workflow setup.