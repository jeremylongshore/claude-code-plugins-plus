# Retry Strategies

## Retry Strategies

### Exponential Backoff

```python
import time
import random

def exponential_backoff(attempt: int, base: float = 1.0, max_wait: float = 60.0):
    """Calculate wait time with jitter."""
    wait = min(base * (2 ** attempt), max_wait)
    jitter = random.uniform(0, wait * 0.1)
    return wait + jitter

def chat_with_backoff(prompt: str, model: str, max_retries: int = 5):
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
        except RateLimitError:
            if attempt == max_retries - 1:
                raise
            wait_time = exponential_backoff(attempt)
            print(f"Rate limited, waiting {wait_time:.1f}s...")
            time.sleep(wait_time)
```

### With Retry-After Header

```python
def get_retry_after(error) -> float:
    """Extract Retry-After from error response."""
    if hasattr(error, 'response') and error.response:
        retry_after = error.response.headers.get('Retry-After')
        if retry_after:
            return float(retry_after)
    return 1.0  # Default

def chat_with_retry_header(prompt: str, model: str, max_retries: int = 5):
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            wait_time = get_retry_after(e)
            time.sleep(wait_time)
```
