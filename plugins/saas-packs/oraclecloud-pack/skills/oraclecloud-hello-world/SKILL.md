---
name: oraclecloud-hello-world
description: |
  Create a minimal working Oracle Cloud example.
  Use when starting a new Oracle Cloud integration, testing your setup,
  or learning basic Oracle Cloud API patterns.
  Trigger with phrases like "oraclecloud hello world", "oraclecloud example",
  "oraclecloud quick start", "simple oraclecloud code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, oraclecloud]
---

# Oracle Cloud Hello World

## Overview
Minimal working example demonstrating core Oracle Cloud functionality.

## Prerequisites
- Completed `oraclecloud-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { OracleCloudClient } from '@oraclecloud/sdk';

const client = new OracleCloudClient({
  apiKey: process.env.ORACLECLOUD_API_KEY,
});
```

### Step 3: Make Your First API Call
```typescript
async function main() {
  // Your first API call here
}

main().catch(console.error);
```

## Output
- Working code file with Oracle Cloud client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Oracle Cloud connection is working.
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
import { OracleCloudClient } from '@oraclecloud/sdk';

const client = new OracleCloudClient({
  apiKey: process.env.ORACLECLOUD_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from oraclecloud import OracleCloudClient

client = OracleCloudClient()

# Your first API call here
```

## Resources
- [Oracle Cloud Getting Started](https://docs.oraclecloud.com/getting-started)
- [Oracle Cloud API Reference](https://docs.oraclecloud.com/api)
- [Oracle Cloud Examples](https://docs.oraclecloud.com/examples)

## Next Steps
Proceed to `oraclecloud-local-dev-loop` for development workflow setup.