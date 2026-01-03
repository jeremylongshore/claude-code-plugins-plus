---
name: openrouter-streaming-setup
description: |
  Implement streaming responses with OpenRouter. Use when building real-time chat interfaces or reducing time-to-first-token. Trigger with phrases like 'openrouter streaming', 'openrouter sse', 'stream response', 'real-time openrouter'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# OpenRouter Streaming Setup

## Overview

This skill demonstrates streaming response implementation for lower perceived latency and real-time output display.

## Prerequisites

- OpenRouter integration
- Frontend capable of handling SSE/streaming

## Instructions

Follow these steps to implement this skill:

1. **Verify Prerequisites**: Ensure all prerequisites listed above are met
2. **Review the Implementation**: Study the code examples and patterns below
3. **Adapt to Your Environment**: Modify configuration values for your setup
4. **Test the Integration**: Run the verification steps to confirm functionality
5. **Monitor in Production**: Set up appropriate logging and monitoring

## Overview

This skill demonstrates streaming response implementation for lower perceived latency and real-time output display.

## Prerequisites

- OpenRouter integration
- Frontend capable of handling SSE/streaming

## Basic Streaming

### Python Streaming
```python
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"]
)

def stream_chat(prompt: str, model: str = "openai/gpt-4-turbo"):
    """Stream response and print in real-time."""
    stream = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )

    full_response = ""
    for chunk in stream:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            print(content, end="", flush=True)
            full_response += content

    print()  # Newline at end
    return full_response

# Usage
response = stream_chat("Explain quantum computing")
```

### TypeScript Streaming
```typescript
import OpenAI from 'openai';

const client = new OpenAI({
  baseURL: 'https://openrouter.ai/api/v1',
  apiKey: process.env.OPENROUTER_API_KEY,
});

async function streamChat(prompt: string, model = 'openai/gpt-4-turbo'): Promise<string> {
  const stream = await client.chat.completions.create({
    model,
    messages: [{ role: 'user', content: prompt }],
    stream: true,
  });

  let fullResponse = '';
  for await (const chunk of stream) {
    const content = chunk.choices[0]?.delta?.content || '';
    process.stdout.write(content);
    fullResponse += content;
  }
  console.log();
  return fullResponse;
}

// Usage
const response = await streamChat('Explain quantum computing');
```

## Async Streaming

### Python Async Stream
```python
from openai import AsyncOpenAI

async_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"]
)

async def async_stream_chat(prompt: str, model: str = "openai/gpt-4-turbo"):
    """Async streaming with yield."""
    stream = await async_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )

    async for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

# Usage
async def main():
    async for content in async_stream_chat("Hello"):
        print(content, end="", flush=True)

import asyncio
asyncio.run(main())
```

### Collecting Streamed Response
```python
async def collect_stream(prompt: str, model: str = "openai/gpt-4-turbo") -> str:
    """Collect full streamed response."""
    parts = []
    async for chunk in async_stream_chat(prompt, model):
        parts.append(chunk)
    return "".join(parts)
```

## Web Framework Integration

### FastAPI Streaming
```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

async def generate_stream(prompt: str, model: str):
    """Generator for StreamingResponse."""
    stream = await async_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )

    async for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

@app.post("/chat/stream")
async def chat_stream(prompt: str, model: str = "openai/gpt-4-turbo"):
    return StreamingResponse(
        generate_stream(prompt, model),
        media_type="text/plain"
    )
```

### Flask SSE Streaming
```python
from flask import Flask, Response, request

app = Flask(__name__)

def generate_sse(prompt: str, model: str):
    """Generate Server-Sent Events."""
    stream = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )

    for chunk in stream:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            # SSE format
            yield f"data: {content}\n\n"

    yield "data: [DONE]\n\n"

@app.route("/chat/stream", methods=["POST"])
def chat_stream():
    data = request.json
    return Response(
        generate_sse(data["prompt"], data.get("model", "openai/gpt-4-turbo")),
        mimetype="text/event-stream"
    )
```

### Express.js SSE
```typescript
import express from 'express';

const app = express();
app.use(express.json());

app.post('/chat/stream', async (req, res) => {
  const { prompt, model = 'openai/gpt-4-turbo' } = req.body;

  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');

  const stream = await client.chat.completions.create({
    model,
    messages: [{ role: 'user', content: prompt }],
    stream: true,
  });

  for await (const chunk of stream) {
    const content = chunk.choices[0]?.delta?.content || '';
    if (content) {
      res.write(`data: ${JSON.stringify({ content })}\n\n`);
    }
  }

  res.write('data: [DONE]\n\n');
  res.end();
});
```

## Stream Processing

### With Callbacks
```python
from typing import Callable

def stream_with_callbacks(
    prompt: str,
    model: str = "openai/gpt-4-turbo",
    on_chunk: Callable[[str], None] = None,
    on_complete: Callable[[str], None] = None,
    on_error: Callable[[Exception], None] = None
):
    """Stream with callback handlers."""
    try:
        stream = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            stream=True
        )

        full_response = ""
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                if on_chunk:
                    on_chunk(content)

        if on_complete:
            on_complete(full_response)

        return full_response

    except Exception as e:
        if on_error:
            on_error(e)
        raise

# Usage
stream_with_callbacks(
    "Hello",
    on_chunk=lambda c: print(c, end=""),
    on_complete=lambda r: print(f"\n\nTotal: {len(r)} chars")
)
```

### Token Counting During Stream
```python
def stream_with_token_count(prompt: str, model: str = "openai/gpt-4-turbo"):
    """Stream and count tokens."""
    stream = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
        stream_options={"include_usage": True}  # Request usage info
    )

    full_response = ""
    usage = None

    for chunk in stream:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            full_response += content
            yield content

        # Check for usage in final chunk
        if hasattr(chunk, 'usage') and chunk.usage:
            usage = chunk.usage

    return full_response, usage
```

## Error Handling in Streams

### Robust Streaming
```python
from openai import APIError, RateLimitError

def robust_stream(prompt: str, model: str, retries: int = 3):
    """Stream with retry logic."""
    for attempt in range(retries):
        try:
            stream = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )

            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield content

            return

        except RateLimitError:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise

        except APIError as e:
            if attempt < retries - 1:
                time.sleep(1)
            else:
                raise
```

### Stream Timeout
```python
import asyncio

async def stream_with_timeout(
    prompt: str,
    model: str = "openai/gpt-4-turbo",
    timeout: float = 60.0
):
    """Stream with overall timeout."""
    async def stream_generator():
        stream = await async_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            stream=True
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    try:
        parts = []
        async for content in asyncio.wait_for(
            stream_generator().__aiter__().__anext__,
            timeout=timeout
        ):
            parts.append(content)
            yield content
    except asyncio.TimeoutError:
        raise Exception(f"Stream timed out after {timeout}s")
```

## Frontend Integration

### React Hook for Streaming
```typescript
import { useState, useCallback } from 'react';

function useStreamingChat() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [response, setResponse] = useState('');
  const [error, setError] = useState<Error | null>(null);

  const streamChat = useCallback(async (prompt: string) => {
    setIsStreaming(true);
    setResponse('');
    setError(null);

    try {
      const res = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
      });

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error('No reader');

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = decoder.decode(value);
        setResponse((prev) => prev + text);
      }
    } catch (err) {
      setError(err as Error);
    } finally {
      setIsStreaming(false);
    }
  }, []);

  return { streamChat, response, isStreaming, error };
}

// Usage
function ChatComponent() {
  const { streamChat, response, isStreaming } = useStreamingChat();

  return (
    <div>
      <button onClick={() => streamChat('Hello')} disabled={isStreaming}>
        Send
      </button>
      <pre>{response}</pre>
    </div>
  );
}
```

### SSE Client
```javascript
function streamSSE(prompt, onChunk, onComplete, onError) {
  const eventSource = new EventSource(
    `/api/chat/stream?prompt=${encodeURIComponent(prompt)}`
  );

  eventSource.onmessage = (event) => {
    if (event.data === '[DONE]') {
      eventSource.close();
      onComplete?.();
    } else {
      onChunk(event.data);
    }
  };

  eventSource.onerror = (error) => {
    eventSource.close();
    onError?.(error);
  };

  return () => eventSource.close();
}

// Usage
const cleanup = streamSSE(
  'Hello',
  (chunk) => console.log(chunk),
  () => console.log('Done'),
  (err) => console.error(err)
);
```

## Output

Successful execution produces:
- Working OpenRouter integration
- Verified API connectivity
- Example responses demonstrating functionality

## Error Handling

Common errors and solutions:
1. **401 Unauthorized**: Check API key format (must start with `sk-or-`)
2. **429 Rate Limited**: Implement exponential backoff
3. **500 Server Error**: Retry with backoff, check OpenRouter status page
4. **Model Not Found**: Verify model ID includes provider prefix

## Examples

See code examples in sections above for complete, runnable implementations.

## Resources

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter Models](https://openrouter.ai/models)
- [OpenRouter API Reference](https://openrouter.ai/docs/api-reference)
- [OpenRouter Status](https://status.openrouter.ai)

## Output

Successful execution produces:
- Working OpenRouter integration
- Verified API connectivity
- Example responses demonstrating functionality

## Error Handling

Common errors and solutions:
1. **401 Unauthorized**: Check API key format (must start with `sk-or-`)
2. **429 Rate Limited**: Implement exponential backoff
3. **500 Server Error**: Retry with backoff, check OpenRouter status page
4. **Model Not Found**: Verify model ID includes provider prefix

## Examples

See code examples in sections above for complete, runnable implementations.

## Resources

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter Models](https://openrouter.ai/models)
- [OpenRouter API Reference](https://openrouter.ai/docs/api-reference)
- [OpenRouter Status](https://status.openrouter.ai)
