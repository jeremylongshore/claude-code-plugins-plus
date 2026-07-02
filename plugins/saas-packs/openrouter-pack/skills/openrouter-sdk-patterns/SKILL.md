---
name: openrouter-sdk-patterns
description: 'Build reusable OpenRouter client wrappers with retries, typing, and
  middleware. Use when creating SDKs or client libraries. Triggers: ''openrouter sdk'',
  ''openrouter client wrapper'', ''openrouter patterns'', ''openrouter library''.

  '
allowed-tools: Read, Write, Edit, Grep, Bash(python3:*), Bash(node:*)
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- openrouter
- sdk
- patterns
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# OpenRouter SDK Patterns

## Overview

Build production-grade OpenRouter client wrappers using the OpenAI SDK. The OpenAI Python/TypeScript SDKs work natively with OpenRouter by changing `base_url` to `https://openrouter.ai/api/v1`. This skill covers typed wrappers, retry strategies, middleware, and reusable patterns.

## Prerequisites

- An OpenRouter API key (`sk-or-v1-...`) exported as `OPENROUTER_API_KEY` — see the `openrouter-install-auth` skill for setup
- Python 3.8+ with the OpenAI SDK plus `requests` (used for the `/auth/key` credits check and `/generation` cost lookups), or Node.js 18+ with the OpenAI SDK
- Optional: `tenacity` if you want the custom retry decorator beyond the SDK's built-in backoff
- An app name and URL to send as `HTTP-Referer` / `X-Title` default headers for dashboard attribution

## Instructions

1. Start from the Python: Production Client Wrapper (or the TypeScript variant): point the OpenAI SDK at `base_url="https://openrouter.ai/api/v1"`, read `OPENROUTER_API_KEY` from the environment, and set the `HTTP-Referer` / `X-Title` default headers in the constructor.
2. Return typed results from every call — the `CompletionResult` dataclass/interface captures `content`, the served `model`, `prompt_tokens`/`completion_tokens`, `generation_id`, and `latency_ms`.
3. Tune the SDK's built-in retries per the Retry Strategy section (`max_retries`, `timeout` in the constructor); add the `tenacity` decorator only when you need retry behavior beyond the SDK's 429/5xx/connection handling.
4. Layer cross-cutting concerns via the Middleware Pattern — `with_cost_tracking` queries `GET /api/v1/generation?id=` after each request and accumulates a session cost total.
5. Surface remaining credits and rate limits with `check_credits()`, which calls `GET /api/v1/auth/key` with the same key.
6. Map SDK exceptions using the Error Handling table, then apply the Enterprise Considerations (single central wrapper, dependency injection for tests, SLA-based `max_retries`).

## Python: Production Client Wrapper

```python
import os, time, hashlib, json, logging
from dataclasses import dataclass
from typing import Optional
from openai import OpenAI, APIError, RateLimitError, APITimeoutError

log = logging.getLogger("openrouter")

@dataclass
class CompletionResult:
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    generation_id: str
    latency_ms: float

class OpenRouterClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        app_name: str = "my-app",
        app_url: str = "https://my-app.com",
        max_retries: int = 3,
        timeout: float = 60.0,
    ):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key or os.environ["OPENROUTER_API_KEY"],
            max_retries=max_retries,  # Built-in SDK retry with backoff
            timeout=timeout,
            default_headers={
                "HTTP-Referer": app_url,
                "X-Title": app_name,
            },
        )
        self._cache: dict[str, CompletionResult] = {}

    def complete(
        self,
        prompt: str,
        model: str = "anthropic/claude-3.5-sonnet",
        system: str = "",
        max_tokens: int = 1024,
        temperature: float = 0.7,
        cache: bool = False,
        **extra_params,
    ) -> CompletionResult:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        # Optional caching (deterministic requests only)
        cache_key = None
        if cache and temperature == 0:
            cache_key = hashlib.sha256(
                json.dumps({"model": model, "messages": messages, "max_tokens": max_tokens}).encode()
            ).hexdigest()
            if cache_key in self._cache:
                log.debug(f"Cache hit: {cache_key[:12]}")
                return self._cache[cache_key]

        start = time.monotonic()
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            **extra_params,
        )
        latency = (time.monotonic() - start) * 1000

        result = CompletionResult(
            content=response.choices[0].message.content or "",
            model=response.model,
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            generation_id=response.id,
            latency_ms=round(latency, 1),
        )

        log.info(f"[{result.model}] {result.prompt_tokens}+{result.completion_tokens} tokens, {result.latency_ms}ms")

        if cache_key:
            self._cache[cache_key] = result
        return result

    def check_credits(self) -> dict:
        """Check remaining credits and rate limits."""
        import requests
        resp = requests.get(
            "https://openrouter.ai/api/v1/auth/key",
            headers={"Authorization": f"Bearer {self.client.api_key}"},
        )
        return resp.json()["data"]

# Usage
or_client = OpenRouterClient(app_name="my-saas")
result = or_client.complete("Explain recursion", model="openai/gpt-4o-mini", max_tokens=200)
print(f"{result.content}\n---\n{result.model} | {result.latency_ms}ms | {result.prompt_tokens}+{result.completion_tokens} tokens")
```

## TypeScript: Production Client Wrapper

```typescript
import OpenAI from "openai";

interface CompletionResult {
  content: string;
  model: string;
  promptTokens: number;
  completionTokens: number;
  generationId: string;
  latencyMs: number;
}

class OpenRouterClient {
  private client: OpenAI;

  constructor(opts: { apiKey?: string; appName?: string; appUrl?: string } = {}) {
    this.client = new OpenAI({
      baseURL: "https://openrouter.ai/api/v1",
      apiKey: opts.apiKey ?? process.env.OPENROUTER_API_KEY,
      maxRetries: 3,
      timeout: 60_000,
      defaultHeaders: {
        "HTTP-Referer": opts.appUrl ?? "https://my-app.com",
        "X-Title": opts.appName ?? "My App",
      },
    });
  }

  async complete(
    prompt: string,
    opts: { model?: string; system?: string; maxTokens?: number; temperature?: number } = {}
  ): Promise<CompletionResult> {
    const messages: OpenAI.ChatCompletionMessageParam[] = [];
    if (opts.system) messages.push({ role: "system", content: opts.system });
    messages.push({ role: "user", content: prompt });

    const start = performance.now();
    const res = await this.client.chat.completions.create({
      model: opts.model ?? "anthropic/claude-3.5-sonnet",
      messages,
      max_tokens: opts.maxTokens ?? 1024,
      temperature: opts.temperature ?? 0.7,
    });
    const latency = Math.round(performance.now() - start);

    return {
      content: res.choices[0].message.content ?? "",
      model: res.model,
      promptTokens: res.usage?.prompt_tokens ?? 0,
      completionTokens: res.usage?.completion_tokens ?? 0,
      generationId: res.id,
      latencyMs: latency,
    };
  }
}

// Usage
const or = new OpenRouterClient({ appName: "my-saas" });
const result = await or.complete("Explain recursion", { model: "openai/gpt-4o-mini", maxTokens: 200 });
console.log(result.content, `\n${result.model} | ${result.latencyMs}ms`);
```

## Retry Strategy

The OpenAI SDK has built-in retries with exponential backoff for:

- 429 (rate limit) -- respects `Retry-After` header
- 5xx (server errors) -- retries with backoff
- Connection errors -- retries on network failures

```python
# Configure via constructor
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="sk-or-v1-...",
    max_retries=5,           # Default is 2
    timeout=120.0,           # Per-request timeout in seconds
)
```

For custom retry logic beyond the SDK:

```python
import tenacity

@tenacity.retry(
    retry=tenacity.retry_if_exception_type((RateLimitError, APITimeoutError)),
    wait=tenacity.wait_exponential(min=1, max=60),
    stop=tenacity.stop_after_attempt(5),
    before_sleep=lambda state: log.warning(f"Retry {state.attempt_number}: {state.outcome.exception()}"),
)
def robust_complete(client, **kwargs):
    return client.chat.completions.create(**kwargs)
```

## Middleware Pattern

```python
from functools import wraps
from typing import Callable

def with_cost_tracking(fn: Callable) -> Callable:
    """Middleware that logs cost per request."""
    total_cost = {"value": 0.0}

    @wraps(fn)
    def wrapper(*args, **kwargs):
        result = fn(*args, **kwargs)
        # Query generation cost asynchronously
        import requests
        gen = requests.get(
            f"https://openrouter.ai/api/v1/generation?id={result.id}",
            headers={"Authorization": f"Bearer {args[0].api_key}"},
        ).json()
        cost = float(gen.get("data", {}).get("total_cost", 0))
        total_cost["value"] += cost
        log.info(f"Request cost: ${cost:.6f} | Session total: ${total_cost['value']:.4f}")
        return result
    wrapper.total_cost = total_cost
    return wrapper
```

## Output

- A typed `CompletionResult` per call: `content`, the `model` that actually served the request, `prompt_tokens`/`completion_tokens`, the `gen-...` `generation_id`, and `latency_ms`
- A structured log line per request, e.g. `[openai/gpt-4o-mini] 12+87 tokens, 843.2ms`
- Cost-tracking middleware output: per-request cost plus a running session total, e.g. `Request cost: $0.000123 | Session total: $0.0045`
- A credits dict from `check_credits()` with usage and limit data from `/api/v1/auth/key`

## Examples

Instantiate the wrapper once and make a typed call:

```python
or_client = OpenRouterClient(app_name="my-saas")
result = or_client.complete("Explain recursion", model="openai/gpt-4o-mini", max_tokens=200)
print(f"{result.model} | {result.latency_ms}ms | {result.prompt_tokens}+{result.completion_tokens} tokens")
# openai/gpt-4o-mini | 812.4ms | 11+142 tokens
```

The reference implementation also shows task helpers (`summarize`, `classify`) built on the same wrapper. More worked examples: `references/examples.md`.

## Error Handling

| Exception | HTTP | Cause | Fix |
|-----------|------|-------|-----|
| `AuthenticationError` | 401 | Bad API key | Check `OPENROUTER_API_KEY` |
| `RateLimitError` | 429 | Too many requests | SDK auto-retries; increase `max_retries` |
| `APITimeoutError` | -- | Response too slow | Increase `timeout`; use streaming |
| `BadRequestError` | 400 | Invalid params | Check model ID, messages format |

## Enterprise Considerations

- Centralize all OpenRouter calls through a single client wrapper for consistent logging, retries, and cost tracking
- Type all response shapes with dataclasses/interfaces for compile-time safety
- Use dependency injection to swap between OpenRouter and direct provider clients in tests
- Set `max_retries` based on your SLA (2 for interactive, 5 for batch)
- Wrap middleware in try/catch so instrumentation never breaks the main request flow

## References

- Examples | Errors
- [OpenRouter SDK](https://openrouter.ai/sdk) | [API Reference](https://openrouter.ai/docs/api/reference/overview)
