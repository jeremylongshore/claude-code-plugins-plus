---
name: klingai-common-errors
description: |
  Diagnose and fix common Kling AI API errors. Use when troubleshooting failed video generation
  or API issues. Trigger with phrases like 'kling ai error', 'klingai not working', 'fix klingai',
  'klingai failed'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Kling AI Common Errors

## Overview

This skill provides a comprehensive guide to identifying, diagnosing, and resolving the most common Kling AI API errors during video generation.

## Prerequisites

- Kling AI integration experiencing errors
- Access to request/response logs
- API key configured

## Instructions

Follow these steps to diagnose and fix errors:

1. **Identify Error Code**: Check the HTTP status and error message
2. **Review Error Details**: Examine the full error response
3. **Apply Fix**: Implement the recommended solution
4. **Verify Fix**: Test with a simple request
5. **Prevent Recurrence**: Add proper error handling

## Error Reference

### HTTP 401 - Unauthorized
```
Error: "Invalid or missing API key"

Causes:
- API key not set in environment
- API key is invalid or revoked
- Missing Authorization header
- Wrong header format

Solutions:
1. Verify API key exists: echo $KLINGAI_API_KEY
2. Check key format (no extra spaces)
3. Ensure header is: "Authorization: Bearer <key>"
4. Generate new key if revoked

Code fix:
```python
import os

api_key = os.environ.get("KLINGAI_API_KEY")
if not api_key:
    raise ValueError("KLINGAI_API_KEY environment variable not set")

headers = {
    "Authorization": f"Bearer {api_key}",  # Note: Bearer prefix
    "Content-Type": "application/json"
}
```

### HTTP 400 - Bad Request
```
Error: "Invalid request parameters"

Common causes:
- Missing required fields (prompt)
- Invalid duration value
- Unsupported aspect ratio
- Malformed JSON

Solutions:
1. Check all required fields are present
2. Validate parameter ranges
3. Use supported aspect ratios
4. Validate JSON syntax

Code fix:
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

### HTTP 403 - Forbidden
```
Error: "Access denied" or "Content policy violation"

Causes:
- Account suspended
- Feature not available on plan
- Content violates usage policy
- Geographic restrictions

Solutions:
1. Check account status at klingai.com
2. Verify plan includes requested feature
3. Review and modify prompt content
4. Use VPN if geographic issue

Content policy check:
```python
BLOCKED_TERMS = [
    # Add known blocked terms
]

def check_content_policy(prompt: str) -> bool:
    """Pre-check prompt for likely policy violations."""
    prompt_lower = prompt.lower()
    for term in BLOCKED_TERMS:
        if term in prompt_lower:
            return False
    return True
```

### HTTP 429 - Rate Limited
```
Error: "Too many requests"

Causes:
- Exceeded requests per minute
- Exceeded concurrent jobs
- Burst limit hit

Solutions:
1. Implement exponential backoff
2. Add request queuing
3. Respect Retry-After header
4. Upgrade plan for higher limits

Code fix:
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

### HTTP 402 - Payment Required
```
Error: "Insufficient credits"

Causes:
- Account out of credits
- Credit limit reached on API key
- Payment method failed

Solutions:
1. Check credit balance
2. Purchase additional credits
3. Update payment method
4. Set up auto-reload

Credit check:
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

### HTTP 500/502/503 - Server Errors
```
Error: "Internal server error" / "Service unavailable"

Causes:
- Temporary service outage
- High load on servers
- Infrastructure issues

Solutions:
1. Wait and retry with backoff
2. Check status.klingai.com
3. Use different region if available
4. Contact support if persistent

Retry logic:
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

### Generation Failed
```
Error: "Video generation failed"

Causes:
- Complex prompt that couldn't be processed
- Timeout during generation
- Internal processing error

Solutions:
1. Simplify the prompt
2. Reduce duration
3. Try different model
4. Split into multiple generations

Diagnostic code:
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

## Error Handling Best Practices

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

## Output

Successful execution produces:
- Identified error cause
- Applied fix
- Verified resolution
- Improved error handling

## Error Handling

See detailed error reference above for all common errors and solutions.

## Examples

See code examples above for complete, runnable implementations.

## Resources

- [Kling AI Error Codes](https://docs.klingai.com/errors)
- [Status Page](https://status.klingai.com)
- [Support](https://klingai.com/support)
