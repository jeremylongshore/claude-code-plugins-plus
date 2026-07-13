# Configuration Migration

## Configuration Migration

### Environment Variables

```bash
# Old format (single key)
OPENROUTER_API_KEY=sk-or-v1-xxx

# New format (with additional config)
OPENROUTER_API_KEY=sk-or-v1-xxx
OPENROUTER_DEFAULT_MODEL=anthropic/claude-3.5-sonnet
OPENROUTER_TIMEOUT=60
OPENROUTER_MAX_RETRIES=3
```

### Config File Migration

```python
# Old config format
OLD_CONFIG = {
    "api_key": "sk-or-v1-xxx",
    "model": "gpt-4"
}

# New config format
NEW_CONFIG = {
    "api_key": "sk-or-v1-xxx",
    "base_url": "https://openrouter.ai/api/v1",
    "default_model": "openai/gpt-4-turbo",
    "fallback_models": [
        "anthropic/claude-3.5-sonnet",
        "meta-llama/llama-3.1-70b-instruct"
    ],
    "timeout": 60.0,
    "max_retries": 3,
    "headers": {
        "HTTP-Referer": "https://your-app.com",
        "X-Title": "Your App"
    }
}

def migrate_config(old_config: dict) -> dict:
    """Migrate old config to new format."""
    return {
        "api_key": old_config.get("api_key"),
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": migrate_model_name(old_config.get("model", "openai/gpt-4-turbo")),
        "fallback_models": ["anthropic/claude-3.5-sonnet"],
        "timeout": old_config.get("timeout", 60.0),
        "max_retries": old_config.get("retries", 3),
        "headers": {}
    }
```
