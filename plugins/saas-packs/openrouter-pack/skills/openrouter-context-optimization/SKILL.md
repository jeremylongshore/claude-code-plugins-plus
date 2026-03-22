---
name: openrouter-context-optimization
description: |
  Optimize context window usage for OpenRouter models to reduce cost and improve quality. Use when hitting context limits, managing long conversations, or building RAG systems. Triggers: 'openrouter context', 'context window', 'openrouter token limit', 'reduce tokens openrouter'.
allowed-tools: Read, Write, Edit, Bash, Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, openrouter, optimization, context-window]

---
# OpenRouter Context Optimization

## Overview

OpenRouter models have varying context windows (4K to 1M+ tokens). Since pricing is per-token, stuffing unnecessary context wastes money and can degrade output quality. This skill covers context window lookup, token estimation, conversation trimming, chunking strategies, and Anthropic prompt caching for large contexts.

## Query Context Limits

```bash
# Check context window for specific models
curl -s https://openrouter.ai/api/v1/models | jq '[.data[] | select(
  .id == "anthropic/claude-3.5-sonnet" or
  .id == "openai/gpt-4o" or
  .id == "google/gemini-2.0-flash-001" or
  .id == "meta-llama/llama-3.1-70b-instruct"
) | {id, context_length, prompt_per_M: ((.pricing.prompt|tonumber)*1000000)}]'
```

## Context-Aware Model Selection

```python
import os, requests
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    default_headers={"HTTP-Referer": "https://my-app.com", "X-Title": "my-app"},
)

# Cache model metadata at startup
MODELS = {m["id"]: m for m in requests.get("https://openrouter.ai/api/v1/models").json()["data"]}

def estimate_tokens(text: str) -> int:
    """Rough estimate: 1 token ~ 4 characters for English text."""
    return len(text) // 4

def select_model_for_context(messages: list, preferred: str = "anthropic/claude-3.5-sonnet") -> str:
    """Pick a model that fits the context, falling back to larger windows."""
    estimated_tokens = sum(len(m.get("content", "")) for m in messages) // 4

    FALLBACK_CHAIN = [
        ("openai/gpt-4o-mini", 128_000),
        ("anthropic/claude-3.5-sonnet", 200_000),
        ("google/gemini-2.0-flash-001", 1_000_000),
    ]

    # Try preferred model first
    preferred_ctx = MODELS.get(preferred, {}).get("context_length", 0)
    if estimated_tokens < preferred_ctx * 0.8:  # 80% safety margin
        return preferred

    for model_id, ctx in FALLBACK_CHAIN:
        if estimated_tokens < ctx * 0.8:
            return model_id

    raise ValueError(f"Content too large ({estimated_tokens} est. tokens)")
```

## Conversation Trimming

```python
def trim_conversation(
    messages: list[dict],
    max_tokens: int = 100_000,
    keep_system: bool = True,
    keep_last_n: int = 4,
) -> list[dict]:
    """Trim conversation history to fit context window.

    Strategy: Keep system prompt + last N messages.
    If still too large, reduce to last 2 messages.
    """
    system = [m for m in messages if m["role"] == "system"] if keep_system else []
    non_system = [m for m in messages if m["role"] != "system"]

    kept = non_system[-keep_last_n:]
    trimmed = non_system[:-keep_last_n] if len(non_system) > keep_last_n else []

    total_est = sum(estimate_tokens(m.get("content", "")) for m in system + kept)
    if total_est > max_tokens and keep_last_n > 2:
        kept = non_system[-2:]

    result = system + kept
    if trimmed:
        summary_note = {
            "role": "system",
            "content": f"[Previous {len(trimmed)} messages trimmed for context limits]",
        }
        result = system + [summary_note] + kept

    return result
```

## Chunking for Large Documents

```python
def chunk_and_process(document: str, question: str, model: str = "openai/gpt-4o-mini",
                      chunk_size: int = 8000, overlap: int = 500) -> str:
    """Process a large document in overlapping chunks, then synthesize."""
    chunks = []
    start = 0
    while start < len(document):
        chunks.append(document[start:start + chunk_size])
        start += chunk_size - overlap

    results = []
    for i, chunk in enumerate(chunks):
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": f"Analyzing chunk {i+1}/{len(chunks)}."},
                {"role": "user", "content": f"Document:\n{chunk}\n\nQuestion: {question}"},
            ],
            max_tokens=1024, temperature=0,
        )
        results.append(response.choices[0].message.content)

    # Synthesize
    synthesis = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Synthesize these partial analyses."},
            {"role": "user", "content": f"Question: {question}\n\nResults:\n" + "\n---\n".join(results)},
        ],
        max_tokens=2048, temperature=0,
    )
    return synthesis.choices[0].message.content
```

## Prompt Caching for Repeated Context

```python
# Anthropic models support prompt caching -- mark large static blocks
# Subsequent requests with same cached block cost 90% less for input tokens
response = client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet",
    messages=[
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": large_reference_document,  # 50K+ tokens
                    "cache_control": {"type": "ephemeral"},
                }
            ],
        },
        {"role": "user", "content": "Summarize section 3."},
    ],
    max_tokens=1024,
)
# First request: cache_creation_input_tokens at 1.25x rate
# Subsequent: cache_read_input_tokens at 0.1x rate (90% savings)
```

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| 400 `context_length_exceeded` | Input + max_tokens > model limit | Trim messages or use larger-context model |
| 400 `max_tokens too large` | max_tokens alone exceeds limit | Reduce max_tokens |
| Slow responses | Very large context | Use streaming; consider chunking |
| Degraded quality | Too much irrelevant context | Trim to relevant content only |

## Enterprise Considerations

- Query `/api/v1/models` at startup to cache context limits -- don't hardcode (they change)
- Use `max_tokens` on every request to prevent runaway completion costs on large contexts
- Implement conversation trimming as middleware so all calls respect limits
- Use Anthropic prompt caching for RAG contexts that repeat across requests (90% input savings)
- Route large-context tasks to cost-effective models (Gemini Flash for 1M context at low cost)
- Monitor `prompt_tokens` in responses to detect context bloat before it hits limits

## References

- [Examples](${CLAUDE_SKILL_DIR}/references/examples.md) | [Errors](${CLAUDE_SKILL_DIR}/references/errors.md)
- [Prompt Caching](https://openrouter.ai/docs/features/prompt-caching) | [Models API](https://openrouter.ai/docs/api/api-reference/models/get-models)
