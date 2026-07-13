# Cost Controls Examples

## Python — Budget Enforcement Middleware

```python
import os
import threading
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

class BudgetTracker:
    """Thread-safe budget tracker for OpenRouter API costs."""

    def __init__(self, daily_limit_usd: float = 5.0):
        self.daily_limit = daily_limit_usd
        self.spent_today = 0.0
        self._lock = threading.Lock()

    # Per-token pricing (fetch from /models in production)
    PRICING = {
        "openai/gpt-4-turbo":    {"prompt": 10e-6, "completion": 30e-6},
        "openai/gpt-3.5-turbo":  {"prompt": 0.5e-6, "completion": 1.5e-6},
        "anthropic/claude-3.5-sonnet": {"prompt": 3e-6, "completion": 15e-6},
    }

    def estimate_cost(self, model: str, prompt_tokens: int, max_tokens: int) -> float:
        prices = self.PRICING.get(model, {"prompt": 10e-6, "completion": 30e-6})
        return (prompt_tokens * prices["prompt"]) + (max_tokens * prices["completion"])

    def record_cost(self, model: str, usage) -> float:
        prices = self.PRICING.get(model, {"prompt": 10e-6, "completion": 30e-6})
        cost = (usage.prompt_tokens * prices["prompt"]) + \
               (usage.completion_tokens * prices["completion"])
        with self._lock:
            self.spent_today += cost
        return cost

    def check_budget(self, estimated_cost: float) -> bool:
        with self._lock:
            return (self.spent_today + estimated_cost) <= self.daily_limit

budget = BudgetTracker(daily_limit_usd=5.0)

def budget_aware_completion(prompt: str, model: str = "openai/gpt-3.5-turbo",
                            max_tokens: int = 300) -> str:
    """Make a completion only if within budget."""
    estimated = budget.estimate_cost(model, len(prompt.split()) * 2, max_tokens)

    if not budget.check_budget(estimated):
        raise RuntimeError(
            f"Budget exceeded: ${budget.spent_today:.4f} / ${budget.daily_limit:.2f}"
        )

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
    )

    actual_cost = budget.record_cost(model, response.usage)
    print(f"[Budget] Cost: ${actual_cost:.6f} | Today: ${budget.spent_today:.4f}")
    return response.choices[0].message.content

# Usage
result = budget_aware_completion("What is Python?")
print(result)
# [Budget] Cost: $0.000225 | Today: $0.0002
```

## cURL — Check Remaining Credits

```bash
# Check how much credit remains on your key
curl -s https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  | jq '{
    used: .data.usage,
    limit: .data.limit,
    remaining: (.data.limit - .data.usage),
    pct_used: ((.data.usage / .data.limit) * 100 | floor | tostring + "%")
  }'

# Expected:
# {
#   "used": 3.42,
#   "limit": 50,
#   "remaining": 46.58,
#   "pct_used": "6%"
# }
```

## TypeScript — Per-Request Cost Logger

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://openrouter.ai/api/v1",
  apiKey: process.env.OPENROUTER_API_KEY!,
});

interface CostLog {
  timestamp: string;
  model: string;
  promptTokens: number;
  completionTokens: number;
  estimatedCostUsd: number;
}

const costHistory: CostLog[] = [];

async function trackedCompletion(prompt: string, model = "openai/gpt-3.5-turbo") {
  const response = await client.chat.completions.create({
    model,
    messages: [{ role: "user", content: prompt }],
    max_tokens: 200,
  });

  const usage = response.usage!;
  const cost = (usage.prompt_tokens * 0.5e-6) + (usage.completion_tokens * 1.5e-6);

  costHistory.push({
    timestamp: new Date().toISOString(),
    model,
    promptTokens: usage.prompt_tokens,
    completionTokens: usage.completion_tokens,
    estimatedCostUsd: cost,
  });

  const totalSpend = costHistory.reduce((s, l) => s + l.estimatedCostUsd, 0);
  console.log(`Request: $${cost.toFixed(6)} | Session total: $${totalSpend.toFixed(4)}`);
  return response.choices[0].message.content;
}

trackedCompletion("Hello!");
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
