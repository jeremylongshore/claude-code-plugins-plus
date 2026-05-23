# Configuration Tuning

## Configuration Tuning

### Optimal Parameters

```python
PERFORMANCE_CONFIGS = {
    "latency_optimized": {
        "model": "anthropic/claude-3-haiku",
        "max_tokens": 500,
        "temperature": 0,  # Deterministic = faster
    },
    "throughput_optimized": {
        "model": "anthropic/claude-3.5-sonnet",
        "max_tokens": 2000,
        "temperature": 0.7,
    },
    "cost_optimized": {
        "model": "meta-llama/llama-3.1-8b-instruct",
        "max_tokens": 500,
        "temperature": 0.7,
    },
    "quality_optimized": {
        "model": "anthropic/claude-3.5-sonnet",
        "max_tokens": 4000,
        "temperature": 0.7,
    }
}

def chat_with_profile(prompt: str, profile: str = "latency_optimized"):
    """Chat with performance profile."""
    config = PERFORMANCE_CONFIGS.get(profile, PERFORMANCE_CONFIGS["latency_optimized"])

    return client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        **config
    )
```
