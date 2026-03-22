---
name: speak-install-auth
description: |
  Install and configure Speak SDK/CLI authentication.
  Use when setting up a new Speak integration, configuring API keys,
  or initializing Speak in your project.
  Trigger with phrases like "install speak", "setup speak",
  "speak auth", "configure speak API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, speak]
---

# Speak Install & Auth

## Overview
Set up Speak SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Speak account with API access

- API key from Speak dashboard (starts with `sk-` or similar prefix)


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @speak/sdk

# Python
pip install speak
```

### Step 2: Configure Authentication

```bash
# Set environment variable
export SPEAK_API_KEY="your-api-key"

# Or create .env file
echo 'SPEAK_API_KEY=your-api-key' >> .env
```


### Step 3: Verify Connection
```typescript
const models = await client.models.list();
console.log(`Connected — ${models.data.length} models available`);

```

## Output
- Installed SDK package in node_modules or site-packages

- Environment variable or .env file with API key
- Successful connection verification output


## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|

| Invalid API Key | Key is missing, expired, or has extra whitespace | Verify key in Speak dashboard. Check for trailing newlines |
| Rate Limited | Exceeded requests/tokens per minute | Check usage at https://docs.speak.com/usage |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { SpeakClient } from '@speak/sdk';

const client = new SpeakClient({

  apiKey: process.env.SPEAK_API_KEY,

});
```

### Python Setup
```python
from speak import SpeakClient

client = SpeakClient(

    api_key=os.environ.get('SPEAK_API_KEY')

)
```

## Resources
- [Speak Documentation](https://docs.speak.com)
- [Speak Dashboard](https://api.speak.com)
- [Speak Status](https://status.speak.com)

## Next Steps
After successful auth, proceed to `speak-hello-world` for your first API call.