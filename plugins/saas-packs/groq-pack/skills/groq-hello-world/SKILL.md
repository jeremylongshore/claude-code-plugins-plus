---
name: groq-hello-world
description: |
  Create a minimal working Groq chat completion example.
  Use when starting a new Groq integration, testing your setup,
  or learning basic Groq API patterns.
  Trigger with phrases like "groq hello world", "groq example",
  "groq quick start", "simple groq code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, groq, api, testing]

---
# Groq Hello World

## Overview
Build a minimal chat completion with Groq's LPU inference API. Groq uses an OpenAI-compatible endpoint, so the API shape is familiar -- but responses arrive 10-50x faster than GPU-based providers.

## Prerequisites
- `groq-sdk` installed (`npm install groq-sdk`)
- `GROQ_API_KEY` environment variable set
- Completed `groq-install-auth` setup

## Instructions

### Step 1: Basic Chat Completion (TypeScript)
```typescript
import Groq from "groq-sdk";

const groq = new Groq();

async function main() {
  const completion = await groq.chat.completions.create({
    model: "llama-3.3-70b-versatile",
    messages: [
      { role: "system", content: "You are a helpful assistant." },
      { role: "user", content: "What is Groq's LPU and why is it fast?" },
    ],
  });

  console.log(completion.choices[0].message.content);
  console.log(`Tokens: ${completion.usage?.total_tokens}`);
}

main().catch(console.error);
```

### Step 2: Streaming Response
```typescript
async function streamExample() {
  const stream = await groq.chat.completions.create({
    model: "llama-3.3-70b-versatile",
    messages: [
      { role: "user", content: "Explain quantum computing in 3 sentences." },
    ],
    stream: true,
  });

  for await (const chunk of stream) {
    const content = chunk.choices[0]?.delta?.content || "";
    process.stdout.write(content);
  }
  console.log(); // newline
}
```

### Step 3: Python Equivalent
```python
from groq import Groq

client = Groq()

completion = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is Groq's LPU and why is it fast?"},
    ],
)

print(completion.choices[0].message.content)
print(f"Tokens: {completion.usage.total_tokens}")
```

### Step 4: Try Different Models
```typescript
// Speed tier -- fastest responses (~560 tok/s)
const fast = await groq.chat.completions.create({
  model: "llama-3.1-8b-instant",
  messages: [{ role: "user", content: "Hello!" }],
});

// Quality tier -- best reasoning (~280 tok/s)
const quality = await groq.chat.completions.create({
  model: "llama-3.3-70b-versatile",
  messages: [{ role: "user", content: "Explain monads in Haskell." }],
});

// Vision tier -- multimodal understanding
const vision = await groq.chat.completions.create({
  model: "meta-llama/llama-4-scout-17b-16e-instruct",
  messages: [{
    role: "user",
    content: [
      { type: "text", text: "Describe this image." },
      { type: "image_url", image_url: { url: "https://example.com/photo.jpg" } },
    ],
  }],
});
```

## Available Models (Current)

| Model ID | Params | Context | Speed | Best For |
|----------|--------|---------|-------|----------|
| `llama-3.1-8b-instant` | 8B | 128K | ~560 tok/s | Classification, extraction, fast tasks |
| `llama-3.3-70b-versatile` | 70B | 128K | ~280 tok/s | General purpose, reasoning, code |
| `llama-3.3-70b-specdec` | 70B | 128K | Faster | Same quality, speculative decoding |
| `meta-llama/llama-4-scout-17b-16e-instruct` | 17Bx16E | 128K | ~460 tok/s | Vision, multimodal |
| `meta-llama/llama-4-maverick-17b-128e-instruct` | 17Bx128E | 128K | — | Best multimodal quality |

## Response Structure
```typescript
interface ChatCompletion {
  id: string;                    // "chatcmpl-xxx"
  object: "chat.completion";
  created: number;               // Unix timestamp
  model: string;                 // Actual model used
  choices: [{
    index: number;
    message: { role: "assistant"; content: string };
    finish_reason: "stop" | "length" | "tool_calls";
  }];
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
    queue_time: number;          // Groq-specific: seconds in queue
    prompt_time: number;         // Groq-specific: seconds for prompt
    completion_time: number;     // Groq-specific: seconds for completion
    total_time: number;          // Groq-specific: total processing seconds
  };
}
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `401 Invalid API Key` | Key not set or invalid | Check `GROQ_API_KEY` env var |
| `model_not_found` | Typo in model ID or deprecated model | Check model list at console.groq.com/docs/models |
| `429 Rate limit` | Free tier: 30 RPM on large models | Wait for `retry-after` header value |
| `context_length_exceeded` | Prompt + max_tokens > model context | Reduce prompt size or set lower `max_tokens` |

## Resources
- [Groq Text Generation Docs](https://console.groq.com/docs/text-chat)
- [Groq Models Reference](https://console.groq.com/docs/models)
- [Groq API Reference](https://console.groq.com/docs/api-reference)

## Next Steps
Proceed to `groq-local-dev-loop` for development workflow setup.
