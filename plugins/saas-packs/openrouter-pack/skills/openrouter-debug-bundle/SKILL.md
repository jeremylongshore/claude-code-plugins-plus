---
name: openrouter-debug-bundle
description: |
  Create debug bundles for troubleshooting OpenRouter API issues. Use when diagnosing failures, unexpected responses, or latency problems. Triggers: 'openrouter debug', 'openrouter troubleshoot', 'debug openrouter request', 'openrouter issue'.
allowed-tools: Read, Write, Edit, Bash, Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, openrouter, debugging, troubleshooting]

---
# OpenRouter Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`python3 --version 2>/dev/null || echo 'N/A'`

## Overview

When an OpenRouter request fails or returns unexpected results, you need a structured debug bundle: the exact request, response, headers, generation metadata, and environment info. The generation ID (`gen-*` prefix in `response.id`) is the key correlator -- it lets you look up exact cost, provider used, and latency via `GET /api/v1/generation?id=`.

## Quick Debug: curl

```bash
# Send a request and capture full response with headers
curl -v https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -H "HTTP-Referer: https://my-app.com" \
  -H "X-Title: debug-test" \
  -d '{
    "model": "openai/gpt-4o-mini",
    "messages": [{"role": "user", "content": "Say hello"}],
    "max_tokens": 50
  }' 2>&1 | tee /tmp/openrouter-debug.txt

# Extract generation ID from response
GEN_ID=$(jq -r '.id' /tmp/openrouter-debug.txt 2>/dev/null)
echo "Generation ID: $GEN_ID"

# Look up generation metadata (exact cost, provider, latency)
curl -s "https://openrouter.ai/api/v1/generation?id=$GEN_ID" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" | jq '.data | {
    model: .model,
    total_cost: .total_cost,
    tokens_prompt: .tokens_prompt,
    tokens_completion: .tokens_completion,
    generation_time: .generation_time,
    provider: .provider_name
  }'
```

## Python Debug Bundle Generator

```python
import os, json, time, platform, sys
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import Optional
from openai import OpenAI, APIError
import requests as http_requests

@dataclass
class DebugBundle:
    timestamp: str
    generation_id: Optional[str]
    request_model: str
    request_messages: list
    request_params: dict
    response_status: str
    response_model: Optional[str]
    response_content: Optional[str]
    error_type: Optional[str]
    error_message: Optional[str]
    error_code: Optional[int]
    latency_ms: float
    generation_metadata: Optional[dict]
    environment: dict

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)

    def save(self, path: str = "debug_bundle.json"):
        with open(path, "w") as f:
            f.write(self.to_json())

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    default_headers={"HTTP-Referer": "https://my-app.com", "X-Title": "my-app"},
)

def debug_request(
    messages: list[dict],
    model: str = "openai/gpt-4o-mini",
    **kwargs,
) -> DebugBundle:
    """Execute a request and capture everything for debugging."""
    env = {
        "python": sys.version,
        "platform": platform.platform(),
        "openai_sdk": getattr(__import__("openai"), "__version__", "unknown"),
    }

    start = time.monotonic()
    gen_id = None
    response_model = None
    content = None
    error_type = None
    error_msg = None
    error_code = None
    status = "success"
    gen_meta = None

    try:
        response = client.chat.completions.create(
            model=model, messages=messages, **kwargs
        )
        gen_id = response.id
        response_model = response.model
        content = response.choices[0].message.content
    except APIError as e:
        status = "error"
        error_type = type(e).__name__
        error_msg = str(e)
        error_code = e.status_code
    except Exception as e:
        status = "error"
        error_type = type(e).__name__
        error_msg = str(e)

    latency = (time.monotonic() - start) * 1000

    # Fetch generation metadata if we have an ID
    if gen_id:
        try:
            gen = http_requests.get(
                f"https://openrouter.ai/api/v1/generation?id={gen_id}",
                headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"},
                timeout=5,
            ).json()
            gen_meta = gen.get("data")
        except Exception:
            pass

    return DebugBundle(
        timestamp=datetime.now(timezone.utc).isoformat(),
        generation_id=gen_id,
        request_model=model,
        request_messages=messages,
        request_params={k: v for k, v in kwargs.items() if k != "messages"},
        response_status=status,
        response_model=response_model,
        response_content=content,
        error_type=error_type,
        error_message=error_msg,
        error_code=error_code,
        latency_ms=round(latency, 1),
        generation_metadata=gen_meta,
        environment=env,
    )

# Usage
bundle = debug_request(
    [{"role": "user", "content": "Test"}],
    model="anthropic/claude-3.5-sonnet",
    max_tokens=100,
)
print(bundle.to_json())
bundle.save("debug_bundle.json")
```

## Common Debug Checks

```bash
# 1. Verify API key is valid
curl -s https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" | jq '.data | {label, usage, limit, is_free_tier}'

# 2. Check if model exists
MODEL="anthropic/claude-3.5-sonnet"
curl -s https://openrouter.ai/api/v1/models | jq --arg m "$MODEL" '.data[] | select(.id == $m) | {id, context_length}'

# 3. Check OpenRouter status
curl -s https://status.openrouter.ai/api/v2/status.json | jq '.status'
```

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| No generation ID in response | Request failed before reaching provider | Check network, verify base URL is `https://openrouter.ai/api/v1` |
| Generation metadata missing | Fetched too soon or wrong key | Wait 1-2s; use same API key that made the request |
| Intermittent 502/503 | Upstream provider outage | Check status.openrouter.ai; try different provider |
| `model_not_found` | Model ID typo or model removed | Query `/api/v1/models` to verify model exists |
| Slow TTFT (>10s) | Model cold start or overload | Use streaming; try `:floor` variant for different provider |

## Enterprise Considerations

- Always redact API keys from debug bundles before sharing (`sk-or-v1-...` -> `sk-or-v1-[REDACTED]`)
- Include the generation ID when contacting OpenRouter support -- it's the primary lookup key
- Log debug bundles to structured storage for post-incident analysis
- Set up automated debug bundle capture on 4xx/5xx responses in production
- Compare failing requests against a known-good baseline to isolate changes

## References

- [Examples](${CLAUDE_SKILL_DIR}/references/examples.md) | [Errors](${CLAUDE_SKILL_DIR}/references/errors.md)
- [Generation API](https://openrouter.ai/docs/api/api-reference/generation-queries/query-a-generation) | [Status](https://status.openrouter.ai)
