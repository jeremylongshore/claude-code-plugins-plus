# Groq SDK — Python Patterns

Full Python implementations for the `groq` package. The client reads `GROQ_API_KEY` from the environment automatically.

## Step 6: Python Patterns (sync, async, streaming)

```python
# Synchronous client
from groq import Groq

client = Groq()  # Reads GROQ_API_KEY from env

completion = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": "Hello"}],
)

# Async client
from groq import AsyncGroq

async_client = AsyncGroq()

async def async_complete(prompt: str) -> str:
    completion = await async_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
    )
    return completion.choices[0].message.content

# Streaming
stream = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": "Hello"}],
    stream=True,
)
for chunk in stream:
    content = chunk.choices[0].delta.content
    if content:
        print(content, end="")
```
