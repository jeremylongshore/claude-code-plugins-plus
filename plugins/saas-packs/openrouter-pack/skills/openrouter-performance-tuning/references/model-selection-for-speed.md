# Model Selection For Speed

## Model Selection for Speed

### Fast Model Options

```python
FAST_MODELS = [
    {
        "id": "anthropic/claude-3-haiku",
        "avg_latency_ms": 500,
        "quality": "good"
    },
    {
        "id": "openai/gpt-3.5-turbo",
        "avg_latency_ms": 600,
        "quality": "good"
    },
    {
        "id": "meta-llama/llama-3.1-8b-instruct",
        "avg_latency_ms": 400,
        "quality": "moderate"
    },
    {
        "id": "mistralai/mistral-7b-instruct",
        "avg_latency_ms": 350,
        "quality": "moderate"
    }
]

def select_fast_model(min_quality: str = "moderate") -> str:
    """Select fastest model meeting quality threshold."""
    quality_order = ["low", "moderate", "good", "excellent"]
    min_quality_idx = quality_order.index(min_quality)

    candidates = [
        m for m in FAST_MODELS
        if quality_order.index(m["quality"]) >= min_quality_idx
    ]

    candidates.sort(key=lambda m: m["avg_latency_ms"])
    return candidates[0]["id"] if candidates else FAST_MODELS[0]["id"]
```
