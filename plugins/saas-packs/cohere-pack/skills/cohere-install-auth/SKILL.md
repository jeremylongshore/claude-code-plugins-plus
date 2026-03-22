---
name: cohere-install-auth
description: |
  Install and configure Cohere SDK authentication with API v2.
  Use when setting up a new Cohere integration, configuring API keys,
  or initializing the CohereClientV2 in your project.
  Trigger with phrases like "install cohere", "setup cohere",
  "cohere auth", "configure cohere API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, nlp, cohere]
compatible-with: claude-code
---

# Cohere Install & Auth

## Overview
Set up the Cohere SDK (v2) and configure authentication for Chat, Embed, Rerank, and Classify endpoints.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Cohere account at [dashboard.cohere.com](https://dashboard.cohere.com)
- API key from Cohere dashboard (trial keys are free, production keys require billing)

## Instructions

### Step 1: Install SDK

```bash
# Node.js / TypeScript
npm install cohere-ai

# Python
pip install cohere
```

### Step 2: Configure API Key

```bash
# Set environment variable
export CO_API_KEY="your-api-key-here"

# Or create .env file (add .env to .gitignore!)
echo 'CO_API_KEY=your-api-key-here' >> .env
```

**Key types:**
- **Trial key** — free, rate-limited (5-20 calls/min per endpoint, 1000/month others)
- **Production key** — metered billing, 1000 calls/min all endpoints, unlimited monthly

### Step 3: Verify Connection (TypeScript)

```typescript
import { CohereClientV2 } from 'cohere-ai';

const cohere = new CohereClientV2({
  token: process.env.CO_API_KEY,
});

async function verify() {
  const response = await cohere.chat({
    model: 'command-a-03-2025',
    messages: [
      { role: 'user', content: 'Say "connection verified" and nothing else.' },
    ],
  });
  console.log('Status:', response.message?.content?.[0]?.text);
}

verify().catch(console.error);
```

### Step 4: Verify Connection (Python)

```python
import cohere
import os

co = cohere.ClientV2(api_key=os.environ.get("CO_API_KEY"))

response = co.chat(
    model="command-a-03-2025",
    messages=[
        {"role": "user", "content": "Say 'connection verified' and nothing else."}
    ],
)
print("Status:", response.message.content[0].text)
```

## Available Models

| Model | ID | Context | Best For |
|-------|----|---------|----------|
| Command A | `command-a-03-2025` | 256K | Latest, most capable |
| Command R+ | `command-r-plus-08-2024` | 128K | Complex RAG, agents |
| Command R | `command-r-08-2024` | 128K | RAG, cost-effective |
| Command R7B | `command-r7b-12-2024` | 128K | Fast, lightweight |
| Embed English v4 | `embed-v4.0` | 128K | Embeddings (EN) |
| Embed Multilingual v3 | `embed-multilingual-v3.0` | 512 | Embeddings (100+ langs) |
| Rerank v3.5 | `rerank-v3.5` | 4K | Search reranking |

## Output
- Installed `cohere-ai` (TS) or `cohere` (Python) package
- Environment variable `CO_API_KEY` configured
- Verified API connectivity with a chat completion

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `CohereApiError: invalid api token` | Wrong or expired key | Regenerate at dashboard.cohere.com |
| `CohereConnectionError` | Network blocked | Ensure HTTPS to `api.cohere.com` allowed |
| `429 Too Many Requests` | Trial rate limit hit | Wait 60s or upgrade to production key |
| `MODULE_NOT_FOUND cohere-ai` | Package not installed | Run `npm install cohere-ai` |

## SDK Auto-Detection
The SDK reads `CO_API_KEY` automatically if set. You can skip the `token` param:

```typescript
// Auto-reads CO_API_KEY from environment
const cohere = new CohereClientV2();
```

## Resources
- [Cohere API v2 Reference](https://docs.cohere.com/reference/about)
- [Cohere Dashboard](https://dashboard.cohere.com)
- [Cohere Models Overview](https://docs.cohere.com/docs/models)
- [API Key & Rate Limits](https://docs.cohere.com/docs/rate-limits)

## Next Steps
After successful auth, proceed to `cohere-hello-world` for your first real API call.
