# Python With Openai Sdk

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
