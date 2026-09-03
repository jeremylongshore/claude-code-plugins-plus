# OrcaRouter Install & Auth — References

## Provider-prefixed model IDs

OrcaRouter exposes a `provider/model` namespace. The `/v1/models` endpoint is the source of truth for what your account can access; the examples below are the categories you will typically see:

| Prefix | Examples | Notes |
| ------ | -------- | ----- |
| `orcarouter/*` | `orcarouter/auto`, `orcarouter/free` | First-party named routers |
| `orcarouter/fusion` | `orcarouter/fusion`, `orcarouter/fusion-flash`, `orcarouter/fusion-mini` | Fusion panels (frontier/budget panel + judge) |
| `openai/*` | `openai/gpt-4o-mini`, `openai/gpt-5` | OpenAI models through the gateway |
| `anthropic/*` | `anthropic/claude-sonnet-4.6`, `anthropic/claude-opus-4.7` | Anthropic models through the gateway |
| `google/*` | `google/gemini-2.5-flash`, `google/gemini-3-pro-preview` | Google models |
| `deepseek/*` | `deepseek/deepseek-chat`, `deepseek/deepseek-reasoner` | DeepSeek models |
| `*/*-free` | `deepseek/deepseek-v4-flash-free` | No-credit models (see [Free Models](https://docs.orcarouter.ai/routing/free-models)) |

See [Models](https://docs.orcarouter.ai/getting-started/models) for the full catalog and provider table.

## Base URL

All requests go to `https://api.orcarouter.ai/v1`. It is OpenAI-compatible, so the OpenAI SDK, cURL with the OpenAI shape, and any OpenAI-compatible client work unchanged.

## Verifying a key

There is no public `/v1/auth/key` identity endpoint in the current API surface. Verify a key with a real request: list models (`GET /v1/models`) or send a minimal chat completion. For account-level usage and quota, the OpenAI-shape billing endpoints are `GET /v1/dashboard/billing/usage` and `GET /v1/dashboard/billing/subscription` (see [Billing & usage](https://docs.orcarouter.ai/operations/billing-and-usage)).

## Full SDK variants

### Python

```python
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://api.orcarouter.ai/v1",
    api_key=os.environ["ORCAROUTER_API_KEY"],
)

r = client.chat.completions.create(
    model="orcarouter/fusion",
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=100,
)
print(r.choices[0].message.content)
print(r.model, r.usage.total_tokens)
```

### TypeScript

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://api.orcarouter.ai/v1",
  apiKey: process.env.ORCAROUTER_API_KEY,
});

const r = await client.chat.completions.create({
  model: "orcarouter/fusion",
  messages: [{ role: "user", content: "Hello" }],
  max_tokens: 100,
});

console.log(r.choices[0].message.content);
```

## Environment variables

| Variable | Example | Purpose |
| -------- | ------- | ------- |
| `ORCAROUTER_API_KEY` | `sk-orca-...` | The gateway key |
| `ORCAROUTER_BASE_URL` | `https://api.orcarouter.ai/v1` | Override point; default is the above |

Never commit keys. Use a `.env` file, a secret manager, or the host harness's secret storage.
