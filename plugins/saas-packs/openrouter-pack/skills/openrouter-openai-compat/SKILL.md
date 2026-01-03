---
name: openrouter-openai-compat
description: |
  Configure OpenRouter as an OpenAI API drop-in replacement. Use when migrating from OpenAI or using OpenAI-compatible libraries. Trigger with phrases like 'openrouter openai', 'openrouter drop-in', 'openrouter compatibility', 'migrate to openrouter'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# OpenRouter OpenAI Compatibility

## Overview

This skill demonstrates how to use OpenRouter with any OpenAI-compatible library or codebase with minimal changes.

## Prerequisites

- Existing OpenAI integration or familiarity with OpenAI API
- OpenRouter API key

## Instructions

Follow these steps to implement this skill:

1. **Verify Prerequisites**: Ensure all prerequisites listed above are met
2. **Review the Implementation**: Study the code examples and patterns below
3. **Adapt to Your Environment**: Modify configuration values for your setup
4. **Test the Integration**: Run the verification steps to confirm functionality
5. **Monitor in Production**: Set up appropriate logging and monitoring

## Overview

This skill demonstrates how to use OpenRouter with any OpenAI-compatible library or codebase with minimal changes.

## Prerequisites

- Existing OpenAI integration or familiarity with OpenAI API
- OpenRouter API key

## Drop-in Replacement

### The Key Insight
```
OpenRouter is OpenAI API compatible.
Change base URL and API key, keep everything else.
```

### Python Migration
```python
# Before (OpenAI direct)
from openai import OpenAI

client = OpenAI(
    api_key="sk-..."  # OpenAI key
)

# After (OpenRouter)
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="sk-or-..."  # OpenRouter key
)

# Code stays exactly the same!
response = client.chat.completions.create(
    model="openai/gpt-4-turbo",  # Add provider prefix
    messages=[{"role": "user", "content": "Hello"}]
)
```

### TypeScript Migration
```typescript
// Before (OpenAI direct)
import OpenAI from 'openai';

const client = new OpenAI({
  apiKey: 'sk-...',
});

// After (OpenRouter)
import OpenAI from 'openai';

const client = new OpenAI({
  baseURL: 'https://openrouter.ai/api/v1',
  apiKey: 'sk-or-...',
});

// Same code works!
const response = await client.chat.completions.create({
  model: 'openai/gpt-4-turbo',  // Add provider prefix
  messages: [{ role: 'user', content: 'Hello' }],
});
```

## Environment Variable Approach

### Single Environment Variable
```bash
# .env for OpenAI
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1

# .env for OpenRouter
OPENAI_API_KEY=sk-or-...
OPENAI_BASE_URL=https://openrouter.ai/api/v1
```

### Code Without Changes
```python
# This code works with either provider
from openai import OpenAI

client = OpenAI()  # Reads from environment

response = client.chat.completions.create(
    model="gpt-4-turbo",  # Works if OPENAI
    # model="openai/gpt-4-turbo",  # For OpenRouter
    messages=[{"role": "user", "content": "Hello"}]
)
```

## Model Name Mapping

### OpenAI → OpenRouter
```
OpenAI Model          → OpenRouter Model
-------------------------------------------------
gpt-4-turbo           → openai/gpt-4-turbo
gpt-4                 → openai/gpt-4
gpt-4-32k             → openai/gpt-4-32k
gpt-3.5-turbo         → openai/gpt-3.5-turbo
gpt-3.5-turbo-16k     → openai/gpt-3.5-turbo-16k
```

### Automatic Mapping Helper
```python
def openai_to_openrouter_model(model: str) -> str:
    """Convert OpenAI model name to OpenRouter format."""
    if "/" in model:
        return model  # Already in OpenRouter format
    if model.startswith("gpt-"):
        return f"openai/{model}"
    return model

# Usage
model = openai_to_openrouter_model("gpt-4-turbo")
# Returns: "openai/gpt-4-turbo"
```

## Feature Compatibility

### Fully Supported
```
✓ chat.completions.create
✓ Streaming responses
✓ Function/tool calling
✓ JSON mode
✓ System messages
✓ Multi-turn conversations
✓ Temperature, top_p, max_tokens
✓ Stop sequences
✓ Presence/frequency penalty
```

### OpenRouter Extras
```
Additional features via OpenRouter:
- Access to 100+ models (not just OpenAI)
- Automatic fallbacks
- Cost tracking per request
- Model comparison
- Provider routing
```

### Not Applicable
```
✗ Assistants API (OpenAI specific)
✗ File uploads to OpenAI
✗ Fine-tuning API
✗ Embeddings (use directly or separate service)
✗ Images (DALL-E - use directly)
✗ Audio (Whisper - use directly)
```

## Switching Between Providers

### Runtime Switching
```python
import os

class LLMClient:
    def __init__(self, provider: str = "openrouter"):
        if provider == "openai":
            self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
            self.model_prefix = ""
        else:
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.environ["OPENROUTER_API_KEY"]
            )
            self.model_prefix = "openai/"

    def chat(self, prompt: str, model: str = "gpt-4-turbo"):
        full_model = f"{self.model_prefix}{model}" if self.model_prefix else model
        return self.client.chat.completions.create(
            model=full_model,
            messages=[{"role": "user", "content": prompt}]
        )

# Usage
client = LLMClient(provider=os.environ.get("LLM_PROVIDER", "openrouter"))
```

### Configuration-Based
```python
# config.py
import os

LLM_CONFIG = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "api_key": os.environ.get("OPENAI_API_KEY"),
        "model_prefix": "",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": os.environ.get("OPENROUTER_API_KEY"),
        "model_prefix": "openai/",
    },
}

ACTIVE_PROVIDER = os.environ.get("LLM_PROVIDER", "openrouter")
```

## LangChain Integration

### With OpenRouter
```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="openai/gpt-4-turbo",
    openai_api_key=os.environ["OPENROUTER_API_KEY"],
    openai_api_base="https://openrouter.ai/api/v1",
)

response = llm.invoke("Hello!")
```

### LlamaIndex Integration
```python
from llama_index.llms.openai import OpenAI

llm = OpenAI(
    model="openai/gpt-4-turbo",
    api_key=os.environ["OPENROUTER_API_KEY"],
    api_base="https://openrouter.ai/api/v1",
)
```

## Testing Compatibility

### Verify Setup
```python
def test_openrouter_compat():
    """Test that OpenRouter works as OpenAI drop-in."""
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"]
    )

    # Test basic completion
    response = client.chat.completions.create(
        model="openai/gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say 'test'"}],
        max_tokens=10
    )

    assert response.choices[0].message.content
    assert response.usage.total_tokens > 0
    print("✓ OpenRouter compatibility verified")

test_openrouter_compat()
```

## Migration Checklist

```
[ ] Update base URL to OpenRouter
[ ] Replace API key with OpenRouter key
[ ] Add model provider prefix (openai/)
[ ] Test basic completion
[ ] Test streaming
[ ] Test function calling (if used)
[ ] Verify error handling works
[ ] Update monitoring/logging
[ ] Update cost tracking
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
