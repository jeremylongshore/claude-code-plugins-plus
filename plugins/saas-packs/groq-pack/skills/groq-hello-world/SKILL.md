---
name: groq-hello-world
description: |
  Create a minimal working Groq chat completion example. Use when starting a new
  Groq integration, testing your setup after installing the SDK, or learning the
  basic Groq API request/response pattern before building something larger.
  Trigger with phrases like "groq hello world", "groq example",
  "groq quick start", "simple groq code".
allowed-tools: Read, Write, Edit
version: 1.11.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- groq
- api
- testing
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Groq Hello World

## Overview

Build a minimal chat completion with Groq's LPU inference API. Groq uses an OpenAI-compatible endpoint, so the API shape is familiar -- but responses arrive 10-50x faster than GPU-based providers. This skill gets you from an installed SDK to a working, verified request; deeper variants (streaming, Python, model selection) live in `references/`.

## Prerequisites

- `groq-sdk` installed (`npm install groq-sdk`)
- `GROQ_API_KEY` environment variable set
- Completed `groq-install-auth` setup

## Instructions

Use `Write` to create the example file, then run it to confirm your key and SDK work. Start with the single basic request below; reach for the reference variants only once this succeeds.

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

### Step 2: Go deeper (references)

Once Step 1 returns text, extend it with the moved-out variants:

- **Streaming** tokens as they generate, plus the **Python** equivalent and a **model-selection** cheat sheet — [references/examples.md](references/examples.md).
- Full **model catalog** (IDs, params, context, speed) and the complete **response interface** — [references/models-and-response.md](references/models-and-response.md).

## Output

A successful run prints the assistant's reply text followed by the total token count, e.g.:

```
Groq's LPU (Language Processing Unit) is a deterministic, single-core
inference chip... [assistant response continues]
Tokens: 142
```

The underlying API returns an OpenAI-compatible `ChatCompletion` object: the text is at `choices[0].message.content`, and `usage` carries token counts plus four Groq-specific timing fields (`queue_time`, `prompt_time`, `completion_time`, `total_time`). Full response shape: [references/models-and-response.md](references/models-and-response.md).

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Invalid API Key` | Key not set or invalid | Check `GROQ_API_KEY` env var |
| `model_not_found` | Typo in model ID or deprecated model | Check model list at console.groq.com/docs/models |
| `429 Rate limit` | Free tier: 30 RPM on large models | Wait for `retry-after` header value |
| `context_length_exceeded` | Prompt + max_tokens > model context | Reduce prompt size or set lower `max_tokens` |

## Examples

- **Minimal request** — the TypeScript block in Step 1 above is the canonical hello-world; run it as-is after setting `GROQ_API_KEY`.
- **Streaming a response** — see [references/examples.md](references/examples.md) for the `stream: true` loop that writes tokens to stdout as they arrive.
- **Python equivalent** — the same request in Python: [references/examples.md](references/examples.md).
- **Choosing a model per task** (speed vs. quality vs. vision) — [references/examples.md](references/examples.md).

## Resources

- [Groq Text Generation Docs](https://console.groq.com/docs/text-chat)
- [Groq Models Reference](https://console.groq.com/docs/models)
- [Groq API Reference](https://console.groq.com/docs/api-reference)
- Next: proceed to `groq-local-dev-loop` for development workflow setup.
