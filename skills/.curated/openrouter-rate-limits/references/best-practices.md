# Best Practices

## Best Practices

### Pre-Request Check

```python
def safe_chat(prompt: str, model: str):
    """Chat with proactive rate limit checking."""
    # Check current usage
    if tracker.should_throttle(model, limit=60):
        time.sleep(2)  # Proactive slowdown

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        tracker.record_request(model)
        return response
    except RateLimitError:
        # Aggressive backoff on actual rate limit
        time.sleep(10)
        raise
```

### Circuit Breaker

```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, reset_timeout: float = 60):
        self.failures = 0
        self.threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.last_failure = 0
        self.state = "closed"  # closed, open, half-open

    def record_failure(self):
        self.failures += 1
        self.last_failure = time.time()
        if self.failures >= self.threshold:
            self.state = "open"

    def record_success(self):
        self.failures = 0
        self.state = "closed"

    def can_proceed(self) -> bool:
        if self.state == "closed":
            return True
        if self.state == "open":
            if time.time() - self.last_failure > self.reset_timeout:
                self.state = "half-open"
                return True
            return False
        return True  # half-open allows one request
```
