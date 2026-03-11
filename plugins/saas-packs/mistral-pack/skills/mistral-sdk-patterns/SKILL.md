---
name: mistral-sdk-patterns
description: |
  Apply production-ready Mistral AI SDK patterns for TypeScript and Python.
  Use when implementing Mistral integrations, refactoring SDK usage,
  or establishing team coding standards for Mistral AI.
  Trigger with phrases like "mistral SDK patterns", "mistral best practices",
  "mistral code patterns", "idiomatic mistral".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Mistral SDK Patterns

## Overview
Production-ready patterns for the Mistral AI SDK (`mistralai` Python package). Covers client initialization, chat completions, streaming, function calling, and embeddings with idiomatic error handling.

## Prerequisites
- `pip install mistralai` (v1.0+)
- `MISTRAL_API_KEY` environment variable set
- Familiarity with async Python patterns

## Instructions

### Step 1: Client Initialization with Configuration

```python
from mistralai import Mistral
import os

# Singleton client with configuration
_client = None

def get_mistral_client() -> Mistral:
    global _client
    if _client is None:
        _client = Mistral(
            api_key=os.environ["MISTRAL_API_KEY"],
            timeout_ms=30000,
            max_retries=3
        )
    return _client
```

### Step 2: Chat Completions with Structured Output

```python
from mistralai import Mistral
import json

client = get_mistral_client()

# Basic chat
response = client.chat.complete(
    model="mistral-small-latest",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain quantum computing briefly."}
    ],
    temperature=0.7,
    max_tokens=500
)
print(response.choices[0].message.content)

# JSON mode for structured output
response = client.chat.complete(
    model="mistral-small-latest",
    messages=[{"role": "user", "content": "List 3 programming languages as JSON array"}],
    response_format={"type": "json_object"}
)
data = json.loads(response.choices[0].message.content)
```

### Step 3: Streaming Responses

```python
def stream_response(prompt: str):
    stream = client.chat.stream(
        model="mistral-small-latest",
        messages=[{"role": "user", "content": prompt}]
    )
    full_response = ""
    for event in stream:
        chunk = event.data.choices[0].delta.content or ""
        full_response += chunk
        yield chunk
    return full_response
```

### Step 4: Function Calling

```python
import json

tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get current weather for a city",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name"},
                "units": {"type": "string", "enum": ["celsius", "fahrenheit"]}
            },
            "required": ["city"]
        }
    }
}]

response = client.chat.complete(
    model="mistral-small-latest",
    messages=[{"role": "user", "content": "What's the weather in Paris?"}],
    tools=tools,
    tool_choice="auto"
)

# Handle tool calls
if response.choices[0].message.tool_calls:
    for call in response.choices[0].message.tool_calls:
        args = json.loads(call.function.arguments)
        result = get_weather(**args)  # your implementation
        # Send result back
        messages.append(response.choices[0].message)
        messages.append({"role": "tool", "name": call.function.name,
                         "content": json.dumps(result), "tool_call_id": call.id})
```

### Step 5: Embeddings

```python
def embed_texts(texts: list[str]) -> list[list[float]]:
    response = client.embeddings.create(
        model="mistral-embed",
        inputs=texts
    )
    return [d.embedding for d in response.data]

# Batch large sets
def embed_batch(texts: list[str], batch_size: int = 64) -> list[list[float]]:
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        embeddings.extend(embed_texts(batch))
    return embeddings
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid API key | Check `MISTRAL_API_KEY` |
| `429 Too Many Requests` | Rate limit hit | Use built-in retry or add backoff |
| `400 Bad Request` | Invalid model or params | Check model name and parameter ranges |
| Timeout | Large prompt or slow network | Increase `timeout_ms` |

## Examples

### Async Client
```python
from mistralai import Mistral
import asyncio

async def async_chat(prompt: str):
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
    response = await client.chat.complete_async(
        model="mistral-small-latest",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
```

## Resources
- [Mistral AI SDK](https://github.com/mistralai/client-python)
- [API Reference](https://docs.mistral.ai/api/)
