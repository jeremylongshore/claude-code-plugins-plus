# Request Errors

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
