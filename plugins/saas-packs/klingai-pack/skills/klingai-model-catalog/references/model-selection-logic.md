# Model Selection Logic

## Model Selection Logic

```python
def select_model(
    duration: int,
    resolution: str,
    quality: str = "standard",
    budget_per_second: float = 0.10
) -> str:
    """Select the best model for requirements."""

    # Duration constraints
    if duration > 30:
        return "kling-pro"

    # Quality requirements
    if quality == "premium" or resolution == "4k":
        if budget_per_second >= 0.20:
            return "kling-pro"
        return "kling-v1.5"

    # Budget optimization
    if budget_per_second < 0.10:
        return "kling-v1"

    # Default to enhanced
    return "kling-v1.5"

# Usage
model = select_model(duration=15, resolution="1080p", quality="high")
print(f"Recommended model: {model}")
```
