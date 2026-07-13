# Exponential Backoff

## Exponential Backoff

```python
import time
import random
from functools import wraps
from typing import TypeVar, Callable

T = TypeVar('T')

def exponential_backoff(
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True
) -> Callable:
    """Decorator for exponential backoff on rate limits."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if "429" not in str(e) and "rate" not in str(e).lower():
                        raise  # Not a rate limit error

                    last_exception = e

                    if attempt == max_retries - 1:
                        raise

                    # Calculate delay
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)

                    # Add jitter to prevent thundering herd
                    if jitter:
                        delay = delay * (0.5 + random.random())

                    print(f"Rate limited. Attempt {attempt + 1}/{max_retries}. "
                          f"Waiting {delay:.2f}s...")
                    time.sleep(delay)

            raise last_exception

        return wrapper
    return decorator

# Usage
@exponential_backoff(max_retries=5, base_delay=2.0)
def generate_video(prompt: str):
    # API call here
    pass
```
