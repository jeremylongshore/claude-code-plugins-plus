# Basic Fallback Pattern

## Basic Fallback Pattern

### Simple Fallback Chain

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"]
)

FALLBACK_CHAIN = [
    "anthropic/claude-3.5-sonnet",
    "openai/gpt-4-turbo",
    "meta-llama/llama-3.1-70b-instruct",
    "mistralai/mistral-large",
]

def chat_with_fallback(prompt: str, **kwargs):
    """Try models in order until one succeeds."""
    last_error = None

    for model in FALLBACK_CHAIN:
        try:
            return client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
        except Exception as e:
            last_error = e
            print(f"Model {model} failed: {e}")
            continue

    raise last_error or Exception("All fallback models failed")
```

### TypeScript Fallback

```typescript
const FALLBACK_CHAIN = [
  'anthropic/claude-3.5-sonnet',
  'openai/gpt-4-turbo',
  'meta-llama/llama-3.1-70b-instruct',
];

async function chatWithFallback(
  prompt: string,
  options: Partial<OpenAI.Chat.ChatCompletionCreateParams> = {}
): Promise<OpenAI.Chat.ChatCompletion> {
  let lastError: Error | null = null;

  for (const model of FALLBACK_CHAIN) {
    try {
      return await client.chat.completions.create({
        model,
        messages: [{ role: 'user', content: prompt }],
        ...options,
      });
    } catch (error) {
      lastError = error as Error;
      console.error(`Model ${model} failed:`, error);
      continue;
    }
  }

  throw lastError || new Error('All fallback models failed');
}
```
