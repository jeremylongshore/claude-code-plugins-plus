# Migration From Direct Api To Sdk

## Migration from Direct API to SDK

### Before (Raw Requests)

```python
import requests

response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    },
    json={
        "model": "openai/gpt-4-turbo",
        "messages": [{"role": "user", "content": "Hello"}]
    }
)
result = response.json()
content = result["choices"][0]["message"]["content"]
```

### After (OpenAI SDK)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)

response = client.chat.completions.create(
    model="openai/gpt-4-turbo",
    messages=[{"role": "user", "content": "Hello"}]
)
content = response.choices[0].message.content
```

### Benefits of SDK

```
✓ Automatic retries
✓ Better error types
✓ Type hints / TypeScript types
✓ Streaming support built-in
✓ Consistent interface
```
