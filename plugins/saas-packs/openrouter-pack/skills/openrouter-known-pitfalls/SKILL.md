---
name: openrouter-known-pitfalls
description: |
  Avoid common OpenRouter integration mistakes and gotchas. Use proactively when starting a new integration or reviewing existing code. Triggers: 'openrouter pitfalls', 'openrouter gotchas', 'openrouter mistakes', 'openrouter best practices'.
allowed-tools: Read, Write, Edit, Bash, Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, openrouter, best-practices, pitfalls]

---
# OpenRouter Known Pitfalls

## Overview

A curated list of real-world mistakes developers make when integrating OpenRouter, each with the specific API behavior that causes the problem and the exact fix. These are not theoretical -- they come from production incidents and support requests.

## Pitfall 1: Missing Provider Prefix on Model ID

```python
# WRONG: Model ID without provider prefix
response = client.chat.completions.create(
    model="gpt-4o",  # ← Will fail with 400 "model not found"
    messages=[{"role": "user", "content": "Hello"}],
)

# RIGHT: Always include provider/model format
response = client.chat.completions.create(
    model="openai/gpt-4o",  # ← Correct
    messages=[{"role": "user", "content": "Hello"}],
)
```

## Pitfall 2: No max_tokens = Runaway Costs

```python
# WRONG: No max_tokens -- model may generate 4000+ tokens
response = client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet",  # $15/1M completion tokens
    messages=[{"role": "user", "content": "Write a story"}],
    # No max_tokens → could generate $0.06+ per request
)

# RIGHT: Always set max_tokens
response = client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet",
    messages=[{"role": "user", "content": "Write a story"}],
    max_tokens=500,  # ← Caps cost at ~$0.0075
)
```

## Pitfall 3: Hardcoded Model IDs Break When Models Are Renamed

```python
# WRONG: Hardcoded model ID scattered across codebase
# When "claude-3-opus" becomes "claude-3-opus-20240229", everything breaks

# RIGHT: Centralize model IDs in config
MODELS = {
    "primary": "anthropic/claude-3.5-sonnet",
    "budget": "openai/gpt-4o-mini",
    "free": "google/gemma-2-9b-it:free",
}

# Validate at startup
import requests
available = {m["id"] for m in requests.get("https://openrouter.ai/api/v1/models").json()["data"]}
for name, model_id in MODELS.items():
    if model_id not in available:
        print(f"WARNING: {name} model '{model_id}' not available!")
```

## Pitfall 4: Fallbacks Route to Unexpected Providers

```python
# WRONG: Default allow_fallbacks=True without controlling which providers
response = client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet",
    messages=[{"role": "user", "content": sensitive_data}],
    # OpenRouter might fall back to a different provider you didn't approve
)

# RIGHT: Control fallback behavior explicitly
response = client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet",
    messages=[{"role": "user", "content": sensitive_data}],
    extra_body={
        "provider": {
            "order": ["Anthropic"],      # Only approved provider
            "allow_fallbacks": False,     # No surprise routing
        },
    },
)
```

## Pitfall 5: Ignoring the Free Model Daily Limit

```python
# WRONG: Using free models in production
# Free models have limits: 50 req/day (no credits), 1000 req/day (with credits)
response = client.chat.completions.create(
    model="google/gemma-2-9b-it:free",  # Will 429 after daily limit
    messages=[{"role": "user", "content": "Hello"}],
)

# RIGHT: Use free models only for dev/testing
# Use paid models with credit limits for production
```

## Pitfall 6: Not Checking Which Model Actually Served the Request

```python
# WRONG: Assuming the model you requested is the model that responded
response = client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet",
    messages=[{"role": "user", "content": "Hello"}],
)
print(response.choices[0].message.content)  # Might be from a fallback model!

# RIGHT: Always check response.model
response = client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet",
    messages=[{"role": "user", "content": "Hello"}],
)
print(f"Served by: {response.model}")  # Log this for debugging
if response.model != "anthropic/claude-3.5-sonnet":
    log.warning(f"Fallback triggered: requested claude-3.5-sonnet, got {response.model}")
```

## Pitfall 7: Creating New Client Instance Per Request

```python
# WRONG: New client per request (new TCP/TLS handshake each time)
for prompt in prompts:
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=key)
    client.chat.completions.create(...)  # Slow!

# RIGHT: Reuse single client (connection pooling)
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    default_headers={"HTTP-Referer": "https://my-app.com", "X-Title": "my-app"},
)
for prompt in prompts:
    client.chat.completions.create(...)  # Reuses HTTP connection
```

## Pitfall 8: Storing API Keys in Source Code

```python
# WRONG: Key in source code
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="sk-or-v1-abc123...",  # ← Will be committed to git
)

# RIGHT: Environment variable + secrets manager
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],  # From .env (gitignored) or secrets manager
)
```

## Pitfall 9: Not Setting Timeouts

```python
# WRONG: No timeout -- request hangs forever if model is slow
client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=key)

# RIGHT: Set explicit timeout
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    timeout=30.0,      # 30s per request
    max_retries=3,     # Retry on 429/5xx
)
```

## Pitfall 10: Caching Non-Deterministic Responses

```python
# WRONG: Caching responses with temperature > 0
# Each call produces different output, so cache is meaningless
cache[key] = client.chat.completions.create(
    model="openai/gpt-4o-mini",
    messages=msgs,
    temperature=0.7,  # ← Non-deterministic!
)

# RIGHT: Only cache with temperature=0
if temperature == 0:
    cache[key] = response
```

## Quick Checklist

```python
PITFALL_CHECKLIST = [
    "Model IDs use provider/model format (e.g., openai/gpt-4o)",
    "max_tokens set on every request",
    "API keys in env vars or secrets manager, never in code",
    "Single client instance reused (not created per request)",
    "Timeout and max_retries configured",
    "response.model checked (may differ from requested model)",
    "Free models NOT used in production",
    "Fallback behavior explicitly controlled for sensitive data",
    "Model IDs centralized in config (not scattered in code)",
    "Only deterministic responses (temp=0) are cached",
]
```

## Error Handling

| Pitfall | Symptom | Quick Fix |
|---------|---------|-----------|
| Missing provider prefix | 400 `model not found` | Add `openai/`, `anthropic/`, etc. |
| No max_tokens | Unexpected high costs | Add `max_tokens` to every call |
| Hardcoded API key | Key exposed in git history | Rotate key; use env vars |
| No timeout | Hanging requests | Set `timeout=30.0` |
| Free model in prod | 429 after 50-1000 requests | Use paid models |

## Enterprise Considerations

- Run the pitfall checklist during code review for any OpenRouter integration PR
- Add pre-commit hooks that scan for hardcoded `sk-or-v1-` patterns
- Centralize model IDs in a config file and validate against `/api/v1/models` at startup
- Log `response.model` on every request to catch unexpected fallbacks
- Set `max_tokens` as a team-wide policy enforced in your client wrapper

## References

- [Examples](${CLAUDE_SKILL_DIR}/references/examples.md) | [Errors](${CLAUDE_SKILL_DIR}/references/errors.md)
- [Quickstart](https://openrouter.ai/docs/quickstart) | [API Reference](https://openrouter.ai/docs/api/reference/overview)
