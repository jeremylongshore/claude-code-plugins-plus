---
name: mistral-install-auth
description: |
  Install and configure the Mistral AI SDK with authentication.
  Use when setting up a new Mistral integration, configuring API keys,
  or initializing Mistral AI in your project.
  Trigger with phrases like "install mistral", "setup mistral",
  "mistral auth", "configure mistral API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, mistral, api, authentication]

---
# Mistral AI Install & Auth

## Overview
Set up the official Mistral AI SDK (`@mistralai/mistralai` for TypeScript, `mistralai` for Python) and configure authentication for chat completions, embeddings, function calling, vision, and agents.

## Prerequisites
- Node.js 18+ or Python 3.9+
- Package manager (npm, pnpm, yarn, or pip)
- Mistral AI account at [console.mistral.ai](https://console.mistral.ai/)
- API key from La Plateforme (Settings > API Keys)

## Instructions

### Step 1: Install SDK

**Node.js (TypeScript/JavaScript) — ESM only**
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
# Set in shell
export MISTRAL_API_KEY="your-api-key"

# Or create .env file (add to .gitignore!)
echo 'MISTRAL_API_KEY=your-api-key' >> .env
echo '.env' >> .gitignore
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
import { Mistral } from '@mistralai/mistralai';

const client = new Mistral({
  apiKey: process.env.MISTRAL_API_KEY,
});

async function testConnection() {
  try {
    const models = await client.models.list();
    console.log('Connection successful! Available models:');
    for (const model of models.data ?? []) {
      console.log(`  - ${model.id}`);
    }
  } catch (error: any) {
    if (error.status === 401) {
      console.error('Invalid API key. Check your key at console.mistral.ai');
    } else {
      console.error('Connection failed:', error.message);
    }
  }
}

testConnection();
```

**Python**
```python
import os
from mistralai import Mistral

client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])

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

### Step 4: Production — Secret Manager

```typescript
// GCP Secret Manager (recommended for production)
import { SecretManagerServiceClient } from '@google-cloud/secret-manager';

const sm = new SecretManagerServiceClient();

async function getMistralKey(): Promise<string> {
  const [version] = await sm.accessSecretVersion({
    name: 'projects/my-project/secrets/mistral-api-key/versions/latest',
  });
  return version.payload?.data?.toString() ?? '';
}
```

```typescript
// AWS Secrets Manager alternative
import { SecretsManager } from '@aws-sdk/client-secrets-manager';

const sm = new SecretsManager({ region: 'us-east-1' });

async function getMistralKey(): Promise<string> {
  const { SecretString } = await sm.getSecretValue({
    SecretId: 'mistral/api-key',
  });
  return SecretString!;
}
```

## Output
- Installed SDK package (`@mistralai/mistralai` or `mistralai`)
- Environment variable or .env file with API key
- Successful connection verification listing available models

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid or missing API key | Verify key at console.mistral.ai |
| `Module not found` | SDK not installed | Run `npm install @mistralai/mistralai` |
| `ERR_REQUIRE_ESM` | Using CommonJS require | SDK is ESM-only; use `import` or dynamic `await import()` |
| Network Error | Firewall blocking HTTPS | Ensure outbound HTTPS to `api.mistral.ai` is allowed |

## Examples

### TypeScript Client with Retry
```typescript
import { Mistral } from '@mistralai/mistralai';

const client = new Mistral({
  apiKey: process.env.MISTRAL_API_KEY,
  timeoutMs: 30_000,
  maxRetries: 3,
});

export default client;
```

### Python Client with Retry
```python
import os
from mistralai import Mistral

client = Mistral(
    api_key=os.environ["MISTRAL_API_KEY"],
    timeout_ms=30_000,
    max_retries=3,
)
```

### Validate API Key Format
```typescript
function validateMistralApiKey(key: string): boolean {
  // Mistral keys are typically 32-char hex strings
  return /^[a-zA-Z0-9]{20,}$/.test(key);
}
```

## Resources
- [Mistral AI Documentation](https://docs.mistral.ai/)
- [Mistral AI Console](https://console.mistral.ai/)
- [TypeScript SDK (client-ts)](https://github.com/mistralai/client-ts)
- [Python SDK (client-python)](https://github.com/mistralai/client-python)
- [API Reference](https://docs.mistral.ai/api/)

## Next Steps
After successful auth, proceed to `mistral-hello-world` for your first chat completion.
