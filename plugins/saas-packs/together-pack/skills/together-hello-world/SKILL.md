---
name: together-hello-world
description: |
  Run inference with Together AI -- chat completions, streaming, and model selection.
  Use when testing open-source models, comparing model performance,
  or learning the Together AI API.
  Trigger: "together hello world, together AI example, run llama".
allowed-tools: Read, Write, Edit, Bash(pip:*), Bash(python3:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, inference, together]
compatible-with: claude-code
---

# Together AI Hello World

## Overview

Run chat completions with open-source models via Together AI's OpenAI-compatible API. Supports Llama, Mixtral, Qwen, and 100+ models. Key endpoints: `/v1/chat/completions`, `/v1/completions`, `/v1/embeddings`, `/v1/images/generations`.

## Instructions

### Step 1: Chat Completions

```python
from together import Together

client = Together()

response = client.chat.completions.create(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
    messages=[
        {"role": "system", "content": "You are a helpful coding assistant."},
        {"role": "user", "content": "Write a Python function to calculate fibonacci numbers"},
    ],
    max_tokens=500,
    temperature=0.7,
    top_p=0.9,
)

print(response.choices[0].message.content)
print(f"Tokens: {response.usage.prompt_tokens} in, {response.usage.completion_tokens} out")
```

### Step 2: Streaming

```python
stream = client.chat.completions.create(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
    messages=[{"role": "user", "content": "Explain quantum computing"}],
    stream=True,
    max_tokens=200,
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### Step 3: Image Generation

```python
response = client.images.generate(
    model="black-forest-labs/FLUX.1-schnell-Free",
    prompt="A sunset over mountains, digital art style",
    width=1024, height=768,
    n=1,
)
print(f"Image URL: {response.data[0].url}")
```

### Step 4: Embeddings

```python
response = client.embeddings.create(
    model="togethercomputer/m2-bert-80M-8k-retrieval",
    input=["Hello world", "Together AI is great"],
)
print(f"Embedding dim: {len(response.data[0].embedding)}")
```

### Step 5: Node.js with OpenAI Client

```typescript
import OpenAI from 'openai';

const together = new OpenAI({
  apiKey: process.env.TOGETHER_API_KEY,
  baseURL: 'https://api.together.xyz/v1',
});

const chat = await together.chat.completions.create({
  model: 'meta-llama/Llama-3.3-70B-Instruct-Turbo',
  messages: [{ role: 'user', content: 'Hello!' }],
});
console.log(chat.choices[0].message.content);
```

## Output

```
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

Tokens: 28 in, 45 out
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Model not found` | Wrong model ID | Check docs.together.ai/docs/inference-models |
| Empty response | max_tokens too low | Increase max_tokens |
| `429 rate limit` | Too many requests | Implement backoff |
| Slow response | Large model | Try Turbo variant or smaller model |

## Resources

- [Chat Completions API](https://docs.together.ai/reference/chat-completions-1)
- [Supported Models](https://docs.together.ai/docs/inference-models)
- [Image Generation](https://docs.together.ai/docs/images-overview)

## Next Steps

Proceed to `together-local-dev-loop` for development workflow.
