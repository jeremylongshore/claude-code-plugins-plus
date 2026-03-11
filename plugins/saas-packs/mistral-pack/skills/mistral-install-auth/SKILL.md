---
name: mistral-install-auth
description: |
  Install and configure Mistral AI SDK/CLI authentication.
  Use when setting up a new Mistral integration, configuring API keys,
  or initializing Mistral AI in your project.
  Trigger with phrases like "install mistral", "setup mistral",
  "mistral auth", "configure mistral API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Mistral AI Install & Auth

## Overview
Set up Mistral AI SDK and configure authentication credentials for chat completions, embeddings, and function calling.

## Prerequisites
- Node.js 18+ or Python 3.9+
- Package manager (npm, pnpm, yarn, or pip)
- Mistral AI account with API access
- API key from Mistral AI console (https://console.mistral.ai/)

## Instructions

### Step 1: Install SDK

**Node.js (TypeScript/JavaScript)**
```bash
set -euo pipefail
# npm
npm install @mistralai/mistralai

# pnpm
pnpm add @mistralai/mistralai

# yarn
yarn add @mistralai/mistralai
```

**Python**
```bash
set -euo pipefail
pip install mistralai
```

### Step 2: Configure Authentication

**Environment Variables (Recommended)**
```bash
# Set environment variable
export MISTRAL_API_KEY="your-api-key"

# Or create .env file
echo 'MISTRAL_API_KEY=your-api-key' >> .env
```

**Using dotenv (Node.js)**
```bash
set -euo pipefail
npm install dotenv
```

```typescript
import 'dotenv/config';
```

### Step 3: Verify Connection

**TypeScript**
```typescript
import Mistral from '@mistralai/mistralai';

const client = new Mistral({
  apiKey: process.env.MISTRAL_API_KEY,
});

async function testConnection() {
  try {
    const models = await client.models.list();
    console.log('Connection successful! Available models:');
    models.data?.forEach(model => console.log(`  - ${model.id}`));
  } catch (error) {
    console.error('Connection failed:', error);
  }
}

testConnection();
```

**Python**
```python
import os
from mistralai import Mistral

client = Mistral(api_key=os.environ.get("MISTRAL_API_KEY"))

def test_connection():
    try:
        models = client.models.list()
        print("Connection successful! Available models:")
        for model in models.data:
            print(f"  - {model.id}")
    except Exception as e:
        print(f"Connection failed: {e}")

test_connection()
```

## Output
- Installed SDK package in node_modules or site-packages
- Environment variable or .env file with API key
- Successful connection verification showing available models

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid or missing API key | Verify key at console.mistral.ai |
| 429 Too Many Requests | Rate limit exceeded | Implement backoff, check quota |
| Network Error | Firewall or connectivity | Ensure HTTPS to api.mistral.ai allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Client Initialization
```typescript
import Mistral from '@mistralai/mistralai';

const client = new Mistral({
  apiKey: process.env.MISTRAL_API_KEY,
  // Optional: custom timeout
  timeout: 30000,  # 30000: 30 seconds in ms
});

export default client;
```

### Python Client Initialization
```python
import os
from mistralai import Mistral

client = Mistral(
    api_key=os.environ.get("MISTRAL_API_KEY"),
    # Optional: custom timeout
    timeout=30.0,
)
```

### Validate API Key Format
```typescript
function validateMistralApiKey(key: string): boolean {
  // Mistral API keys are UUIDs or specific format
  return key.length > 20 && !key.includes(' ');
}
```

## Resources
- [Mistral AI Documentation](https://docs.mistral.ai/)
- [Mistral AI Console](https://console.mistral.ai/)
- [Mistral AI API Reference](https://docs.mistral.ai/api/)
- [GitHub: mistralai-client-js](https://github.com/mistralai/client-js)
- [GitHub: mistralai-client-python](https://github.com/mistralai/client-python)

## Next Steps
After successful auth, proceed to `mistral-hello-world` for your first chat completion.