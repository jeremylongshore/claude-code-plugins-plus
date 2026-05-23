# Security Checklist

## Security Checklist

### Key Management

```python
# ✓ Correct: Environment variable
api_key = os.environ["OPENROUTER_API_KEY"]

# ✗ Wrong: Hardcoded
api_key = "sk-or-v1-xxxxx"

# ✓ Correct: Secrets manager
from google.cloud import secretmanager
client = secretmanager.SecretManagerServiceClient()
api_key = client.access_secret_version(name=secret_path).payload.data.decode()
```

### Request Validation

```python
def validate_request(prompt: str, model: str):
    """Validate before sending to API."""
    if not prompt or not prompt.strip():
        raise ValueError("Empty prompt")

    if len(prompt) > 100_000:  # ~25K tokens
        raise ValueError("Prompt too long")

    if "/" not in model:
        raise ValueError("Model must include provider prefix")

    # Sanitize if needed
    return prompt.strip()
```

### Response Handling

```python
def safe_extract_response(response) -> str:
    """Safely extract content from response."""
    if not response.choices:
        return ""

    content = response.choices[0].message.content
    if content is None:
        return ""

    # Optionally sanitize output
    return content
```
