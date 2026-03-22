---
name: together-install-auth
description: |
  Install Together AI SDK and configure API key for inference and fine-tuning.
  Use when setting up Together AI, configuring the OpenAI-compatible API,
  or initializing the together Python package.
  Trigger: "install together, setup together ai, together API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, inference, together]
compatible-with: claude-code
---

# Together AI Install & Auth

## Overview

Together AI provides an OpenAI-compatible API for open-source model inference and fine-tuning. Base URL: `https://api.together.xyz/v1`. Works with the official `together` Python SDK or any OpenAI-compatible client.

## Prerequisites

- Together AI account at [api.together.xyz](https://api.together.xyz)
- API key from Settings > API Keys
- Python 3.8+ or Node.js 18+

## Instructions

### Step 1: Install SDK

```bash
# Python (official)
pip install together

# Node.js (use OpenAI SDK with custom base URL)
npm install openai
```

### Step 2: Configure API Key

```bash
# .env
TOGETHER_API_KEY=your-api-key-here
```

### Step 3: Verify Connection (Python)

```python
from together import Together

client = Together(api_key=os.environ["TOGETHER_API_KEY"])
response = client.chat.completions.create(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
    messages=[{"role": "user", "content": "Say hello"}],
    max_tokens=10,
)
print(f"Connected! Response: {response.choices[0].message.content}")
```

### Step 4: Verify with OpenAI Client (Node.js)

```typescript
import OpenAI from 'openai';

const client = new OpenAI({
  apiKey: process.env.TOGETHER_API_KEY,
  baseURL: 'https://api.together.xyz/v1',
});

const response = await client.chat.completions.create({
  model: 'meta-llama/Llama-3.3-70B-Instruct-Turbo',
  messages: [{ role: 'user', content: 'Say hello' }],
  max_tokens: 10,
});
console.log(`Connected! ${response.choices[0].message.content}`);
```

### Step 5: List Available Models

```python
models = client.models.list()
for m in models.data[:5]:
    print(f"{m.id} ({m.type})")
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid API key | Check key at api.together.xyz |
| `Model not found` | Wrong model ID | Use `client.models.list()` to verify |
| `ModuleNotFoundError` | SDK not installed | `pip install together` |
| `429 Too Many Requests` | Rate limit | Back off and retry |

## Resources

- [Together AI Docs](https://docs.together.ai/)
- [Quickstart](https://docs.together.ai/docs/quickstart)
- [OpenAI Compatibility](https://docs.together.ai/docs/openai-api-compatibility)
- [Supported Models](https://docs.together.ai/docs/inference-models)

## Next Steps

Proceed to `together-hello-world` for inference examples.
