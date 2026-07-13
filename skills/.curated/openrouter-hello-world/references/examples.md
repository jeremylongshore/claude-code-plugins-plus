# Hello World Examples

## cURL — Minimal Request

```bash
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "Say hello in three languages."}
    ],
    "max_tokens": 100
  }' | jq .
```

### Expected Response

```json
{
  "id": "gen-abc123def456",
  "model": "openai/gpt-3.5-turbo",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! (English)\nBonjour! (French)\nHola! (Spanish)"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 14,
    "completion_tokens": 18,
    "total_tokens": 32
  }
}
```

## Python — Using the OpenAI SDK

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

response = client.chat.completions.create(
    model="openai/gpt-3.5-turbo",
    messages=[
        {"role": "user", "content": "What is OpenRouter in one sentence?"}
    ],
    max_tokens=50,
)

print(response.choices[0].message.content)
# Output: "OpenRouter is a unified API gateway that provides access
#          to multiple AI models from different providers through
#          a single endpoint."

print(f"Tokens used: {response.usage.total_tokens}")
# Output: Tokens used: 42
```

## TypeScript — Using the OpenAI SDK

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://openrouter.ai/api/v1",
  apiKey: process.env.OPENROUTER_API_KEY,
});

async function helloWorld() {
  const response = await client.chat.completions.create({
    model: "openai/gpt-3.5-turbo",
    messages: [
      { role: "user", content: "What is 2 + 2? Reply with just the number." },
    ],
    max_tokens: 10,
  });

  console.log(response.choices[0].message.content);
  // Output: "4"

  console.log(`Model used: ${response.model}`);
  console.log(`Total tokens: ${response.usage?.total_tokens}`);
}

helloWorld();
```

## Trying a Free Model

```bash
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemma-2-9b-it:free",
    "messages": [
      {"role": "user", "content": "Explain what an API is in 20 words or less."}
    ],
    "max_tokens": 50
  }' | jq '.choices[0].message.content'
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
