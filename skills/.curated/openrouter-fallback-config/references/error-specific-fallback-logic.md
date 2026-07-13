# Error-Specific Fallback Logic

## Error-Specific Fallback Logic

### Conditional Fallback

```python
from openai import RateLimitError, APIError, APIConnectionError

def smart_fallback(prompt: str, primary_model: str, fallback_models: list):
    """Fallback based on error type."""
    try:
        return client.chat.completions.create(
            model=primary_model,
            messages=[{"role": "user", "content": prompt}]
        )
    except RateLimitError:
        # Rate limited - try different model immediately
        pass
    except APIConnectionError:
        # Connection issue - retry same model first
        time.sleep(1)
        try:
            return client.chat.completions.create(
                model=primary_model,
                messages=[{"role": "user", "content": prompt}]
            )
        except:
            pass
    except APIError as e:
        if e.status_code == 503:
            # Model unavailable - try fallbacks
            pass
        else:
            raise  # Don't fallback on client errors

    # Try fallbacks
    for model in fallback_models:
        try:
            return client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
        except Exception:
            continue

    raise Exception("Primary and all fallbacks failed")
```
