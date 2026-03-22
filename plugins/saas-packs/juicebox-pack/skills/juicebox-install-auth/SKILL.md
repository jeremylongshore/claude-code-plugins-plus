---
name: juicebox-install-auth
description: |
  Install and configure Juicebox PeopleGPT API authentication.
  Use when setting up people search or initializing Juicebox.
  Trigger: "install juicebox", "setup juicebox", "juicebox auth".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, recruiting, juicebox]
compatible-with: claude-code
---

# Juicebox Install & Auth

## Overview
Set up Juicebox PeopleGPT API for AI-powered people search across 800M+ professional profiles.

## Prerequisites
- Juicebox account at [app.juicebox.ai](https://app.juicebox.ai)
- API key from Dashboard > Settings > API Keys
- Node.js 18+ or Python 3.8+

## Instructions

### Step 1: Install SDK
```bash
npm install @juicebox/sdk
# or: pip install juicebox-sdk
```

### Step 2: Configure Authentication
```bash
export JUICEBOX_API_KEY="jb_live_..."
echo 'JUICEBOX_API_KEY=jb_live_your-key' >> .env
```

### Step 3: Verify Connection
```typescript
import { JuiceboxClient } from '@juicebox/sdk';
const client = new JuiceboxClient({ apiKey: process.env.JUICEBOX_API_KEY });

const results = await client.search({ query: 'engineer', limit: 1 });
console.log(`Connected! ${results.total} profiles available`);
```

```python
from juicebox import JuiceboxClient
client = JuiceboxClient(api_key=os.environ['JUICEBOX_API_KEY'])
results = client.search(query='engineer', limit=1)
print(f'Connected! {results.total} profiles')
```

## Error Handling
| Error | Code | Solution |
|-------|------|----------|
| Invalid API key | 401 | Verify at app.juicebox.ai/settings |
| Plan limit exceeded | 403 | Upgrade plan or check quota |
| Rate limited | 429 | Check `Retry-After` header |

## Resources
- [Juicebox Docs](https://docs.juicebox.work)
- [PeopleGPT](https://juicebox.ai/peoplegpt)

## Next Steps
After auth, proceed to `juicebox-hello-world`.
