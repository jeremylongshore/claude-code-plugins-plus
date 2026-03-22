---
name: exa-install-auth
description: |
  Install the exa-js SDK and configure API key authentication.
  Use when setting up a new Exa integration, configuring API keys,
  or initializing Exa in a Node.js/Python project.
  Trigger with phrases like "install exa", "setup exa",
  "exa auth", "configure exa API key", "exa-js".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, exa, api, authentication, setup]

---
# Exa Install & Auth

## Overview
Install the official Exa SDK and configure API key authentication. Exa is a neural search API at `api.exa.ai` that retrieves web content using semantic similarity. Authentication uses the `x-api-key` header. The SDK is `exa-js` on npm or `exa-py` on PyPI.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, yarn, or pip)
- Exa account at [dashboard.exa.ai](https://dashboard.exa.ai)
- API key from the Exa dashboard

## Instructions

### Step 1: Install the SDK

**Node.js (exa-js)**
```bash
set -euo pipefail
npm install exa-js
# or
pnpm add exa-js
```

**Python (exa-py)**
```bash
pip install exa-py
```

### Step 2: Configure the API Key

```bash
# Set environment variable
export EXA_API_KEY="your-api-key-here"

# Or create .env file (add .env to .gitignore first)
echo 'EXA_API_KEY=your-api-key-here' >> .env
```

Add to `.gitignore`:
```
.env
.env.local
.env.*.local
```

### Step 3: Initialize the Client

**TypeScript**
```typescript
import Exa from "exa-js";

const exa = new Exa(process.env.EXA_API_KEY);
```

**Python**
```python
from exa_py import Exa
import os

exa = Exa(api_key=os.environ["EXA_API_KEY"])
```

### Step 4: Verify Connection
```typescript
import Exa from "exa-js";

const exa = new Exa(process.env.EXA_API_KEY);

async function verifyConnection() {
  try {
    const result = await exa.search("test connectivity", { numResults: 1 });
    console.log("Connected. Results:", result.results.length);
    console.log("First result:", result.results[0]?.title);
  } catch (err: any) {
    if (err.status === 401) {
      console.error("Invalid API key. Check EXA_API_KEY.");
    } else if (err.status === 402) {
      console.error("No credits remaining. Top up at dashboard.exa.ai.");
    } else {
      console.error("Connection failed:", err.message);
    }
  }
}

verifyConnection();
```

## Output
- `exa-js` or `exa-py` installed in project dependencies
- `EXA_API_KEY` environment variable configured
- `.env` added to `.gitignore`
- Successful search result confirming connectivity

## Error Handling
| Error | HTTP Code | Cause | Solution |
|-------|-----------|-------|----------|
| `INVALID_API_KEY` | 401 | Missing or invalid API key | Verify key at dashboard.exa.ai |
| `NO_MORE_CREDITS` | 402 | Account balance exhausted | Top up credits in dashboard |
| `MODULE_NOT_FOUND` | N/A | SDK not installed | Run `npm install exa-js` |
| `ENOTFOUND` | N/A | Network unreachable | Check internet connectivity |
| `API_KEY_BUDGET_EXCEEDED` | 402 | Spending limit reached | Increase budget in dashboard |

## Examples

### With dotenv (Node.js)
```typescript
import "dotenv/config";
import Exa from "exa-js";

const exa = new Exa(process.env.EXA_API_KEY);
```

### With Validation
```typescript
function createExaClient(): Exa {
  const apiKey = process.env.EXA_API_KEY;
  if (!apiKey) {
    throw new Error(
      "EXA_API_KEY not set. Get one at https://dashboard.exa.ai"
    );
  }
  return new Exa(apiKey);
}
```

## Resources
- [Exa Dashboard](https://dashboard.exa.ai)
- [Exa Getting Started](https://docs.exa.ai/reference/getting-started)
- [exa-js on npm](https://www.npmjs.com/package/exa-js)
- [exa-py on PyPI](https://pypi.org/project/exa-py/)

## Next Steps
After successful auth, proceed to `exa-hello-world` for your first search.
