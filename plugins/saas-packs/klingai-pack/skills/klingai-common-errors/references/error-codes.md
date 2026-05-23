# Kling AI Error Codes Reference

## HTTP 401 - Unauthorized

**Error:** `Invalid or missing API key`

**Causes:**

- API key not set in environment
- API key is invalid or revoked
- Missing Authorization header
- Wrong header format

**Solution:**

```python
import os

api_key = os.environ.get("KLINGAI_API_KEY")
if not api_key:
    raise ValueError("KLINGAI_API_KEY environment variable not set")

headers = {
    "Authorization": f"Bearer {api_key}",  # Note: Bearer prefix required
    "Content-Type": "application/json"
}
```

## HTTP 400 - Bad Request

**Error:** `Invalid request parameters`

**Causes:**

- Missing required fields (prompt)
- Invalid duration value
- Unsupported aspect ratio
- Malformed JSON

**Solution:**

```python
def validate_request(params: dict) -> list[str]:
    """Validate request parameters before sending."""
    errors = []

    # Required fields
    if not params.get("prompt"):
        errors.append("prompt is required")

    # Duration range
    duration = params.get("duration", 5)
    if not 1 <= duration <= 60:
        errors.append("duration must be 1-60 seconds")

    # Aspect ratio
    valid_ratios = ["16:9", "9:16", "1:1", "4:3"]
    if params.get("aspect_ratio") not in valid_ratios:
        errors.append(f"aspect_ratio must be one of {valid_ratios}")

    return errors
```

## HTTP 403 - Forbidden

**Error:** `Access denied` or `Content policy violation`

**Causes:**

- Account suspended
- Feature not available on plan
- Content violates usage policy
- Geographic restrictions

**Solution:**

```python
BLOCKED_TERMS = []  # Add known blocked terms

def check_content_policy(prompt: str) -> bool:
    """Pre-check prompt for likely policy violations."""
    prompt_lower = prompt.lower()
    for term in BLOCKED_TERMS:
        if term in prompt_lower:
            return False
    return True
```

## HTTP 429 - Rate Limited

**Error:** `Too many requests`

**Causes:**

- Exceeded requests per minute
- Exceeded concurrent jobs
- Burst limit hit

**Solution:**

```python
import time
from functools import wraps

def rate_limit_handler(max_retries: int = 5):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if "429" in str(e):
                        wait_time = 2 ** attempt
                        print(f"Rate limited. Waiting {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        raise
            raise Exception("Max retries exceeded")
        return wrapper
    return decorator
```

## HTTP 402 - Payment Required

**Error:** `Insufficient credits`

**Causes:**

- Account out of credits
- Credit limit reached on API key
- Payment method failed

**Solution:**

```python
def check_credits_before_generation(required: int) -> bool:
    """Verify sufficient credits before generation."""
    response = requests.get(
        "https://api.klingai.com/v1/account",
        headers=headers
    )
    available = response.json().get("credits", 0)
    return available >= required
```

## HTTP 500/502/503 - Server Errors

**Error:** `Internal server error` or `Service unavailable`

**Causes:**

- Temporary service outage
- High load on servers
- Infrastructure issues

**Solution:**

```python
def retry_on_server_error(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if any(code in str(e) for code in ["500", "502", "503"]):
                wait = (attempt + 1) * 10
                print(f"Server error. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise
    raise Exception("Server error persisted after retries")
```

## Generation Failed

**Error:** `Video generation failed`

**Causes:**

- Complex prompt that couldn't be processed
- Timeout during generation
- Internal processing error

**Solution:**

```python
def handle_generation_failure(job_id: str, error: dict):
    """Diagnose and handle generation failure."""
    error_code = error.get("code", "unknown")
    error_message = error.get("message", "No details")

    if "timeout" in error_message.lower():
        print("Suggestion: Reduce duration or simplify prompt")
    elif "content" in error_message.lower():
        print("Suggestion: Modify prompt to comply with content policy")
    elif "complexity" in error_message.lower():
        print("Suggestion: Simplify the scene description")

    return {
        "job_id": job_id,
        "error_code": error_code,
        "error_message": error_message,
        "recoverable": error_code not in ["content_policy", "account_suspended"]
    }
```

## Unified Error Handler

```python
class KlingAIError(Exception):
    """Base exception for Kling AI errors."""
    def __init__(self, status_code: int, message: str, details: dict = None):
        self.status_code = status_code
        self.message = message
        self.details = details or {}
        super().__init__(f"[{status_code}] {message}")

def handle_response(response):
    """Convert API response to appropriate exception if error."""
    if response.status_code >= 400:
        error_data = response.json() if response.text else {}
        raise KlingAIError(
            status_code=response.status_code,
            message=error_data.get("error", {}).get("message", "Unknown error"),
            details=error_data
        )
    return response.json()
```
