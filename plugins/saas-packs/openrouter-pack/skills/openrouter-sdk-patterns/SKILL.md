---
name: openrouter-sdk-patterns
description: |
  SDK usage patterns for OpenRouter. Triggers on "openrouter sdk",
  "openrouter python", "openrouter typescript", "openrouter client".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# OpenRouter SDK Patterns

## Python with OpenAI SDK

### Basic Setup
```python
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
    default_headers={
        "HTTP-Referer": "https://your-app.com",
        "X-Title": "Your App Name",
    }
)
```

### Synchronous Requests
```python
def chat(prompt: str, model: str = "openai/gpt-4-turbo") -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
```

### Async Requests
```python
from openai import AsyncOpenAI
import asyncio

async_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)

async def chat_async(prompt: str, model: str = "openai/gpt-4-turbo") -> str:
    response = await async_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# Usage
result = asyncio.run(chat_async("Hello!"))
```

### Streaming
```python
def stream_chat(prompt: str, model: str = "openai/gpt-4-turbo"):
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

    return full_response
```

## TypeScript/Node.js

### Basic Setup
```typescript
import OpenAI from 'openai';

const client = new OpenAI({
  baseURL: 'https://openrouter.ai/api/v1',
  apiKey: process.env.OPENROUTER_API_KEY,
  defaultHeaders: {
    'HTTP-Referer': 'https://your-app.com',
    'X-Title': 'Your App Name',
  },
});
```

### Basic Request
```typescript
async function chat(prompt: string, model = 'openai/gpt-4-turbo'): Promise<string> {
  const response = await client.chat.completions.create({
    model,
    messages: [{ role: 'user', content: prompt }],
  });
  return response.choices[0].message.content || '';
}
```

### Streaming
```typescript
async function streamChat(prompt: string, model = 'openai/gpt-4-turbo') {
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
  return fullResponse;
}
```

### With Types
```typescript
interface ChatOptions {
  model?: string;
  temperature?: number;
  maxTokens?: number;
  systemPrompt?: string;
}

async function chat(
  prompt: string,
  options: ChatOptions = {}
): Promise<string> {
  const {
    model = 'openai/gpt-4-turbo',
    temperature = 0.7,
    maxTokens = 1000,
    systemPrompt,
  } = options;

  const messages: OpenAI.Chat.ChatCompletionMessageParam[] = [];

  if (systemPrompt) {
    messages.push({ role: 'system', content: systemPrompt });
  }
  messages.push({ role: 'user', content: prompt });

  const response = await client.chat.completions.create({
    model,
    messages,
    temperature,
    max_tokens: maxTokens,
  });

  return response.choices[0].message.content || '';
}
```

## Wrapper Class Pattern

### Python
```python
class OpenRouterClient:
    def __init__(
        self,
        api_key: str = None,
        default_model: str = "openai/gpt-4-turbo",
        app_name: str = None,
        app_url: str = None,
    ):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key or os.environ.get("OPENROUTER_API_KEY"),
            default_headers={
                "HTTP-Referer": app_url or "",
                "X-Title": app_name or "",
            }
        )
        self.default_model = default_model

    def chat(
        self,
        prompt: str,
        model: str = None,
        system: str = None,
        **kwargs
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=model or self.default_model,
            messages=messages,
            **kwargs
        )
        return response.choices[0].message.content

    def stream(self, prompt: str, model: str = None, **kwargs):
        response = self.client.chat.completions.create(
            model=model or self.default_model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            **kwargs
        )
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

# Usage
router = OpenRouterClient(
    default_model="anthropic/claude-3.5-sonnet",
    app_name="My App"
)
response = router.chat("Hello!")
```

### TypeScript
```typescript
class OpenRouterClient {
  private client: OpenAI;
  private defaultModel: string;

  constructor(options: {
    apiKey?: string;
    defaultModel?: string;
    appName?: string;
    appUrl?: string;
  } = {}) {
    this.client = new OpenAI({
      baseURL: 'https://openrouter.ai/api/v1',
      apiKey: options.apiKey || process.env.OPENROUTER_API_KEY,
      defaultHeaders: {
        'HTTP-Referer': options.appUrl || '',
        'X-Title': options.appName || '',
      },
    });
    this.defaultModel = options.defaultModel || 'openai/gpt-4-turbo';
  }

  async chat(prompt: string, options: ChatOptions = {}): Promise<string> {
    const response = await this.client.chat.completions.create({
      model: options.model || this.defaultModel,
      messages: [{ role: 'user', content: prompt }],
      ...options,
    });
    return response.choices[0].message.content || '';
  }

  async *stream(prompt: string, options: ChatOptions = {}) {
    const stream = await this.client.chat.completions.create({
      model: options.model || this.defaultModel,
      messages: [{ role: 'user', content: prompt }],
      stream: true,
      ...options,
    });

    for await (const chunk of stream) {
      yield chunk.choices[0]?.delta?.content || '';
    }
  }
}
```

## Error Handling Pattern

```python
from openai import APIError, RateLimitError, APIConnectionError

def safe_chat(prompt: str, model: str, retries: int = 3) -> str:
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except RateLimitError:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
        except APIConnectionError:
            if attempt < retries - 1:
                time.sleep(1)
                continue
            raise
        except APIError as e:
            raise Exception(f"API error: {e}")
```

## Batch Processing Pattern

```python
import asyncio

async def batch_chat(prompts: list[str], model: str, max_concurrent: int = 5):
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_one(prompt: str) -> str:
        async with semaphore:
            response = await async_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content

    tasks = [process_one(p) for p in prompts]
    return await asyncio.gather(*tasks)

# Usage
prompts = ["Question 1", "Question 2", "Question 3"]
results = asyncio.run(batch_chat(prompts, "openai/gpt-4-turbo"))
```
