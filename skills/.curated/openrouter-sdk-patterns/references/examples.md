# SDK Patterns Examples

## Python — Typed Client Wrapper

```python
import os
from dataclasses import dataclass
from openai import OpenAI

@dataclass
class ChatResult:
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float

class OpenRouterClient:
    """Typed wrapper around OpenAI SDK for OpenRouter."""

    PRICING = {
        "openai/gpt-3.5-turbo": (0.5e-6, 1.5e-6),
        "openai/gpt-4-turbo": (10e-6, 30e-6),
        "anthropic/claude-3.5-sonnet": (3e-6, 15e-6),
        "anthropic/claude-3-haiku": (0.25e-6, 1.25e-6),
    }

    def __init__(self, api_key: str | None = None, app_name: str = ""):
        self._client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key or os.environ["OPENROUTER_API_KEY"],
            max_retries=3,
            default_headers={"X-Title": app_name} if app_name else {},
        )

    def chat(self, prompt: str, model: str = "openai/gpt-3.5-turbo",
             system: str = "", max_tokens: int = 500) -> ChatResult:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self._client.chat.completions.create(
            model=model, messages=messages, max_tokens=max_tokens,
        )

        usage = response.usage
        prices = self.PRICING.get(model, (10e-6, 30e-6))
        cost = usage.prompt_tokens * prices[0] + usage.completion_tokens * prices[1]

        return ChatResult(
            content=response.choices[0].message.content,
            model=response.model,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            cost_usd=cost,
        )

    def summarize(self, text: str, max_length: int = 100) -> str:
        result = self.chat(
            prompt=f"Summarize in {max_length} words or fewer:\n\n{text}",
            model="openai/gpt-3.5-turbo",
            max_tokens=max_length * 2,
        )
        return result.content

    def classify(self, text: str, categories: list[str]) -> str:
        cats = ", ".join(categories)
        result = self.chat(
            prompt=f"Classify into one of [{cats}]: {text}",
            system="Reply with only the category name.",
            model="openai/gpt-3.5-turbo",
            max_tokens=20,
        )
        return result.content.strip()

# Usage
client = OpenRouterClient(app_name="My App")

result = client.chat("What is Python?")
print(f"Response: {result.content[:80]}...")
print(f"Cost: ${result.cost_usd:.6f}")

summary = client.summarize("Python is a high-level programming language...")
category = client.classify("Fix login bug on staging", ["feature", "bug", "docs", "ops"])
print(f"Category: {category}")
```

## TypeScript — Middleware Pipeline

```typescript
import OpenAI from "openai";

type Middleware = (req: any, next: () => Promise<any>) => Promise<any>;

class OpenRouterSDK {
  private client: OpenAI;
  private middlewares: Middleware[] = [];

  constructor(apiKey?: string) {
    this.client = new OpenAI({
      baseURL: "https://openrouter.ai/api/v1",
      apiKey: apiKey || process.env.OPENROUTER_API_KEY!,
    });
  }

  use(mw: Middleware) {
    this.middlewares.push(mw);
    return this;
  }

  async chat(prompt: string, model = "openai/gpt-3.5-turbo"): Promise<string> {
    const req = { prompt, model };

    const execute = async () => {
      const res = await this.client.chat.completions.create({
        model: req.model,
        messages: [{ role: "user", content: req.prompt }],
        max_tokens: 300,
      });
      return res;
    };

    // Run middleware chain
    let result: any;
    const chain = [...this.middlewares];
    const run = async (): Promise<any> => {
      const mw = chain.shift();
      if (mw) return mw(req, run);
      result = await execute();
      return result;
    };
    await run();

    return result.choices[0].message.content || "";
  }
}

// Logging middleware
const logger: Middleware = async (req, next) => {
  const start = performance.now();
  const result = await next();
  const ms = Math.round(performance.now() - start);
  console.log(`[${req.model}] ${ms}ms`);
  return result;
};

// Usage
const sdk = new OpenRouterSDK();
sdk.use(logger);

const answer = await sdk.chat("What is TypeScript?");
console.log(answer);
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
