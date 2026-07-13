# Security Best Practices

## Security Best Practices

### Secure Configuration

```python
# Environment-based configuration
class SecureConfig:
    def __init__(self):
        self.api_key = os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not set")

        # Never log the full key
        self.masked_key = f"{self.api_key[:10]}...{self.api_key[-4:]}"

    def get_client(self):
        return OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key
        )

# Never print or log full API key
config = SecureConfig()
print(f"Using key: {config.masked_key}")
```

### Request Validation

```python
def validate_request(prompt: str, max_length: int = 100000) -> bool:
    """Validate request before sending."""
    # Length check
    if len(prompt) > max_length:
        raise ValueError(f"Prompt exceeds {max_length} characters")

    # Check for potential injection
    dangerous_patterns = [
        r'ignore previous instructions',
        r'system:',
        r'<\|.*\|>',
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, prompt, re.IGNORECASE):
            raise ValueError("Potentially dangerous content detected")

    return True
```
