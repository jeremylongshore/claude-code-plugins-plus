---
name: openrouter-hello-world
description: |
  Make your first OpenRouter API request. Triggers on "openrouter first request",
  "openrouter hello world", "openrouter getting started", "try openrouter".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# OpenRouter Hello World

## Your First Request

### cURL
```bash
curl https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "Say hello!"}
    ]
  }'
```

### Response
```json
{
  "id": "gen-abc123",
  "model": "openai/gpt-3.5-turbo",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I assist you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 9,
    "total_tokens": 19
  }
}
```

## Python Example

### Basic Request
```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)

response = client.chat.completions.create(
    model="openai/gpt-3.5-turbo",
    messages=[
        {"role": "user", "content": "Say hello!"}
    ]
)

print(response.choices[0].message.content)
```

### With System Message
```python
response = client.chat.completions.create(
    model="anthropic/claude-3-sonnet",
    messages=[
        {"role": "system", "content": "You are a helpful coding assistant."},
        {"role": "user", "content": "Write a Python hello world"}
    ]
)
```

## TypeScript Example

### Basic Request
```typescript
import OpenAI from 'openai';

const client = new OpenAI({
  baseURL: 'https://openrouter.ai/api/v1',
  apiKey: process.env.OPENROUTER_API_KEY,
});

async function main() {
  const response = await client.chat.completions.create({
    model: 'openai/gpt-3.5-turbo',
    messages: [
      { role: 'user', content: 'Say hello!' }
    ],
  });

  console.log(response.choices[0].message.content);
}

main();
```

### With Streaming
```typescript
const stream = await client.chat.completions.create({
  model: 'openai/gpt-4-turbo',
  messages: [{ role: 'user', content: 'Write a poem' }],
  stream: true,
});

for await (const chunk of stream) {
  process.stdout.write(chunk.choices[0]?.delta?.content || '');
}
```

## Try Different Models

### OpenAI Models
```python
# GPT-4 Turbo
response = client.chat.completions.create(
    model="openai/gpt-4-turbo",
    messages=[{"role": "user", "content": "Hello!"}]
)

# GPT-4o
response = client.chat.completions.create(
    model="openai/gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Anthropic Models
```python
# Claude 3.5 Sonnet
response = client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet",
    messages=[{"role": "user", "content": "Hello!"}]
)

# Claude 3 Opus
response = client.chat.completions.create(
    model="anthropic/claude-3-opus",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Open Source Models
```python
# Llama 3.1 70B
response = client.chat.completions.create(
    model="meta-llama/llama-3.1-70b-instruct",
    messages=[{"role": "user", "content": "Hello!"}]
)

# Mixtral
response = client.chat.completions.create(
    model="mistralai/mixtral-8x7b-instruct",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## Request Parameters

### Temperature
```python
response = client.chat.completions.create(
    model="openai/gpt-4-turbo",
    messages=[{"role": "user", "content": "Write a story"}],
    temperature=0.7,  # 0-2, higher = more creative
)
```

### Max Tokens
```python
response = client.chat.completions.create(
    model="openai/gpt-4-turbo",
    messages=[{"role": "user", "content": "Summarize..."}],
    max_tokens=500,  # Limit response length
)
```

### Top P
```python
response = client.chat.completions.create(
    model="openai/gpt-4-turbo",
    messages=[{"role": "user", "content": "..."}],
    top_p=0.9,  # Nucleus sampling
)
```

## Understanding the Response

### Key Fields
```python
response = client.chat.completions.create(...)

# The generated text
content = response.choices[0].message.content

# Why it stopped
finish_reason = response.choices[0].finish_reason
# "stop" = natural completion
# "length" = hit max_tokens
# "tool_calls" = function calling

# Token usage (for cost tracking)
usage = response.usage
print(f"Prompt: {usage.prompt_tokens}")
print(f"Completion: {usage.completion_tokens}")
print(f"Total: {usage.total_tokens}")

# Model used (may differ if fallback triggered)
model = response.model
```

## Quick Comparison

### Compare Models
```python
models = [
    "openai/gpt-3.5-turbo",
    "anthropic/claude-3-haiku",
    "meta-llama/llama-3.1-8b-instruct",
]

prompt = "Explain quantum computing in one sentence."

for model in models:
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100
    )
    print(f"{model}:")
    print(response.choices[0].message.content)
    print()
```

## Next Steps

After hello world:
1. Explore model catalog
2. Set up fallbacks
3. Implement streaming
4. Add error handling
5. Configure for production
