---
name: openrouter-pricing-basics
description: |
  Understand OpenRouter pricing and cost estimation. Use when budgeting or optimizing costs. Trigger with phrases like 'openrouter pricing', 'openrouter costs', 'openrouter budget', 'openrouter token pricing'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# OpenRouter Pricing Basics

## Overview

This skill explains the OpenRouter pricing model, how to estimate costs, and strategies for cost-effective model selection.

## Prerequisites

- OpenRouter account
- Basic understanding of token-based pricing

## Instructions

Follow these steps to implement this skill:

1. **Verify Prerequisites**: Ensure all prerequisites listed above are met
2. **Review the Implementation**: Study the code examples and patterns below
3. **Adapt to Your Environment**: Modify configuration values for your setup
4. **Test the Integration**: Run the verification steps to confirm functionality
5. **Monitor in Production**: Set up appropriate logging and monitoring

## Overview

This skill explains the OpenRouter pricing model, how to estimate costs, and strategies for cost-effective model selection.

## Prerequisites

- OpenRouter account
- Basic understanding of token-based pricing

## Pricing Model

### How Pricing Works
```
OpenRouter uses pay-per-token pricing:
- You pay for tokens used (prompt + completion)
- Different models have different prices
- No subscriptions or minimum commitments
- Pre-paid credits system
```

### Token Basics
```
1 token ≈ 4 characters (English)
1 token ≈ 0.75 words

Example:
"Hello, how are you?" = ~6 tokens
1,000 words ≈ 1,333 tokens
```

## Model Pricing Tiers

### Budget Models (< $0.50/1M tokens)
```
meta-llama/llama-3.1-8b-instruct
  Prompt:     $0.06/1M tokens
  Completion: $0.06/1M tokens

mistralai/mistral-7b-instruct
  Prompt:     $0.07/1M tokens
  Completion: $0.07/1M tokens

google/gemma-7b-it
  Prompt:     $0.07/1M tokens
  Completion: $0.07/1M tokens
```

### Standard Models ($0.50-3/1M tokens)
```
anthropic/claude-3-haiku
  Prompt:     $0.25/1M tokens
  Completion: $1.25/1M tokens

openai/gpt-3.5-turbo
  Prompt:     $0.50/1M tokens
  Completion: $1.50/1M tokens

meta-llama/llama-3.1-70b-instruct
  Prompt:     $0.52/1M tokens
  Completion: $0.75/1M tokens
```

### Premium Models ($3-15/1M tokens)
```
anthropic/claude-3.5-sonnet
  Prompt:     $3.00/1M tokens
  Completion: $15.00/1M tokens

openai/gpt-4-turbo
  Prompt:     $10.00/1M tokens
  Completion: $30.00/1M tokens

anthropic/claude-3-sonnet
  Prompt:     $3.00/1M tokens
  Completion: $15.00/1M tokens
```

### Enterprise Models ($15+/1M tokens)
```
anthropic/claude-3-opus
  Prompt:     $15.00/1M tokens
  Completion: $75.00/1M tokens

openai/gpt-4
  Prompt:     $30.00/1M tokens
  Completion: $60.00/1M tokens
```

## Cost Calculation

### Formula
```
Total Cost = (Prompt Tokens × Prompt Price) + (Completion Tokens × Completion Price)
```

### Example Calculations
```python
def calculate_cost(model_pricing, prompt_tokens, completion_tokens):
    prompt_cost = prompt_tokens * model_pricing["prompt"] / 1_000_000
    completion_cost = completion_tokens * model_pricing["completion"] / 1_000_000
    return prompt_cost + completion_cost

# GPT-4 Turbo example
gpt4_pricing = {"prompt": 10.00, "completion": 30.00}
cost = calculate_cost(gpt4_pricing, 1000, 500)
# = (1000 × $10/1M) + (500 × $30/1M)
# = $0.01 + $0.015
# = $0.025 per request

# Claude 3 Haiku example
haiku_pricing = {"prompt": 0.25, "completion": 1.25}
cost = calculate_cost(haiku_pricing, 1000, 500)
# = (1000 × $0.25/1M) + (500 × $1.25/1M)
# = $0.00025 + $0.000625
# = $0.000875 per request (100x cheaper!)
```

## Credit System

### Adding Credits
```
1. Go to openrouter.ai/credits
2. Choose amount:
   - $5 (starter)
   - $20 (recommended)
   - $100 (heavy usage)
   - Custom amount
3. Pay with card
4. Credits available instantly
```

### Credit Limits per Key
```python
# Set per-key limits to control spending
# In dashboard: openrouter.ai/keys

Key: "development"
Limit: $10.00

Key: "production"
Limit: $100.00

Key: "testing"
Limit: $1.00
```

### Checking Balance
```bash
curl https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

```json
{
  "data": {
    "label": "my-key",
    "limit": 100.0,
    "usage": 23.45,
    "limit_remaining": 76.55
  }
}
```

## Cost Optimization

### Model Selection Strategy
```
Task Type → Recommended Model → Cost

Simple Q&A:
  claude-3-haiku      $0.001/request

Code completion:
  llama-3.1-70b       $0.001/request

Complex analysis:
  gpt-4-turbo         $0.03/request

Final review:
  claude-3-opus       $0.10/request
```

### Token Optimization
```python
# Reduce prompt tokens
- Remove unnecessary context
- Use concise system prompts
- Summarize long conversations

# Reduce completion tokens
- Set appropriate max_tokens
- Use stop sequences
- Request concise responses
```

### Caching Strategy
```python
import hashlib
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_completion(prompt_hash: str, model: str):
    # Cache repeated identical requests
    return client.chat.completions.create(...)

def chat_with_cache(prompt: str, model: str):
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
    return cached_completion(prompt_hash, model)
```

## Monitoring Costs

### Per-Request Cost
```python
def get_request_cost(response, model_pricing):
    usage = response.usage
    return calculate_cost(
        model_pricing,
        usage.prompt_tokens,
        usage.completion_tokens
    )

response = client.chat.completions.create(...)
cost = get_request_cost(response, {"prompt": 10, "completion": 30})
print(f"Request cost: ${cost:.6f}")
```

### Dashboard Monitoring
```
openrouter.ai/activity shows:
- Per-request costs
- Daily/weekly/monthly totals
- Model breakdown
- Usage trends
```

### Budget Alerts
```
Set up monitoring:
1. Per-key credit limits
2. Daily spend tracking
3. Alerts when approaching limits
4. Automatic key disable at limit
```

## Cost Comparison Tool

```python
def compare_model_costs(prompt: str, models: list):
    """Compare costs across models for same prompt."""
    results = []

    for model_id in models:
        response = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )

        # Get pricing from models API
        model_info = get_model_info(model_id)
        cost = calculate_cost(
            model_info["pricing"],
            response.usage.prompt_tokens,
            response.usage.completion_tokens
        )

        results.append({
            "model": model_id,
            "cost": cost,
            "tokens": response.usage.total_tokens
        })

    return sorted(results, key=lambda x: x["cost"])

# Usage
models = [
    "anthropic/claude-3-haiku",
    "openai/gpt-3.5-turbo",
    "openai/gpt-4-turbo"
]
comparison = compare_model_costs("Explain recursion", models)
```

## Billing FAQ

### When are credits charged?
```
- Immediately after each successful request
- Failed requests are not charged
- Streaming charges on completion
```

### What if I run out of credits?
```
- Requests return 402 Payment Required
- No service interruption warning
- Add credits to resume
```

### Refunds?
```
- Unused credits don't expire
- No refunds for used credits
- Contact support for issues
```

## Output

Successful execution produces:
- Working OpenRouter integration
- Verified API connectivity
- Example responses demonstrating functionality

## Error Handling

Common errors and solutions:
1. **401 Unauthorized**: Check API key format (must start with `sk-or-`)
2. **429 Rate Limited**: Implement exponential backoff
3. **500 Server Error**: Retry with backoff, check OpenRouter status page
4. **Model Not Found**: Verify model ID includes provider prefix

## Examples

See code examples in sections above for complete, runnable implementations.

## Resources

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter Models](https://openrouter.ai/models)
- [OpenRouter API Reference](https://openrouter.ai/docs/api-reference)
- [OpenRouter Status](https://status.openrouter.ai)

## Output

Successful execution produces:
- Working OpenRouter integration
- Verified API connectivity
- Example responses demonstrating functionality

## Error Handling

Common errors and solutions:
1. **401 Unauthorized**: Check API key format (must start with `sk-or-`)
2. **429 Rate Limited**: Implement exponential backoff
3. **500 Server Error**: Retry with backoff, check OpenRouter status page
4. **Model Not Found**: Verify model ID includes provider prefix

## Examples

See code examples in sections above for complete, runnable implementations.

## Resources

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter Models](https://openrouter.ai/models)
- [OpenRouter API Reference](https://openrouter.ai/docs/api-reference)
- [OpenRouter Status](https://status.openrouter.ai)
