---
name: openrouter-upgrade-migration
description: |
  Migrate and upgrade OpenRouter SDK versions safely. Use when updating dependencies or migrating configurations. Trigger with phrases like 'openrouter upgrade', 'openrouter migration', 'update openrouter', 'openrouter breaking changes'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# OpenRouter Upgrade & Migration

## Overview

This skill guides you through SDK version upgrades, configuration migrations, and handling breaking changes safely.

## Prerequisites

- Existing OpenRouter integration
- Version control for rollback capability

## Instructions

Follow these steps to implement this skill:

1. **Verify Prerequisites**: Ensure all prerequisites listed above are met
2. **Review the Implementation**: Study the code examples and patterns below
3. **Adapt to Your Environment**: Modify configuration values for your setup
4. **Test the Integration**: Run the verification steps to confirm functionality
5. **Monitor in Production**: Set up appropriate logging and monitoring

## Overview

This skill guides you through SDK version upgrades, configuration migrations, and handling breaking changes safely.

## Prerequisites

- Existing OpenRouter integration
- Version control for rollback capability

## SDK Version Upgrades

### Python OpenAI SDK
```bash
# Check current version
pip show openai

# Upgrade to latest
pip install --upgrade openai

# Pin specific version
pip install openai==1.40.0
```

### TypeScript/Node.js
```bash
# Check current version
npm list openai

# Upgrade to latest
npm install openai@latest

# Pin specific version
npm install openai@4.56.0
```

## Migration from Direct API to SDK

### Before (Raw Requests)
```python
import requests

response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    },
    json={
        "model": "openai/gpt-4-turbo",
        "messages": [{"role": "user", "content": "Hello"}]
    }
)
result = response.json()
content = result["choices"][0]["message"]["content"]
```

### After (OpenAI SDK)
```python
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)

response = client.chat.completions.create(
    model="openai/gpt-4-turbo",
    messages=[{"role": "user", "content": "Hello"}]
)
content = response.choices[0].message.content
```

### Benefits of SDK
```
✓ Automatic retries
✓ Better error types
✓ Type hints / TypeScript types
✓ Streaming support built-in
✓ Consistent interface
```

## Model Migration

### Updating Model References
```python
# Old model name mapping
MODEL_MIGRATIONS = {
    "openai/gpt-4": "openai/gpt-4-turbo",
    "anthropic/claude-2": "anthropic/claude-3-haiku",
    "anthropic/claude-instant-1": "anthropic/claude-3-haiku",
}

def migrate_model_name(model: str) -> str:
    """Migrate deprecated model to current equivalent."""
    return MODEL_MIGRATIONS.get(model, model)

# Usage
old_model = "anthropic/claude-2"
new_model = migrate_model_name(old_model)
```

### Batch Model Update
```python
import re

def update_model_references(file_path: str):
    """Update model references in source file."""
    with open(file_path, 'r') as f:
        content = f.read()

    for old_model, new_model in MODEL_MIGRATIONS.items():
        # Match model in strings
        pattern = rf'["\']({re.escape(old_model)})["\']'
        content = re.sub(pattern, f'"{new_model}"', content)

    with open(file_path, 'w') as f:
        f.write(content)

# Apply to all Python files
import glob
for file in glob.glob("**/*.py", recursive=True):
    update_model_references(file)
```

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

## Code Pattern Updates

### Sync to Async Migration
```python
# Before: Synchronous
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)

def chat(prompt: str) -> str:
    response = client.chat.completions.create(
        model="openai/gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# After: Asynchronous
from openai import AsyncOpenAI

async_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)

async def chat_async(prompt: str) -> str:
    response = await async_client.chat.completions.create(
        model="openai/gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
```

### Adding Streaming Support
```python
# Before: Non-streaming
def chat(prompt: str) -> str:
    response = client.chat.completions.create(
        model="openai/gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# After: With streaming option
def chat(prompt: str, stream: bool = False):
    if stream:
        return stream_chat(prompt)
    else:
        response = client.chat.completions.create(
            model="openai/gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

def stream_chat(prompt: str):
    stream = client.chat.completions.create(
        model="openai/gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )
    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
```

## Error Handling Updates

### Modern Error Handling
```python
# Before: Generic exceptions
try:
    response = client.chat.completions.create(...)
except Exception as e:
    print(f"Error: {e}")

# After: Specific exception types
from openai import (
    APIError,
    RateLimitError,
    APIConnectionError,
    AuthenticationError
)

try:
    response = client.chat.completions.create(...)
except AuthenticationError:
    print("Invalid API key")
except RateLimitError:
    print("Rate limited, retrying...")
except APIConnectionError:
    print("Connection failed")
except APIError as e:
    print(f"API error: {e.status_code}")
```

## Testing During Migration

### Parallel Testing
```python
def test_migration(prompt: str, model: str):
    """Test both old and new implementations."""
    # Old implementation
    old_result = old_chat_function(prompt, model)

    # New implementation
    new_result = new_chat_function(prompt, model)

    # Compare
    assert old_result is not None
    assert new_result is not None
    print(f"Old: {old_result[:100]}...")
    print(f"New: {new_result[:100]}...")

    return {
        "old_success": True,
        "new_success": True,
        "responses_match": old_result[:50] == new_result[:50]
    }
```

### Gradual Rollout
```python
import random

def chat_with_rollout(prompt: str, new_implementation_percentage: int = 10):
    """Gradually roll out new implementation."""
    use_new = random.randint(1, 100) <= new_implementation_percentage

    if use_new:
        try:
            return new_chat_function(prompt)
        except Exception as e:
            # Fallback to old on error
            log_error(f"New implementation failed: {e}")
            return old_chat_function(prompt)
    else:
        return old_chat_function(prompt)
```

## Migration Checklist

```
Pre-Migration:
[ ] Document current implementation
[ ] List all model references
[ ] Identify configuration locations
[ ] Create backup of current code
[ ] Set up parallel testing

Migration Steps:
[ ] Update SDK/dependencies
[ ] Migrate model names
[ ] Update configuration format
[ ] Update error handling
[ ] Add new features (streaming, async)
[ ] Update tests

Post-Migration:
[ ] Run full test suite
[ ] Compare responses with old implementation
[ ] Monitor error rates
[ ] Check latency metrics
[ ] Verify cost tracking
[ ] Update documentation
```

## Rollback Plan

```python
# Keep old implementation available
def chat(prompt: str, use_legacy: bool = False):
    if use_legacy:
        return legacy_chat(prompt)
    return new_chat(prompt)

# Environment variable toggle
USE_LEGACY = os.environ.get("USE_LEGACY_OPENROUTER", "false").lower() == "true"

def chat(prompt: str):
    if USE_LEGACY:
        return legacy_chat(prompt)
    return new_chat(prompt)
```

### Quick Rollback
```bash
# Environment variable rollback
export USE_LEGACY_OPENROUTER=true

# Dependency rollback
pip install openai==1.35.0  # Previous version

# Git rollback
git revert HEAD  # If changes were committed
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
