# Authentication Errors (401)

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
