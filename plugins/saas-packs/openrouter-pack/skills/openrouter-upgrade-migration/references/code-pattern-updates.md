# Code Pattern Updates

## Code Pattern Updates

### Sync to Async Migration

```python
# Before: Synchronous
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)

def chat(prompt: str) -> str:
    response = client.chat.completions.create(
        model="openai/gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# After: Asynchronous
from openai import AsyncOpenAI

async_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)

async def chat_async(prompt: str) -> str:
    response = await async_client.chat.completions.create(
        model="openai/gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
```

### Adding Streaming Support

```python
# Before: Non-streaming
def chat(prompt: str) -> str:
    response = client.chat.completions.create(
        model="openai/gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# After: With streaming option
def chat(prompt: str, stream: bool = False):
    if stream:
        return stream_chat(prompt)
    else:
        response = client.chat.completions.create(
            model="openai/gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

def stream_chat(prompt: str):
    stream = client.chat.completions.create(
        model="openai/gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )
    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
```
