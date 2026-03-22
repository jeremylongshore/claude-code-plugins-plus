---
name: perplexity-install-auth
description: |
  Install and configure Perplexity Sonar API authentication.
  Use when setting up a new Perplexity integration, configuring API keys,
  or initializing the OpenAI-compatible client for Perplexity.
  Trigger with phrases like "install perplexity", "setup perplexity",
  "perplexity auth", "configure perplexity API key", "perplexity sonar setup".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, perplexity, api, authentication]

---
# Perplexity Install & Auth

## Overview
Set up Perplexity Sonar API access using the OpenAI-compatible chat completions endpoint at `https://api.perplexity.ai`. Perplexity does not have a custom SDK -- you use the standard OpenAI client library pointed at Perplexity's base URL.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Perplexity account at [perplexity.ai](https://www.perplexity.ai)
- API key from [perplexity.ai/settings/api](https://www.perplexity.ai/settings/api)

## Instructions

### Step 1: Install OpenAI Client Library
```bash
set -euo pipefail
# Node.js / TypeScript
npm install openai

# Python
pip install openai
```

There is no `@perplexity/sdk` package. Perplexity uses the OpenAI wire format, so you use the official `openai` package with a custom `baseURL`.

### Step 2: Configure API Key
```bash
# Set environment variable
export PERPLEXITY_API_KEY="pplx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Or create .env file (add .env to .gitignore)
echo 'PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' >> .env
```

API keys start with `pplx-` and are generated at [perplexity.ai/settings/api](https://www.perplexity.ai/settings/api). You must add credits to your account before making API calls.

### Step 3: Verify Connection (TypeScript)
```typescript
import OpenAI from "openai";

const client = new OpenAI({
  apiKey: process.env.PERPLEXITY_API_KEY,
  baseURL: "https://api.perplexity.ai",
});

async function verify() {
  const response = await client.chat.completions.create({
    model: "sonar",
    messages: [{ role: "user", content: "What is 2+2?" }],
    max_tokens: 50,
  });
  console.log("Connected:", response.choices[0].message.content);
  console.log("Model:", response.model);
  console.log("Tokens used:", response.usage?.total_tokens);
}

verify().catch(console.error);
```

### Step 4: Verify Connection (Python)
```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["PERPLEXITY_API_KEY"],
    base_url="https://api.perplexity.ai",
)

response = client.chat.completions.create(
    model="sonar",
    messages=[{"role": "user", "content": "What is 2+2?"}],
    max_tokens=50,
)
print("Connected:", response.choices[0].message.content)
print("Model:", response.model)
print("Tokens:", response.usage.total_tokens)
```

## Available Models

| Model | Use Case | Input $/M tokens | Output $/M tokens |
|-------|----------|-------------------|-------------------|
| `sonar` | Fast search, simple queries | $1 | $1 |
| `sonar-pro` | Deep research, more citations | $3 | $15 |
| `sonar-reasoning-pro` | Chain-of-thought with search | $3 | $15 |
| `sonar-deep-research` | Multi-step research synthesis | $2 | $8 |

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid or missing API key | Verify key starts with `pplx-` and has credits |
| `403 Forbidden` | Key lacks model access | Check key permissions at perplexity.ai/settings |
| `Module not found: openai` | SDK not installed | Run `npm install openai` or `pip install openai` |
| `Connection refused` | Wrong base URL | Ensure `baseURL` is `https://api.perplexity.ai` |

## Output
- OpenAI client configured with Perplexity base URL
- Successful API response confirming connection
- Token usage confirming billing is active

## Resources
- [Perplexity API Documentation](https://docs.perplexity.ai)
- [API Key Management](https://www.perplexity.ai/settings/api)
- [OpenAI Compatibility Guide](https://docs.perplexity.ai/guides/chat-completions-guide)
- [Model Cards](https://docs.perplexity.ai/getting-started/models)

## Next Steps
After successful auth, proceed to `perplexity-hello-world` for your first search query.
