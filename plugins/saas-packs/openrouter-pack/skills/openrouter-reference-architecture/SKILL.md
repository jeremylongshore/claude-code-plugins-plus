---
name: openrouter-reference-architecture
description: |
  Design production architectures using OpenRouter as the LLM gateway. Use when planning system design, reviewing architecture, or scaling AI applications. Triggers: 'openrouter architecture', 'openrouter system design', 'openrouter at scale', 'llm gateway architecture'.
allowed-tools: Read, Write, Edit, Bash, Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, openrouter, architecture, system-design, scaling]

---
# OpenRouter Reference Architecture

## Overview

OpenRouter serves as a unified LLM gateway, abstracting provider complexity. A production architecture wraps it with caching, rate limiting, cost controls, observability, and async processing. This skill provides three reference architectures: simple (single service), standard (microservice), and enterprise (event-driven).

## Architecture 1: Simple (Single Service)

```
┌─────────────┐     ┌──────────────────────────┐     ┌──────────────┐
│  Your App   │────▶│  OpenRouter Client        │────▶│  OpenRouter  │
│             │     │  - Retry (SDK built-in)   │     │  /api/v1     │
│             │◀────│  - Cost tracking          │◀────│              │
│             │     │  - Structured logging     │     └──────────────┘
└─────────────┘     └──────────────────────────┘
```

```python
import os, logging
from openai import OpenAI

log = logging.getLogger("llm")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    max_retries=3,
    timeout=30.0,
    default_headers={"HTTP-Referer": "https://my-app.com", "X-Title": "my-app"},
)

def complete(prompt, model="openai/gpt-4o-mini", **kwargs):
    kwargs.setdefault("max_tokens", 1024)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        **kwargs,
    )
    log.info(f"[{response.model}] {response.usage.prompt_tokens}+{response.usage.completion_tokens} tokens")
    return response.choices[0].message.content
```

## Architecture 2: Standard (Microservice)

```
┌─────────────┐     ┌─────────────────────┐     ┌──────────────┐
│  API Gateway│────▶│  AI Service          │────▶│  OpenRouter  │
│  (auth,     │     │  ┌─────────────┐    │     │  /api/v1     │
│   rate-limit│     │  │ Router      │    │     └──────────────┘
│   logging)  │     │  │ (task→model)│    │
└─────────────┘     │  └─────────────┘    │
                    │  ┌─────────────┐    │
                    │  │ Cache       │◀──▶│── Redis
                    │  │ (TTL-based) │    │
                    │  └─────────────┘    │
                    │  ┌─────────────┐    │
                    │  │ Budget      │◀──▶│── SQLite/Postgres
                    │  │ Enforcer    │    │
                    │  └─────────────┘    │
                    └─────────────────────┘
```

```python
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel

app = FastAPI()

class CompletionRequest(BaseModel):
    prompt: str
    task_type: str = "general"  # classification, code, analysis, etc.
    max_tokens: int = 1024
    user_id: str = "anonymous"

ROUTING_TABLE = {
    "classification": "openai/gpt-4o-mini",
    "code": "anthropic/claude-3.5-sonnet",
    "analysis": "anthropic/claude-3.5-sonnet",
    "general": "openai/gpt-4o-mini",
    "budget": "meta-llama/llama-3.1-8b-instruct",
}

@app.post("/v1/complete")
async def complete(req: CompletionRequest):
    model = ROUTING_TABLE.get(req.task_type, "openai/gpt-4o-mini")

    # Check cache first (for deterministic requests)
    cached = cache.get(model, req.prompt)
    if cached:
        return {"content": cached, "cached": True}

    # Check budget
    budget.check(req.user_id, model, estimate_tokens(req.prompt), req.max_tokens)

    # Call OpenRouter
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": req.prompt}],
        max_tokens=req.max_tokens,
        extra_body={
            "models": [model, "openai/gpt-4o-mini"],  # Fallback
            "route": "fallback",
        },
    )

    # Record cost and cache
    budget.record(req.user_id, response.id)
    cache.set(model, req.prompt, response.choices[0].message.content)

    return {
        "content": response.choices[0].message.content,
        "model": response.model,
        "tokens": response.usage.prompt_tokens + response.usage.completion_tokens,
    }
```

## Architecture 3: Enterprise (Event-Driven)

```
┌──────────┐    ┌───────────┐    ┌──────────────┐    ┌──────────────┐
│  API     │───▶│  Queue    │───▶│  Workers     │───▶│  OpenRouter  │
│  Gateway │    │  (Redis/  │    │  (auto-scale) │    │  /api/v1     │
└──────────┘    │  SQS)     │    │  ┌──────────┐│    └──────────────┘
                └───────────┘    │  │ Router   ││
                     │           │  │ Cache    ││
                     ▼           │  │ Budget   ││
                ┌───────────┐    │  │ Audit    ││
                │  Results  │◀───│  └──────────┘│
                │  Store    │    └──────────────┘
                └───────────┘
                     │
                ┌───────────┐    ┌──────────────┐
                │  Metrics  │───▶│  Dashboard   │
                │  (OTEL)   │    │  Alerts      │
                └───────────┘    └──────────────┘
```

```python
# Worker that processes queued AI requests
import json, redis

r = redis.Redis()

def worker_loop():
    """Process AI requests from the queue."""
    while True:
        _, raw = r.brpop("ai:requests")
        request = json.loads(raw)

        try:
            response = client.chat.completions.create(
                model=request["model"],
                messages=request["messages"],
                max_tokens=request.get("max_tokens", 1024),
                extra_body={
                    "models": [request["model"], "openai/gpt-4o-mini"],
                    "route": "fallback",
                },
            )
            result = {
                "id": request["id"],
                "content": response.choices[0].message.content,
                "model": response.model,
                "status": "complete",
            }
        except Exception as e:
            result = {"id": request["id"], "error": str(e), "status": "failed"}

        r.lpush(f"ai:results:{request['id']}", json.dumps(result))
        r.expire(f"ai:results:{request['id']}", 3600)
```

## Choosing an Architecture

| Factor | Simple | Standard | Enterprise |
|--------|--------|----------|------------|
| Team size | 1-3 | 3-10 | 10+ |
| Requests/day | <1K | 1K-100K | 100K+ |
| Latency needs | Tolerant | Low | Mixed (sync+async) |
| Budget tracking | Basic | Per-user | Per-user + department |
| Failure handling | SDK retries | Fallback chain | Queue + retry + DLQ |
| Observability | Logging | Metrics + logging | Full OTEL tracing |

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| Single point of failure | No redundancy in AI service | Deploy 2+ instances behind load balancer |
| Queue backlog | Worker throughput < incoming rate | Auto-scale workers; implement backpressure |
| Cache stampede | Many requests for same uncached key | Use cache locking or singleflight pattern |
| Budget bypass | Direct calls skipping middleware | All calls must go through the AI service |

## Enterprise Considerations

- Start with Architecture 1 and evolve to 2/3 as scale demands
- Use the queue-based pattern for any request that can tolerate >1s latency (cost reports, batch processing)
- OpenTelemetry traces should span from API gateway through AI service to OpenRouter
- Implement dead letter queues (DLQ) for failed requests that exhaust all retries
- Run separate worker pools for different priority levels (real-time vs batch)
- All architectures should share the same OpenRouter client wrapper for consistent logging and cost tracking

## References

- [Examples](${CLAUDE_SKILL_DIR}/references/examples.md) | [Errors](${CLAUDE_SKILL_DIR}/references/errors.md)
- [API Reference](https://openrouter.ai/docs/api/reference/overview) | [Model Routing](https://openrouter.ai/docs/features/model-routing)
