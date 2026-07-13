# Rate Limiting Mistakes

## Rate Limiting Mistakes

### No Backoff Strategy

```python
# ❌ Wrong: Keep hammering on rate limit
while True:
    try:
        response = client.chat.completions.create(...)
        break
    except RateLimitError:
        continue  # Immediately retry

# ✓ Correct: Exponential backoff
for attempt in range(5):
    try:
        response = client.chat.completions.create(...)
        break
    except RateLimitError:
        wait = 2 ** attempt
        time.sleep(wait)
```

### Ignoring Rate Limit Headers

```python
# ✓ Better: Respect rate limit headers
def make_request_with_headers(prompt: str):
    response = client.chat.completions.create(...)

    # Check remaining requests
    # OpenRouter may include rate limit info in headers

    return response
```
