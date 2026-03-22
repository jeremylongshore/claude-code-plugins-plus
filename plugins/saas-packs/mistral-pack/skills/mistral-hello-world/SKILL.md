---
name: mistral-hello-world
description: |
  Create a minimal working Mistral AI chat completion example.
  Use when starting a new Mistral integration, testing your setup,
  or learning basic Mistral API patterns.
  Trigger with phrases like "mistral hello world", "mistral example",
  "mistral quick start", "simple mistral code", "mistral chat".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, mistral, api, testing]

---
# Mistral AI Hello World

## Overview
Minimal working examples demonstrating Mistral AI chat completions, streaming, multi-turn conversation, and JSON mode. Uses the official `@mistralai/mistralai` TypeScript SDK and `mistralai` Python SDK.

## Prerequisites
- Completed `mistral-install-auth` setup
- Valid `MISTRAL_API_KEY` environment variable set
- Node.js 18+ or Python 3.9+

## Instructions

### Step 1: Basic Chat Completion

**TypeScript (hello-mistral.ts)**
```typescript
import { Mistral } from '@mistralai/mistralai';

const client = new Mistral({ apiKey: process.env.MISTRAL_API_KEY });

async function main() {
  const response = await client.chat.complete({
    model: 'mistral-small-latest',
    messages: [
      { role: 'user', content: 'Say "Hello, World!" in a creative way.' },
    ],
  });

  console.log(response.choices?.[0]?.message?.content);
  console.log('Tokens used:', response.usage);
}

main().catch(console.error);
```

**Python (hello_mistral.py)**
```python
import os
from mistralai import Mistral

client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])

response = client.chat.complete(
    model="mistral-small-latest",
    messages=[
        {"role": "user", "content": "Say 'Hello, World!' in a creative way."}
    ],
)

print(response.choices[0].message.content)
print(f"Tokens: {response.usage}")
```

### Step 2: Run the Example
```bash
# TypeScript
npx tsx hello-mistral.ts

# Python
python hello_mistral.py
```

### Step 3: Streaming Response

Streaming delivers the first token in ~200ms instead of waiting 1-2s for the full response.

**TypeScript**
```typescript
import { Mistral } from '@mistralai/mistralai';

const client = new Mistral({ apiKey: process.env.MISTRAL_API_KEY });

async function streamChat() {
  const stream = await client.chat.stream({
    model: 'mistral-small-latest',
    messages: [
      { role: 'user', content: 'Tell me a short story about AI.' },
    ],
  });

  for await (const event of stream) {
    const content = event.data?.choices?.[0]?.delta?.content;
    if (content) process.stdout.write(content);
  }
  console.log(); // newline
}

streamChat().catch(console.error);
```

**Python**
```python
stream = client.chat.stream(
    model="mistral-small-latest",
    messages=[{"role": "user", "content": "Tell me a short story about AI."}],
)

for event in stream:
    content = event.data.choices[0].delta.content
    if content:
        print(content, end="", flush=True)
print()
```

### Step 4: Multi-Turn Conversation

```typescript
const messages: Array<{ role: 'system' | 'user' | 'assistant'; content: string }> = [
  { role: 'system', content: 'You are a helpful coding assistant.' },
  { role: 'user', content: 'What is the capital of France?' },
];

const r1 = await client.chat.complete({
  model: 'mistral-small-latest', messages,
});
const answer = r1.choices?.[0]?.message?.content ?? '';
console.log('A1:', answer);

// Continue the conversation
messages.push({ role: 'assistant', content: answer });
messages.push({ role: 'user', content: 'What about Germany?' });

const r2 = await client.chat.complete({
  model: 'mistral-small-latest', messages,
});
console.log('A2:', r2.choices?.[0]?.message?.content);
```

### Step 5: JSON Mode (Structured Output)

```typescript
const response = await client.chat.complete({
  model: 'mistral-small-latest',
  messages: [
    { role: 'user', content: 'List 3 programming languages with their year of creation as JSON.' },
  ],
  responseFormat: { type: 'json_object' },
});

const data = JSON.parse(response.choices?.[0]?.message?.content ?? '{}');
console.log(data);
```

### Step 6: With Temperature and Token Limits

```typescript
const response = await client.chat.complete({
  model: 'mistral-small-latest',
  messages: [{ role: 'user', content: 'Write a haiku about coding.' }],
  temperature: 0.7,   // 0-1, higher = more creative
  maxTokens: 100,     // cap output length
  topP: 0.9,          // nucleus sampling
});
```

## Output
- Working code file with Mistral client initialization
- Successful API response with generated text
- Console output showing response and token usage

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `Import Error` | SDK not installed | Run `npm install @mistralai/mistralai` |
| `401 Unauthorized` | Invalid API key | Check `MISTRAL_API_KEY` is set |
| `ERR_REQUIRE_ESM` | CommonJS project | Use `import` syntax or dynamic `await import()` |
| `429 Rate Limited` | Too many requests | Wait and retry with backoff |

## Model Quick Reference

| Model ID | Best For | Context |
|----------|----------|---------|
| `mistral-small-latest` | Fast, cost-effective tasks | 256k |
| `mistral-large-latest` | Complex reasoning, analysis | 256k |
| `codestral-latest` | Code generation, FIM | 256k |
| `mistral-embed` | Text/code embeddings | 8k |
| `pixtral-large-latest` | Vision + text (multimodal) | 128k |

## Resources
- [Mistral AI Quickstart](https://docs.mistral.ai/getting-started/quickstart/)
- [Chat Completions API](https://docs.mistral.ai/api/endpoint/chat/)
- [Models Overview](https://docs.mistral.ai/getting-started/models/)

## Next Steps
Proceed to `mistral-core-workflow-a` for production chat patterns or `mistral-local-dev-loop` for dev workflow setup.
