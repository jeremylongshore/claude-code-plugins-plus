# Cost Surprises

## Cost Surprises

### No max_tokens Limit

```python
# ❌ Risky: No response limit
response = client.chat.completions.create(
    model="anthropic/claude-3-opus",  # Expensive model
    messages=[{"role": "user", "content": prompt}]
    # Missing max_tokens - could be very long response
)

# ✓ Better: Set limits
response = client.chat.completions.create(
    model="anthropic/claude-3-opus",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=1000  # Control costs
)
```

### Wrong Model for Task

```python
# ❌ Expensive: Using Opus for simple tasks
response = client.chat.completions.create(
    model="anthropic/claude-3-opus",  # $75/M completion tokens
    messages=[{"role": "user", "content": "What's 2+2?"}]
)

# ✓ Cost-effective: Use Haiku for simple tasks
response = client.chat.completions.create(
    model="anthropic/claude-3-haiku",  # $1.25/M completion tokens
    messages=[{"role": "user", "content": "What's 2+2?"}]
)
```

### Not Tracking Costs

```python
# ❌ Problem: No cost visibility
for prompt in prompts:
    response = client.chat.completions.create(...)

# ✓ Better: Track costs
total_cost = 0
for prompt in prompts:
    response = client.chat.completions.create(...)
    cost = calculate_cost(response.usage)
    total_cost += cost
    if total_cost > budget:
        raise Exception("Budget exceeded")
```
