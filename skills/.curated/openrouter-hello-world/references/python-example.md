# Python Example

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
