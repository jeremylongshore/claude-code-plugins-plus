---
name: openrouter-model-catalog
description: |
  Explore and query the OpenRouter model catalog programmatically. Use when selecting models or checking availability. Trigger with phrases like 'openrouter models', 'list openrouter models', 'openrouter model catalog', 'available models openrouter'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# OpenRouter Model Catalog

## Overview

This skill teaches you how to query the OpenRouter models API, filter by capabilities, and select the right model for your use case.

## Prerequisites

- OpenRouter API key configured
- Basic understanding of LLM model differences

## Instructions

Follow these steps to implement this skill:

1. **Verify Prerequisites**: Ensure all prerequisites listed above are met
2. **Review the Implementation**: Study the code examples and patterns below
3. **Adapt to Your Environment**: Modify configuration values for your setup
4. **Test the Integration**: Run the verification steps to confirm functionality
5. **Monitor in Production**: Set up appropriate logging and monitoring

## Overview

This skill teaches you how to query the OpenRouter models API, filter by capabilities, and select the right model for your use case.

## Prerequisites

- OpenRouter API key configured
- Basic understanding of LLM model differences

## Listing All Models

### API Request
```bash
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

### Python
```python
import requests

response = requests.get(
    "https://openrouter.ai/api/v1/models",
    headers={"Authorization": f"Bearer {api_key}"}
)

models = response.json()["data"]
for model in models:
    print(f"{model['id']}: ${model['pricing']['prompt']}/1K tokens")
```

## Model Categories

### OpenAI Models
```
openai/gpt-4o              - Latest multimodal
openai/gpt-4-turbo         - Fast GPT-4
openai/gpt-4               - Original GPT-4
openai/gpt-4-32k           - Extended context
openai/gpt-3.5-turbo       - Fast and cheap
openai/gpt-3.5-turbo-16k   - Extended context
```

### Anthropic Models
```
anthropic/claude-3.5-sonnet  - Best balance
anthropic/claude-3-opus      - Highest capability
anthropic/claude-3-sonnet    - Good balance
anthropic/claude-3-haiku     - Fastest Claude
anthropic/claude-2.1         - Legacy
```

### Meta Llama Models
```
meta-llama/llama-3.1-405b-instruct  - Largest
meta-llama/llama-3.1-70b-instruct   - Great balance
meta-llama/llama-3.1-8b-instruct    - Fast/cheap
meta-llama/llama-3-70b-instruct     - Previous gen
```

### Mistral Models
```
mistralai/mistral-large       - Most capable
mistralai/mistral-medium      - Balanced
mistralai/mixtral-8x7b-instruct - MoE model
mistralai/mistral-7b-instruct - Smallest
```

### Google Models
```
google/gemini-pro-1.5      - Latest Gemini
google/gemini-pro          - Standard
google/palm-2-chat-bison   - PaLM 2
```

### Specialized Models
```
# Code-focused
deepseek/deepseek-coder
codellama/codellama-34b-instruct

# Long context
anthropic/claude-3-opus (200K)
openai/gpt-4-turbo (128K)

# Cost-effective
meta-llama/llama-3.1-8b-instruct
mistralai/mistral-7b-instruct
```

## Model Selection Criteria

### By Task Type
```
Code generation:
  1. anthropic/claude-3.5-sonnet
  2. openai/gpt-4-turbo
  3. deepseek/deepseek-coder

Creative writing:
  1. anthropic/claude-3-opus
  2. openai/gpt-4
  3. meta-llama/llama-3.1-70b-instruct

Analysis/Reasoning:
  1. anthropic/claude-3-opus
  2. openai/gpt-4-turbo
  3. anthropic/claude-3.5-sonnet

Quick tasks:
  1. anthropic/claude-3-haiku
  2. openai/gpt-3.5-turbo
  3. mistralai/mistral-7b-instruct
```

### By Context Length
```
< 4K tokens:   Any model
4K - 16K:      gpt-3.5-turbo-16k, most models
16K - 32K:     gpt-4-32k, claude-3 models
32K - 128K:    gpt-4-turbo, gemini-pro-1.5
128K - 200K:   claude-3-opus, claude-3.5-sonnet
```

### By Cost (per 1M tokens)
```
Budget (< $1):
  - meta-llama/llama-3.1-8b-instruct
  - mistralai/mistral-7b-instruct

Mid-range ($1-5):
  - anthropic/claude-3-haiku
  - openai/gpt-3.5-turbo
  - meta-llama/llama-3.1-70b-instruct

Premium ($5-30):
  - anthropic/claude-3.5-sonnet
  - openai/gpt-4-turbo
  - anthropic/claude-3-sonnet

Enterprise ($30+):
  - anthropic/claude-3-opus
  - openai/gpt-4
  - meta-llama/llama-3.1-405b-instruct
```

## Model Information API

### Get Model Details
```python
def get_model_info(model_id):
    response = requests.get(
        "https://openrouter.ai/api/v1/models",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    models = response.json()["data"]
    return next((m for m in models if m["id"] == model_id), None)

model = get_model_info("anthropic/claude-3.5-sonnet")
print(f"Context: {model['context_length']}")
print(f"Prompt cost: ${model['pricing']['prompt']}/token")
print(f"Completion cost: ${model['pricing']['completion']}/token")
```

### Model Schema
```json
{
  "id": "anthropic/claude-3.5-sonnet",
  "name": "Claude 3.5 Sonnet",
  "description": "...",
  "context_length": 200000,
  "pricing": {
    "prompt": "0.000003",
    "completion": "0.000015"
  },
  "top_provider": {
    "context_length": 200000,
    "max_completion_tokens": 8192
  },
  "per_request_limits": null
}
```

## Dynamic Model Selection

### Based on Input Length
```python
def select_model(input_tokens):
    if input_tokens < 4000:
        return "openai/gpt-3.5-turbo"
    elif input_tokens < 16000:
        return "openai/gpt-3.5-turbo-16k"
    elif input_tokens < 128000:
        return "openai/gpt-4-turbo"
    else:
        return "anthropic/claude-3.5-sonnet"
```

### Based on Task
```python
def select_model_for_task(task_type):
    models = {
        "code": "anthropic/claude-3.5-sonnet",
        "creative": "anthropic/claude-3-opus",
        "quick": "anthropic/claude-3-haiku",
        "analysis": "openai/gpt-4-turbo",
        "translation": "openai/gpt-4-turbo",
    }
    return models.get(task_type, "openai/gpt-4-turbo")
```

## Model Comparison Tool

### Compare Models Side-by-Side
```python
async def compare_models(prompt, models):
    results = {}
    for model in models:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        results[model] = {
            "response": response.choices[0].message.content,
            "tokens": response.usage.total_tokens,
        }
    return results

# Usage
models = [
    "openai/gpt-4-turbo",
    "anthropic/claude-3.5-sonnet",
    "meta-llama/llama-3.1-70b-instruct"
]
results = await compare_models("Explain recursion", models)
```

## Staying Updated

### Model Changes
```
OpenRouter frequently adds new models:
- Check openrouter.ai/models for latest
- Subscribe to changelog
- API response includes all current models
```

### Deprecation Handling
```python
# Models may be deprecated
# Use fallbacks to handle gracefully
try:
    response = client.chat.completions.create(
        model="deprecated/model",
        messages=[...]
    )
except Exception as e:
    response = client.chat.completions.create(
        model="fallback/model",
        messages=[...]
    )
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
