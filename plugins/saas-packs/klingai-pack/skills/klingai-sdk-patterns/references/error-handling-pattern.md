# Error Handling Pattern

## Error Handling Pattern

```python
from enum import Enum

class KlingAIError(Exception):
    """Base exception for Kling AI errors."""
    pass

class AuthenticationError(KlingAIError):
    """Invalid or missing API key."""
    pass

class RateLimitError(KlingAIError):
    """Rate limit exceeded."""
    def __init__(self, retry_after: int = None):
        self.retry_after = retry_after
        super().__init__(f"Rate limited. Retry after {retry_after}s")

class ContentPolicyError(KlingAIError):
    """Content violates usage policy."""
    pass

class GenerationError(KlingAIError):
    """Video generation failed."""
    pass

def handle_api_error(response: requests.Response):
    """Convert HTTP errors to specific exceptions."""
    if response.status_code == 401:
        raise AuthenticationError("Invalid API key")
    elif response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 60))
        raise RateLimitError(retry_after)
    elif response.status_code == 400:
        error = response.json().get("error", {})
        if "content_policy" in error.get("code", ""):
            raise ContentPolicyError(error.get("message"))
        raise KlingAIError(error.get("message", "Bad request"))
    elif response.status_code >= 500:
        raise KlingAIError(f"Server error: {response.status_code}")
```
