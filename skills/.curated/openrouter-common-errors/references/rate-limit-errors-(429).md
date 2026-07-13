# Rate Limit Errors (429)

## Rate Limit Errors (429)

### Too Many Requests

```
Error: 429 Too Many Requests
{
  "error": {
    "message": "Rate limit exceeded",
    "type": "rate_limit_error"
  }
}
```

**Handling:**

```python
import time
from openai import RateLimitError

def chat_with_retry(prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(
                model="openai/gpt-4-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
        except RateLimitError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
```
