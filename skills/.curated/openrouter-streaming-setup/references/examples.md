# Streaming Setup Examples

## cURL — Stream a Response

```bash
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Count from 1 to 10."}],
    "stream": true,
    "max_tokens": 100
  }'

# Each line arrives as:
# data: {"id":"gen-...","choices":[{"delta":{"content":"1"},...}]}
# data: {"id":"gen-...","choices":[{"delta":{"content":","}, ...}]}
# ...
# data: [DONE]
```

## Python — Streaming with OpenAI SDK

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

def stream_chat(prompt: str, model: str = "openai/gpt-3.5-turbo") -> str:
    """Stream a chat completion and print tokens as they arrive."""
    full_response = ""

    stream = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
        max_tokens=500,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            print(delta.content, end="", flush=True)
            full_response += delta.content

    print()  # newline after streaming completes
    return full_response

# Usage
result = stream_chat("Write a haiku about programming.")
print(f"\nFull response ({len(result)} chars): {result}")
```

## TypeScript — Streaming with Async Iterator

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://openrouter.ai/api/v1",
  apiKey: process.env.OPENROUTER_API_KEY!,
});

async function streamChat(prompt: string): Promise<string> {
  const stream = await client.chat.completions.create({
    model: "openai/gpt-3.5-turbo",
    messages: [{ role: "user", content: prompt }],
    stream: true,
    max_tokens: 500,
  });

  let fullResponse = "";

  for await (const chunk of stream) {
    const content = chunk.choices[0]?.delta?.content;
    if (content) {
      process.stdout.write(content);
      fullResponse += content;
    }
  }

  console.log(); // newline
  return fullResponse;
}

streamChat("Explain REST APIs in 3 bullet points.");
```

## Browser — Fetch API Streaming

```javascript
async function streamFromBrowser(prompt) {
  const response = await fetch("https://openrouter.ai/api/v1/chat/completions", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: "openai/gpt-3.5-turbo",
      messages: [{ role: "user", content: prompt }],
      stream: true,
      max_tokens: 300,
    }),
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop(); // keep incomplete line in buffer

    for (const line of lines) {
      if (line.startsWith("data: ") && line !== "data: [DONE]") {
        const json = JSON.parse(line.slice(6));
        const token = json.choices[0]?.delta?.content;
        if (token) document.getElementById("output").textContent += token;
      }
    }
  }
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
