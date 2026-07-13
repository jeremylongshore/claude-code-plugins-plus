# Basic Streaming

## Basic Streaming

### Python Streaming

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"]
)

def stream_chat(prompt: str, model: str = "openai/gpt-4-turbo"):
    """Stream response and print in real-time."""
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

    print()  # Newline at end
    return full_response

# Usage
response = stream_chat("Explain quantum computing")
```

### TypeScript Streaming

```typescript
import OpenAI from 'openai';

const client = new OpenAI({
  baseURL: 'https://openrouter.ai/api/v1',
  apiKey: process.env.OPENROUTER_API_KEY,
});

async function streamChat(prompt: string, model = 'openai/gpt-4-turbo'): Promise<string> {
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
  console.log();
  return fullResponse;
}

// Usage
const response = await streamChat('Explain quantum computing');
```
