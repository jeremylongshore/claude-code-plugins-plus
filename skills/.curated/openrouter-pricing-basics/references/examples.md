# Pricing Basics Examples

## cURL — Check Model Pricing

```bash
# Get pricing for a specific model
curl -s https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  | jq '.data[] | select(.id == "openai/gpt-4-turbo") | {
      id,
      prompt_per_1M: (.pricing.prompt | tonumber * 1000000 | tostring + " USD"),
      completion_per_1M: (.pricing.completion | tonumber * 1000000 | tostring + " USD"),
      context_length
    }'

# Expected:
# {
#   "id": "openai/gpt-4-turbo",
#   "prompt_per_1M": "10 USD",
#   "completion_per_1M": "30 USD",
#   "context_length": 128000
# }
```

## Python — Cost Calculator

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

# Model pricing (per token) — fetch from /models in production
PRICING = {
    "openai/gpt-4-turbo":         {"prompt": 10e-6, "completion": 30e-6},
    "openai/gpt-3.5-turbo":       {"prompt": 0.5e-6, "completion": 1.5e-6},
    "anthropic/claude-3.5-sonnet": {"prompt": 3e-6, "completion": 15e-6},
    "anthropic/claude-3-haiku":    {"prompt": 0.25e-6, "completion": 1.25e-6},
    "google/gemma-2-9b-it:free":   {"prompt": 0, "completion": 0},
}

def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Calculate the cost of a single request in USD."""
    prices = PRICING.get(model, {"prompt": 0, "completion": 0})
    return (prompt_tokens * prices["prompt"]) + (completion_tokens * prices["completion"])

def estimate_monthly_cost(model: str, requests_per_day: int,
                          avg_prompt_tokens: int, avg_completion_tokens: int) -> float:
    """Estimate monthly cost for a given usage pattern."""
    cost_per_request = calculate_cost(model, avg_prompt_tokens, avg_completion_tokens)
    return cost_per_request * requests_per_day * 30

# Example: Compare costs across models
prompt = "Summarize this 500-word article about climate change."
response = client.chat.completions.create(
    model="openai/gpt-3.5-turbo",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=200,
)

usage = response.usage
actual_cost = calculate_cost(response.model, usage.prompt_tokens, usage.completion_tokens)
print(f"Request cost: ${actual_cost:.6f}")
print(f"  Prompt tokens: {usage.prompt_tokens}")
print(f"  Completion tokens: {usage.completion_tokens}")

# Monthly estimate
for model, prices in PRICING.items():
    monthly = estimate_monthly_cost(model, requests_per_day=1000,
                                     avg_prompt_tokens=500, avg_completion_tokens=200)
    print(f"{model}: ${monthly:.2f}/month at 1K req/day")
```

### Expected Output

```
Request cost: $0.000276
  Prompt tokens: 52
  Completion tokens: 148
openai/gpt-4-turbo: $330.00/month at 1K req/day
openai/gpt-3.5-turbo: $16.50/month at 1K req/day
anthropic/claude-3.5-sonnet: $135.00/month at 1K req/day
anthropic/claude-3-haiku: $11.25/month at 1K req/day
google/gemma-2-9b-it:free: $0.00/month at 1K req/day
```

## cURL — Check Credit Balance

```bash
curl -s https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  | jq '{credits_used: .data.usage, credit_limit: .data.limit,
         remaining: (.data.limit - .data.usage)}'

# Expected:
# {
#   "credits_used": 2.34,
#   "credit_limit": 50,
#   "remaining": 47.66
# }
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
