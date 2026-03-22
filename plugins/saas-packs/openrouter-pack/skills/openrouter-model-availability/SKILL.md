---
name: openrouter-model-availability
description: |
  Monitor OpenRouter model availability and implement health checks. Use when building systems that depend on specific models being online. Triggers: 'openrouter model status', 'is model available', 'openrouter health check', 'model availability'.
allowed-tools: Read, Write, Edit, Bash, Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, openrouter, monitoring, availability]

---
# OpenRouter Model Availability

## Overview

OpenRouter's `/api/v1/models` endpoint is the source of truth for model availability. Models can be temporarily unavailable, have degraded performance, or be permanently removed. This skill covers querying model status, building health probes, tracking availability over time, and automating failover.

## Query Model Status

```bash
# Check if specific models exist and their status
curl -s https://openrouter.ai/api/v1/models | jq '[.data[] | select(
  .id == "anthropic/claude-3.5-sonnet" or
  .id == "openai/gpt-4o" or
  .id == "openai/gpt-4o-mini"
) | {
  id,
  context_length,
  prompt_per_M: ((.pricing.prompt | tonumber) * 1000000),
  completion_per_M: ((.pricing.completion | tonumber) * 1000000)
}]'

# List all available models (just IDs)
curl -s https://openrouter.ai/api/v1/models | jq '[.data[].id] | sort'

# Count models by provider
curl -s https://openrouter.ai/api/v1/models | jq '[.data[].id | split("/")[0]] | group_by(.) | map({provider: .[0], count: length}) | sort_by(-.count)'
```

## Health Check Service

```python
import os, time, logging
from datetime import datetime, timezone
from dataclasses import dataclass
import requests
from openai import OpenAI, APIError, APITimeoutError

log = logging.getLogger("openrouter.health")

@dataclass
class HealthStatus:
    model: str
    available: bool
    latency_ms: float
    checked_at: str
    error: str = ""

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    timeout=15.0,
    default_headers={"HTTP-Referer": "https://my-app.com", "X-Title": "health-check"},
)

def probe_model(model_id: str) -> HealthStatus:
    """Send a minimal request to test model availability."""
    start = time.monotonic()
    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=1,  # Minimal cost
        )
        latency = (time.monotonic() - start) * 1000
        return HealthStatus(
            model=model_id, available=True, latency_ms=round(latency, 1),
            checked_at=datetime.now(timezone.utc).isoformat(),
        )
    except (APIError, APITimeoutError) as e:
        latency = (time.monotonic() - start) * 1000
        return HealthStatus(
            model=model_id, available=False, latency_ms=round(latency, 1),
            checked_at=datetime.now(timezone.utc).isoformat(),
            error=str(e),
        )

def check_critical_models() -> list[HealthStatus]:
    """Probe all critical models."""
    CRITICAL_MODELS = [
        "anthropic/claude-3.5-sonnet",
        "openai/gpt-4o",
        "openai/gpt-4o-mini",
        "google/gemini-2.0-flash-001",
    ]
    results = []
    for model in CRITICAL_MODELS:
        status = probe_model(model)
        log.info(f"{'OK' if status.available else 'FAIL'} {model} ({status.latency_ms}ms)")
        results.append(status)
    return results
```

## Catalog-Based Availability Check

```python
def check_model_exists(model_id: str) -> dict:
    """Check if a model exists in the catalog (no API call cost)."""
    resp = requests.get("https://openrouter.ai/api/v1/models")
    models = {m["id"]: m for m in resp.json()["data"]}

    if model_id in models:
        m = models[model_id]
        return {
            "exists": True,
            "context_length": m["context_length"],
            "pricing": m["pricing"],
        }
    return {"exists": False, "suggestion": find_similar(model_id, models)}

def find_similar(model_id: str, models: dict) -> list[str]:
    """Find models with similar names (for migration when model is removed)."""
    prefix = model_id.split("/")[0]
    return [m for m in models if m.startswith(prefix)][:5]
```

## Availability Monitoring Script

```bash
#!/bin/bash
# Run as cron job: */5 * * * * /path/to/check_models.sh

MODELS=("anthropic/claude-3.5-sonnet" "openai/gpt-4o" "openai/gpt-4o-mini")
LOG_FILE="/var/log/openrouter-health.log"

for MODEL in "${MODELS[@]}"; do
  START=$(date +%s%N)
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    https://openrouter.ai/api/v1/chat/completions \
    -H "Authorization: Bearer $OPENROUTER_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"ping\"}],\"max_tokens\":1}" \
    --max-time 15)
  END=$(date +%s%N)
  LATENCY=$(( (END - START) / 1000000 ))

  STATUS="OK"
  [ "$HTTP_CODE" != "200" ] && STATUS="FAIL"

  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $STATUS $MODEL $HTTP_CODE ${LATENCY}ms" >> "$LOG_FILE"
done
```

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| Model not in catalog | Model renamed or removed | Use `find_similar()` to find replacement |
| Health check timeout (>15s) | Model overloaded or cold-starting | Distinguish slow vs down; increase timeout for probes |
| False positive down | Transient network issue | Require 2-3 consecutive failures before alerting |
| 402 on health check | Credits exhausted | Health checks cost ~$0.0001 each; ensure adequate credits |

## Enterprise Considerations

- Health probes cost tokens ($0.0001 or less per probe with `max_tokens: 1`) -- budget for monitoring
- Require 2-3 consecutive failures before marking a model as down to avoid false positives
- Cache the models list and refresh every 5 minutes -- don't hit `/api/v1/models` on every request
- Subscribe to OpenRouter announcements for model deprecations and new additions
- Maintain a model alias map so your code uses logical names (e.g., "primary-chat") that you can remap
- Alert when critical models disappear from the catalog, not just when they fail probes

## References

- [Examples](${CLAUDE_SKILL_DIR}/references/examples.md) | [Errors](${CLAUDE_SKILL_DIR}/references/errors.md)
- [Models API](https://openrouter.ai/docs/api/api-reference/models/get-models) | [Status](https://status.openrouter.ai)
