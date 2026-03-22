---
name: groq-install-auth
description: |
  Install and configure Groq SDK authentication for TypeScript or Python.
  Use when setting up a new Groq integration, configuring API keys,
  or initializing the groq-sdk in your project.
  Trigger with phrases like "install groq", "setup groq",
  "groq auth", "configure groq API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, groq, api, authentication]

---
# Groq Install & Auth

## Overview
Install the official Groq SDK and configure API key authentication. Groq provides ultra-fast LLM inference on custom LPU hardware through an OpenAI-compatible REST API at `api.groq.com/openai/v1/`.

## Prerequisites
- Node.js 18+ or Python 3.8+
- Package manager (npm, pnpm, or pip)
- Groq account at [console.groq.com](https://console.groq.com)
- API key from GroqCloud console (Settings > API Keys)

## Instructions

### Step 1: Install the SDK
```bash
set -euo pipefail
# TypeScript / JavaScript
npm install groq-sdk

# Python
pip install groq
```

### Step 2: Get Your API Key
1. Go to [console.groq.com/keys](https://console.groq.com/keys)
2. Click "Create API Key"
3. Copy the key (starts with `gsk_`)
4. Store it securely -- you cannot view it again

### Step 3: Configure Environment
```bash
# Set environment variable (recommended)
export GROQ_API_KEY="gsk_your_key_here"

# Or create .env file (add .env to .gitignore first)
echo 'GROQ_API_KEY=gsk_your_key_here' >> .env
```

### Step 4: Verify Connection (TypeScript)
```typescript
import Groq from "groq-sdk";

const groq = new Groq({
  apiKey: process.env.GROQ_API_KEY,
});

async function verify() {
  const models = await groq.models.list();
  console.log("Connected! Available models:");
  for (const model of models.data) {
    console.log(`  ${model.id} (owned by ${model.owned_by})`);
  }
}

verify().catch(console.error);
```

### Step 5: Verify Connection (Python)
```python
import os
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

models = client.models.list()
print("Connected! Available models:")
for model in models.data:
    print(f"  {model.id} (owned by {model.owned_by})")
```

## SDK Defaults
The Groq SDK auto-reads `GROQ_API_KEY` from environment if no `apiKey` is passed to the constructor. Additional constructor options:

```typescript
const groq = new Groq({
  apiKey: process.env.GROQ_API_KEY,  // Optional if env var set
  baseURL: "https://api.groq.com/openai/v1",  // Default
  maxRetries: 2,      // Default retry count
  timeout: 60_000,    // 60 second timeout (ms)
});
```

## API Key Formats
| Prefix | Type | Usage |
|--------|------|-------|
| `gsk_` | Standard API key | All API endpoints |

Groq uses a single key type. There are no separate read/write scopes -- all keys have full API access. Restrict access through organizational controls in the console.

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `401 Invalid API Key` | Key missing, revoked, or mistyped | Verify key at console.groq.com/keys |
| `MODULE_NOT_FOUND groq-sdk` | SDK not installed | Run `npm install groq-sdk` |
| `ModuleNotFoundError: No module named 'groq'` | Python SDK missing | Run `pip install groq` |
| `ENOTFOUND api.groq.com` | Network/DNS issue | Check internet connectivity and firewall |

## .gitignore Template
```
# Groq secrets
.env
.env.local
.env.*.local
```

## Resources
- [Groq Quickstart](https://console.groq.com/docs/quickstart)
- [Groq API Reference](https://console.groq.com/docs/api-reference)
- [groq-sdk on npm](https://www.npmjs.com/package/groq-sdk)
- [groq-typescript on GitHub](https://github.com/groq/groq-typescript)

## Next Steps
After successful auth, proceed to `groq-hello-world` for your first chat completion.
