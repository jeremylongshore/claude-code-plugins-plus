---
name: together-cost-tuning
description: |
  Together AI cost tuning for inference, fine-tuning, and model deployment.
  Use when working with Together AI's OpenAI-compatible API.
  Trigger: "together cost tuning".
allowed-tools: Read, Write, Edit, Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, inference, together]
compatible-with: claude-code
---

# Together AI Cost Tuning

## Overview

Optimize Together AI costs with model selection, batching, and caching.

## Instructions

### Together AI Pricing Model

| Model Category | Price (per 1M tokens) | Example Models |
|---------------|----------------------|----------------|
| Small (< 10B) | $0.10-0.30 | Llama-3.2-3B, Qwen-2.5-7B |
| Medium (10-40B) | $0.60-1.20 | Mixtral-8x7B, Llama-3.3-70B-Turbo |
| Large (40B+) | $2.00-5.00 | Llama-3.1-405B, DeepSeek-V3 |
| Image gen | $0.003-0.05/image | FLUX.1-schnell, SDXL |
| Embeddings | $0.008/1M tokens | M2-BERT |
| Fine-tuning | ~$5-25/hour | Depends on model + GPU |
| Batch inference | 50% off | Same models, async |

### Cost Reduction Strategies

```python
# 1. Use Turbo variants (faster, cheaper, similar quality)
# meta-llama/Llama-3.3-70B-Instruct-Turbo vs Llama-3.1-70B-Instruct

# 2. Batch inference (50% cost reduction)
batch_response = client.batch.create(
    input_file_id=file_id,
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
    completion_window="24h",
)

# 3. Cache responses for identical prompts
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_completion(prompt: str, model: str) -> str:
    response = client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content

# 4. Use smallest model that works
# Test with 3B first, upgrade to 70B only if quality insufficient
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| High costs | Wrong model tier | Downsize model |
| Batch failures | Invalid input format | Validate JSONL |
| Fine-tuning expensive | Too many epochs | Start with 1-2 epochs |

## Resources

- [Together AI Pricing](https://www.together.ai/pricing)
- [Batch Inference](https://docs.together.ai/docs/batch-inference)

## Next Steps

For architecture patterns, see `together-reference-architecture`.
