---
name: openrouter-common-errors
description: |
  Diagnose and fix common OpenRouter API errors. Use when troubleshooting failed requests. Trigger with phrases like 'openrouter error', 'openrouter not working', 'openrouter 401', 'openrouter 429', 'fix openrouter'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# OpenRouter Common Errors

## Overview

This skill provides a comprehensive guide to identifying, diagnosing, and resolving the most common OpenRouter API errors.

## Prerequisites

- OpenRouter integration experiencing errors
- Access to request/response logs

## Instructions

Follow these steps to implement this skill:

1. **Verify Prerequisites**: Ensure all prerequisites listed above are met
2. **Review the Implementation**: Study the code examples and patterns below
3. **Adapt to Your Environment**: Modify configuration values for your setup
4. **Test the Integration**: Run the verification steps to confirm functionality
5. **Monitor in Production**: Set up appropriate logging and monitoring

## Overview

This skill provides a comprehensive guide to identifying, diagnosing, and resolving the most common OpenRouter API errors.

## Prerequisites

- OpenRouter integration experiencing errors
- Access to request/response logs

## Authentication Errors (401)

### Invalid API Key
```
Error: 401 Unauthorized
{
  "error": {
    "message": "Invalid API key",
    "type": "authentication_error"
  }
}
```

**Causes:**
```
1. Wrong key format (should start with sk-or-)
2. Key revoked or expired
3. Missing Bearer prefix in header
4. Environment variable not loaded
```

**Fixes:**
```python
# Check key format
import os
key = os.environ.get("OPENROUTER_API_KEY", "")
print(f"Key prefix: {key[:10]}...")  # Should be sk-or-...

# Verify header format
headers = {
    "Authorization": f"Bearer {key}",  # Must have "Bearer "
    "Content-Type": "application/json"
}
```

### Missing Authorization Header
```python
# Wrong
requests.post(url, json=data)

# Right
requests.post(url, json=data, headers={"Authorization": f"Bearer {key}"})
```

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

## Payment Errors (402)

### Insufficient Credits
```
Error: 402 Payment Required
{
  "error": {
    "message": "Insufficient credits",
    "type": "payment_required"
  }
}
```

**Resolution:**
```
1. Go to openrouter.ai/credits
2. Add credits to your account
3. Check key-specific limits: openrouter.ai/keys
```

**Check Balance:**
```bash
curl https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

## Model Errors (400)

### Model Not Found
```
Error: 400 Bad Request
{
  "error": {
    "message": "Model not found: invalid/model-name",
    "type": "invalid_request_error"
  }
}
```

**Fixes:**
```python
# Check exact model ID format
# Wrong
model = "gpt-4-turbo"

# Right
model = "openai/gpt-4-turbo"

# Get valid models
response = requests.get(
    "https://openrouter.ai/api/v1/models",
    headers={"Authorization": f"Bearer {api_key}"}
)
valid_models = [m["id"] for m in response.json()["data"]]
```

### Model Temporarily Unavailable
```
Error: 503 Service Unavailable
{
  "error": {
    "message": "Model temporarily unavailable",
    "type": "service_unavailable"
  }
}
```

**Handling:**
```python
FALLBACK_MODELS = [
    "anthropic/claude-3.5-sonnet",
    "openai/gpt-4-turbo",
    "meta-llama/llama-3.1-70b-instruct",
]

def chat_with_fallback(prompt, models=FALLBACK_MODELS):
    for model in models:
        try:
            return client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
        except Exception as e:
            if "unavailable" in str(e).lower():
                continue
            raise
    raise Exception("All models unavailable")
```

## Request Errors

### Invalid JSON
```
Error: 400 Bad Request
{
  "error": {
    "message": "Invalid JSON in request body"
  }
}
```

**Check:**
```python
import json

# Validate before sending
try:
    json.dumps(your_data)
except TypeError as e:
    print(f"JSON serialization error: {e}")
```

### Invalid Messages Format
```python
# Wrong - missing role
messages = [{"content": "Hello"}]

# Wrong - invalid role
messages = [{"role": "assistant", "content": "Hello"}]  # Can't start with assistant

# Right
messages = [{"role": "user", "content": "Hello"}]

# With system message
messages = [
    {"role": "system", "content": "You are helpful."},
    {"role": "user", "content": "Hello"}
]
```

### Context Length Exceeded
```
Error: 400 Bad Request
{
  "error": {
    "message": "This model's maximum context length is 128000 tokens"
  }
}
```

**Solutions:**
```python
# 1. Truncate input
def truncate_messages(messages, max_tokens=100000):
    # Estimate tokens (rough: 4 chars = 1 token)
    total_chars = sum(len(m["content"]) for m in messages)
    if total_chars > max_tokens * 4:
        # Truncate from oldest messages
        pass
    return messages

# 2. Use longer context model
model = "anthropic/claude-3.5-sonnet"  # 200K context
```

## Connection Errors

### Timeout
```python
from openai import APITimeoutError

try:
    response = client.chat.completions.create(
        model="openai/gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        timeout=60.0  # Increase timeout
    )
except APITimeoutError:
    print("Request timed out - try again or reduce prompt size")
```

### Connection Failed
```python
from openai import APIConnectionError

try:
    response = client.chat.completions.create(...)
except APIConnectionError:
    print("Check internet connection or OpenRouter status")
```

## Debugging Checklist

```
[ ] API key starts with sk-or-
[ ] Authorization header includes "Bearer "
[ ] Model ID includes provider prefix (openai/, anthropic/)
[ ] Account has sufficient credits
[ ] Key hasn't hit per-key limit
[ ] Request JSON is valid
[ ] Messages array is properly formatted
[ ] Context length within model limits
```

## Error Response Structure

```json
{
  "error": {
    "message": "Human-readable error description",
    "type": "error_type",
    "param": "specific_param_if_relevant",
    "code": "error_code"
  }
}
```

**Error Types:**
```
authentication_error  - API key issues (401)
rate_limit_error     - Too many requests (429)
payment_required     - Insufficient credits (402)
invalid_request_error - Bad request format (400)
service_unavailable  - Model down (503)
```

## Output

Successful execution produces:
- Working OpenRouter integration
- Verified API connectivity
- Example responses demonstrating functionality

## Error Handling

Common errors and solutions:
1. **401 Unauthorized**: Check API key format (must start with `sk-or-`)
2. **429 Rate Limited**: Implement exponential backoff
3. **500 Server Error**: Retry with backoff, check OpenRouter status page
4. **Model Not Found**: Verify model ID includes provider prefix

## Examples

See code examples in sections above for complete, runnable implementations.

## Resources

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter Models](https://openrouter.ai/models)
- [OpenRouter API Reference](https://openrouter.ai/docs/api-reference)
- [OpenRouter Status](https://status.openrouter.ai)

## Output

Successful execution produces:
- Working OpenRouter integration
- Verified API connectivity
- Example responses demonstrating functionality

## Error Handling

Common errors and solutions:
1. **401 Unauthorized**: Check API key format (must start with `sk-or-`)
2. **429 Rate Limited**: Implement exponential backoff
3. **500 Server Error**: Retry with backoff, check OpenRouter status page
4. **Model Not Found**: Verify model ID includes provider prefix

## Examples

See code examples in sections above for complete, runnable implementations.

## Resources

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter Models](https://openrouter.ai/models)
- [OpenRouter API Reference](https://openrouter.ai/docs/api-reference)
- [OpenRouter Status](https://status.openrouter.ai)
