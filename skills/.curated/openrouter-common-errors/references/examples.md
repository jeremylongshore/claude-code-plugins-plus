# Common Errors — Runnable Examples

## Python — Error Handling Middleware

```python
import os
import time
from openai import OpenAI, APIStatusError, RateLimitError, APIConnectionError

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

def chat_with_error_handling(
    prompt: str,
    model: str = "openai/gpt-3.5-turbo",
    max_retries: int = 3,
) -> str:
    messages = [{"role": "user", "content": prompt}]

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=500,
            )
            return response.choices[0].message.content

        except RateLimitError as e:
            retry_after = float(e.response.headers.get("Retry-After", 2 ** attempt))
            print(f"[429] Rate limited. Retrying in {retry_after:.1f}s (attempt {attempt+1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(retry_after)
            else:
                raise

        except APIStatusError as e:
            status = e.status_code

            if status == 401:
                raise RuntimeError(
                    f"[401] Invalid API key. Verify at openrouter.ai/keys."
                ) from e

            elif status == 402:
                raise RuntimeError(
                    "[402] Insufficient credits. Add credits at openrouter.ai/credits."
                ) from e

            elif status == 400:
                raise ValueError(f"[400] Bad request — {e.message}") from e

            elif status in (502, 503, 504):
                wait = 2 ** attempt
                print(f"[{status}] Provider outage. Retrying in {wait}s...")
                if attempt < max_retries - 1:
                    time.sleep(wait)
                else:
                    raise

            else:
                raise

        except APIConnectionError as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise

    raise RuntimeError("Max retries exceeded")


if __name__ == "__main__":
    result = chat_with_error_handling("What is 2 + 2?")
    print(result)

    result = chat_with_error_handling(
        "Summarize quantum computing in one sentence.",
        model="google/gemma-2-9b-it:free",
    )
    print(result)
```

## TypeScript — Error Handler with Typed Errors

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://openrouter.ai/api/v1",
  apiKey: process.env.OPENROUTER_API_KEY!,
  maxRetries: 0,
});

type ErrorCategory = "auth" | "credits" | "rate_limit" | "bad_request" | "server" | "unknown";

function classifyError(error: unknown): { category: ErrorCategory; status: number; retryable: boolean } {
  if (error instanceof OpenAI.APIStatusError) {
    const status = error.status;
    if (status === 401) return { category: "auth", status, retryable: false };
    if (status === 402) return { category: "credits", status, retryable: false };
    if (status === 429) return { category: "rate_limit", status, retryable: true };
    if (status === 400) return { category: "bad_request", status, retryable: false };
    if (status >= 500) return { category: "server", status, retryable: true };
  }
  return { category: "unknown", status: 0, retryable: false };
}

async function chatWithRetry(prompt: string, model = "openai/gpt-3.5-turbo", maxRetries = 3): Promise<string> {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const res = await client.chat.completions.create({
        model,
        messages: [{ role: "user", content: prompt }],
        max_tokens: 500,
      });
      return res.choices[0].message.content || "";
    } catch (error) {
      const { category, retryable } = classifyError(error);
      if (!retryable) {
        throw new Error(`[${category}]: ${(error as Error).message}`);
      }
      if (attempt < maxRetries - 1) {
        const waitMs = category === "rate_limit" ? 2000 * (attempt + 1) : 500 * 2 ** attempt;
        await new Promise((r) => setTimeout(r, waitMs));
      } else {
        throw error;
      }
    }
  }
  throw new Error("Max retries exceeded");
}

const answer = await chatWithRetry("Explain REST APIs briefly.");
console.log(answer);
```

## Python — Validation Middleware (Prevent 400 Errors)

```python
KNOWN_PROVIDERS = {"openai", "anthropic", "google", "meta-llama", "mistralai",
                   "cohere", "nousresearch", "microsoft", "deepseek", "phind"}

def validate_request(model: str, messages: list, max_tokens: int | None) -> None:
    if "/" not in model:
        raise ValueError(
            f"Invalid model ID '{model}' — must include provider prefix, e.g. 'openai/gpt-4'"
        )
    if not messages:
        raise ValueError("messages array cannot be empty")
    for i, msg in enumerate(messages):
        if "role" not in msg:
            raise ValueError(f"messages[{i}] missing 'role' field")
        if "content" not in msg:
            raise ValueError(f"messages[{i}] missing 'content' field")
        if msg["role"] not in ("system", "user", "assistant", "tool"):
            raise ValueError(f"messages[{i}] has invalid role '{msg['role']}'")
    if max_tokens is not None and max_tokens <= 0:
        raise ValueError(f"max_tokens must be positive, got {max_tokens}")


def safe_complete(model: str, messages: list, max_tokens: int = 500) -> str:
    validate_request(model, messages, max_tokens)
    response = client.chat.completions.create(
        model=model, messages=messages, max_tokens=max_tokens
    )
    return response.choices[0].message.content


result = safe_complete(
    model="openai/gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(result)
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
