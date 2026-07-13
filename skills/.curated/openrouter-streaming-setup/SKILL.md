---
name: openrouter-streaming-setup
description: 'Implement streaming responses with OpenRouter for real-time UIs. Use
  when building chat interfaces, reducing time-to-first-token, or processing long
  completions. Triggers: ''openrouter streaming'', ''openrouter sse'', ''stream response
  openrouter'', ''real-time openrouter''.

  '
allowed-tools: Read, Write, Edit, Grep, Bash(python3:*), Bash(node:*)
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- openrouter
- streaming
- real-time
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# OpenRouter Streaming Setup

## Overview

OpenRouter supports Server-Sent Events (SSE) streaming via `stream: true`, compatible with the OpenAI SDK. Streaming returns tokens as they're generated, reducing time-to-first-token (TTFT) from seconds to milliseconds. Usage stats are available via `stream_options: {include_usage: true}` in the final chunk. This skill covers Python and TypeScript streaming, SSE forwarding to browsers, and error recovery.

## Prerequisites

- An OpenRouter API key (`sk-or-v1-...`) exported as `OPENROUTER_API_KEY` — see the `openrouter-install-auth` skill for setup
- Python 3.8+ or Node.js 18+ with the OpenAI SDK (the async example uses `AsyncOpenAI` from the same Python package)
- FastAPI if you plan to forward the SSE stream to browsers per the SSE Forwarding section
- A streaming-appropriate client timeout (e.g. 120s) — longer than for non-streaming requests

## Instructions

1. Start with Python: Basic Streaming — pass `stream=True` plus `stream_options={"include_usage": True}` so the final chunk carries token counts, and print each `chunk.choices[0].delta.content` as it arrives.
2. Wrap that loop in the Python: Streaming with Metrics generator to capture TTFT and total time per request; the metrics dict is available after the generator is exhausted.
3. For Node services, use the TypeScript: Streaming `for await` loop over the same `stream: true` request.
4. To reach a browser UI, expose the FastAPI endpoint in SSE Forwarding to Browser — it re-emits each token as a `data: {"token": ...}` SSE line and terminates with `data: [DONE]`.
5. Consume that endpoint with the Browser Client (JavaScript) reader loop, appending tokens to the DOM as they decode.
6. In async web frameworks, switch to the Async Streaming pattern built on `AsyncOpenAI`.
7. Handle mid-stream failures (cut-offs, missing `usage`, keep-alive pings, `finish_reason: "length"`) per the Error Handling table.

## Python: Basic Streaming

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    default_headers={"HTTP-Referer": "https://my-app.com", "X-Title": "my-app"},
)

# Stream with usage stats
stream = client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet",
    messages=[{"role": "user", "content": "Explain how HTTP streaming works"}],
    max_tokens=500,
    stream=True,
    stream_options={"include_usage": True},  # Get token counts in final chunk
)

full_content = []
for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
        token = chunk.choices[0].delta.content
        print(token, end="", flush=True)
        full_content.append(token)

    # Final chunk contains usage stats
    if chunk.usage:
        print(f"\n---\nTokens: {chunk.usage.prompt_tokens} in + {chunk.usage.completion_tokens} out")

result = "".join(full_content)
```

## Python: Streaming with Metrics

```python
import time

def stream_with_metrics(messages, model="anthropic/claude-3.5-sonnet", **kwargs):
    """Stream response and capture performance metrics."""
    start = time.monotonic()
    first_token_time = None
    chunks = []
    usage = None

    stream = client.chat.completions.create(
        model=model, messages=messages, stream=True,
        stream_options={"include_usage": True},
        **kwargs,
    )

    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            token = chunk.choices[0].delta.content
            if first_token_time is None:
                first_token_time = (time.monotonic() - start) * 1000
            chunks.append(token)
            yield token  # Yield each token as it arrives

        if chunk.usage:
            usage = {
                "prompt_tokens": chunk.usage.prompt_tokens,
                "completion_tokens": chunk.usage.completion_tokens,
            }

    total_time = (time.monotonic() - start) * 1000
    # Metrics available after generator exhausted
    stream_with_metrics.last_metrics = {
        "ttft_ms": round(first_token_time or 0),
        "total_ms": round(total_time),
        "usage": usage,
        "model": model,
    }

# Usage
for token in stream_with_metrics(
    [{"role": "user", "content": "Hello"}],
    model="openai/gpt-4o-mini",
    max_tokens=200,
):
    print(token, end="", flush=True)
print(f"\nMetrics: {stream_with_metrics.last_metrics}")
```

## TypeScript: Streaming

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://openrouter.ai/api/v1",
  apiKey: process.env.OPENROUTER_API_KEY,
  defaultHeaders: { "HTTP-Referer": "https://my-app.com", "X-Title": "my-app" },
});

async function streamCompletion(prompt: string, model = "openai/gpt-4o-mini") {
  const stream = await client.chat.completions.create({
    model,
    messages: [{ role: "user", content: prompt }],
    max_tokens: 500,
    stream: true,
  });

  const chunks: string[] = [];
  for await (const chunk of stream) {
    const token = chunk.choices[0]?.delta?.content;
    if (token) {
      process.stdout.write(token);
      chunks.push(token);
    }
  }
  return chunks.join("");
}
```

## SSE Forwarding to Browser (FastAPI)

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

@app.post("/v1/stream")
async def stream_endpoint(prompt: str, model: str = "openai/gpt-4o-mini"):
    """Forward OpenRouter SSE stream to browser."""
    async def generate():
        stream = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            stream=True,
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                token = chunk.choices[0].delta.content
                yield f"data: {json.dumps({'token': token})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

## Browser Client (JavaScript)

```javascript
// Consume SSE stream from your backend
async function streamChat(prompt) {
  const response = await fetch("/v1/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const text = decoder.decode(value);
    for (const line of text.split("\n")) {
      if (line.startsWith("data: ") && line !== "data: [DONE]") {
        const data = JSON.parse(line.slice(6));
        document.getElementById("output").textContent += data.token;
      }
    }
  }
}
```

## Async Streaming (Python)

```python
from openai import AsyncOpenAI

aclient = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    default_headers={"HTTP-Referer": "https://my-app.com", "X-Title": "my-app"},
)

async def async_stream(messages, model="openai/gpt-4o-mini", **kwargs):
    """Async streaming for use in async web frameworks."""
    stream = await aclient.chat.completions.create(
        model=model, messages=messages, stream=True, **kwargs,
    )
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
```

## Output

- Token-by-token console output as the model generates, followed by usage counts from the final chunk (`Tokens: 14 in + 132 out`)
- A metrics dict after the generator is exhausted: `ttft_ms`, `total_ms`, `usage` token counts, and the `model` used
- A FastAPI SSE endpoint emitting `data: {"token": ...}` lines and a terminating `data: [DONE]` for browser consumption
- Incrementally rendered text in the browser as the JavaScript reader loop decodes each SSE line

## Examples

Stream with metrics and inspect TTFT after the tokens finish printing:

```python
for token in stream_with_metrics(
    [{"role": "user", "content": "Write a haiku about programming"}],
    model="openai/gpt-4o-mini", max_tokens=60,
):
    print(token, end="", flush=True)
print(f"\nMetrics: {stream_with_metrics.last_metrics}")
# Code flows like a stream / bugs surface then sink away / green tests light the dawn
# Metrics: {'ttft_ms': 412, 'total_ms': 1875, 'usage': {'prompt_tokens': 14, 'completion_tokens': 21}, 'model': 'openai/gpt-4o-mini'}
```

More worked examples: `references/examples.md`.

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| Stream cuts off mid-response | Network timeout or provider error | Save partial content; implement retry from last position |
| Missing `usage` in stream | Didn't set `stream_options` | Add `stream_options: {"include_usage": True}` |
| Empty delta chunks | Keep-alive pings | Filter `chunk.choices[0].delta.content is None` |
| `finish_reason: "length"` | Hit max_tokens limit | Increase max_tokens or continue with follow-up request |

## Enterprise Considerations

- Always use `stream_options: {"include_usage": True}` to get token counts for cost tracking
- Set connection timeouts appropriate for streaming (longer than non-streaming, e.g., 120s)
- Implement heartbeat detection: if no chunks for >30s, consider the stream dead and retry
- Buffer partial tokens on the server before forwarding to the client for smoother rendering
- Log TTFT per model to benchmark streaming performance over time
- Use streaming for all user-facing requests; use non-streaming for batch/background processing

## References

- Examples | Errors
- Streaming | [API Reference](https://openrouter.ai/docs/api/reference/overview)
