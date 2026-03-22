---
name: anth-performance-tuning
description: |
  Optimize Claude API performance with prompt caching, model selection,
  streaming, and latency reduction techniques.
  Use when experiencing slow responses, optimizing token usage,
  or reducing time-to-first-token in production.
  Trigger with phrases like "anthropic performance", "claude speed",
  "optimize claude latency", "anthropic caching", "faster claude responses".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, anthropic]
compatible-with: claude-code
---

# Anthropic Performance Tuning

## Overview

Optimize Claude API latency and throughput via prompt caching, model selection, streaming, and request optimization. The biggest wins come from prompt caching (90% input cost reduction) and model selection (Haiku is 4x faster than Sonnet).

## Prompt Caching (Biggest Win)

```python
import anthropic

client = anthropic.Anthropic()

# Mark long, reusable content with cache_control
# Cached content: 90% cheaper on subsequent requests, near-zero latency for cached portion
message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": "You are an expert on the following 50-page document: ...<long document>...",
            "cache_control": {"type": "ephemeral"}  # Cache this block
        }
    ],
    messages=[{"role": "user", "content": "What does section 3.2 say?"}]
)

# Check cache performance
print(f"Cache read tokens: {message.usage.cache_read_input_tokens}")   # Free/cheap
print(f"Cache creation tokens: {message.usage.cache_creation_input_tokens}")  # First call only
print(f"Uncached input tokens: {message.usage.input_tokens}")
```

**Cache requirements:** Minimum 1,024 tokens for Sonnet/Opus, 2,048 for Haiku. Cache lives for 5 minutes (refreshed on each hit).

## Model Selection for Speed

| Model | Speed | Cost (per MTok in/out) | Best For |
|-------|-------|----------------------|----------|
| Claude Haiku | Fastest | $0.80 / $4.00 | Classification, extraction, routing |
| Claude Sonnet | Balanced | $3.00 / $15.00 | General tasks, tool use, code |
| Claude Opus | Deepest | $15.00 / $75.00 | Complex reasoning, research |

```python
# Route by task complexity
def select_model(task_type: str) -> str:
    routing = {
        "classify": "claude-haiku-4-20250514",
        "extract": "claude-haiku-4-20250514",
        "summarize": "claude-sonnet-4-20250514",
        "code": "claude-sonnet-4-20250514",
        "research": "claude-opus-4-20250514",
    }
    return routing.get(task_type, "claude-sonnet-4-20250514")
```

## Streaming for Perceived Speed

```python
# Streaming reduces time-to-first-token from seconds to ~200ms
with client.messages.stream(
    model="claude-sonnet-4-20250514",
    max_tokens=2048,
    messages=[{"role": "user", "content": prompt}]
) as stream:
    for text in stream.text_stream:
        yield text  # User sees response immediately
```

## Reduce Token Count

```python
# 1. Set max_tokens to what you actually need (not max)
msg = client.messages.create(
    model="claude-haiku-4-20250514",
    max_tokens=128,  # Not 4096 — smaller = faster generation
    messages=[{"role": "user", "content": "Classify as positive/negative: 'Great product!'"}]
)

# 2. Use prefill to skip preamble
msg = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=64,
    messages=[
        {"role": "user", "content": "Classify sentiment: 'Great product!'"},
        {"role": "assistant", "content": "Sentiment:"}  # Skip "Sure, I'd be happy to..."
    ]
)

# 3. Pre-check token count for large inputs
count = client.messages.count_tokens(
    model="claude-sonnet-4-20250514",
    messages=[{"role": "user", "content": large_document}]
)
if count.input_tokens > 100_000:
    # Chunk or summarize first
    pass
```

## Parallel Requests

```typescript
import Anthropic from '@anthropic-ai/sdk';
import PQueue from 'p-queue';

const client = new Anthropic();
const queue = new PQueue({ concurrency: 10 });

// Process multiple prompts in parallel (within rate limits)
const results = await Promise.all(
  prompts.map(p => queue.add(() =>
    client.messages.create({
      model: 'claude-haiku-4-20250514',
      max_tokens: 256,
      messages: [{ role: 'user', content: p }],
    })
  ))
);
```

## Performance Benchmarks

| Optimization | Latency Impact | Cost Impact |
|-------------|----------------|-------------|
| Prompt caching | -50% (cached portion) | -90% input cost |
| Haiku over Sonnet | -75% TTFT | -73% cost |
| Streaming | -80% TTFT (perceived) | Same cost |
| Lower max_tokens | -10-30% total time | Same cost |
| Prefill technique | -20% output tokens | Proportional savings |

## Resources

- [Prompt Caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)
- [Token Counting](https://docs.anthropic.com/en/docs/build-with-claude/token-counting)
- [Pricing](https://docs.anthropic.com/en/docs/about-claude/pricing)

## Next Steps

For cost optimization, see `anth-cost-tuning`.
