---
name: openrouter-prod-checklist
description: |
  Pre-launch production readiness checklist for OpenRouter. Use when preparing to deploy to production. Trigger with phrases like 'openrouter production', 'openrouter go-live', 'openrouter launch checklist', 'deploy openrouter'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# OpenRouter Production Checklist

## Overview

This skill provides a comprehensive checklist covering security, monitoring, error handling, and operational readiness for production OpenRouter deployments.

## Prerequisites

- Working OpenRouter integration
- Production infrastructure ready

## Instructions

Follow these steps to implement this skill:

1. **Verify Prerequisites**: Ensure all prerequisites listed above are met
2. **Review the Implementation**: Study the code examples and patterns below
3. **Adapt to Your Environment**: Modify configuration values for your setup
4. **Test the Integration**: Run the verification steps to confirm functionality
5. **Monitor in Production**: Set up appropriate logging and monitoring

## Overview

This skill provides a comprehensive checklist covering security, monitoring, error handling, and operational readiness for production OpenRouter deployments.

## Prerequisites

- Working OpenRouter integration
- Production infrastructure ready

## Pre-Launch Checklist

### API Key Security
```
[ ] API key stored in environment variable, not code
[ ] Key has appropriate credit limit set
[ ] Production key separate from development key
[ ] Key has descriptive label in dashboard
[ ] HTTP-Referer header set for tracking
[ ] X-Title header set for identification
```

### Error Handling
```
[ ] All API calls wrapped in try/catch
[ ] Rate limit errors handled with exponential backoff
[ ] Payment errors (402) caught and alerted
[ ] Model unavailability triggers fallback
[ ] Timeout handling implemented
[ ] Connection errors retry appropriately
```

### Fallbacks Configured
```
[ ] Primary model selected
[ ] At least 2 fallback models configured
[ ] Fallbacks tested and verified working
[ ] Model unavailability detection in place
[ ] Automatic failover logic implemented
```

### Cost Controls
```
[ ] Per-key credit limits set
[ ] max_tokens limit on all requests
[ ] Token usage monitoring active
[ ] Cost alerts configured
[ ] Budget thresholds defined
```

### Monitoring
```
[ ] Request logging enabled
[ ] Error rate tracking active
[ ] Latency monitoring configured
[ ] Token usage dashboards set up
[ ] Alert thresholds defined
```

## Security Checklist

### Key Management
```python
# ✓ Correct: Environment variable
api_key = os.environ["OPENROUTER_API_KEY"]

# ✗ Wrong: Hardcoded
api_key = "sk-or-v1-xxxxx"

# ✓ Correct: Secrets manager
from google.cloud import secretmanager
client = secretmanager.SecretManagerServiceClient()
api_key = client.access_secret_version(name=secret_path).payload.data.decode()
```

### Request Validation
```python
def validate_request(prompt: str, model: str):
    """Validate before sending to API."""
    if not prompt or not prompt.strip():
        raise ValueError("Empty prompt")

    if len(prompt) > 100_000:  # ~25K tokens
        raise ValueError("Prompt too long")

    if "/" not in model:
        raise ValueError("Model must include provider prefix")

    # Sanitize if needed
    return prompt.strip()
```

### Response Handling
```python
def safe_extract_response(response) -> str:
    """Safely extract content from response."""
    if not response.choices:
        return ""

    content = response.choices[0].message.content
    if content is None:
        return ""

    # Optionally sanitize output
    return content
```

## Production Configuration

### Recommended Defaults
```python
PRODUCTION_CONFIG = {
    # Timeouts
    "timeout": 60.0,          # Connection timeout
    "max_retries": 3,         # Retry count

    # Token limits
    "max_tokens": 4096,       # Default response limit
    "temperature": 0.7,       # Balanced creativity

    # Headers
    "http_referer": "https://your-app.com",
    "x_title": "Your App Name",

    # Fallback models
    "fallback_models": [
        "anthropic/claude-3.5-sonnet",
        "openai/gpt-4-turbo",
        "meta-llama/llama-3.1-70b-instruct"
    ]
}
```

### Production Client
```python
class ProductionOpenRouterClient:
    def __init__(self, config: dict = None):
        config = config or PRODUCTION_CONFIG

        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ["OPENROUTER_API_KEY"],
            timeout=config.get("timeout", 60.0),
            max_retries=config.get("max_retries", 3),
            default_headers={
                "HTTP-Referer": config.get("http_referer", ""),
                "X-Title": config.get("x_title", ""),
            }
        )
        self.fallback_models = config.get("fallback_models", [])
        self.max_tokens = config.get("max_tokens", 4096)

    def chat(
        self,
        prompt: str,
        model: str = "anthropic/claude-3.5-sonnet",
        **kwargs
    ):
        models_to_try = [model] + [
            m for m in self.fallback_models if m != model
        ]

        last_error = None
        for try_model in models_to_try:
            try:
                return self.client.chat.completions.create(
                    model=try_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=kwargs.get("max_tokens", self.max_tokens),
                    **{k: v for k, v in kwargs.items() if k != "max_tokens"}
                )
            except Exception as e:
                last_error = e
                if "unavailable" in str(e).lower():
                    continue
                raise

        raise last_error or Exception("All models failed")
```

## Monitoring Setup

### Basic Metrics
```python
import time
from dataclasses import dataclass
from typing import Optional

@dataclass
class RequestMetrics:
    model: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float
    success: bool
    error: Optional[str] = None

class MetricsCollector:
    def __init__(self):
        self.metrics = []

    def record(self, metrics: RequestMetrics):
        self.metrics.append(metrics)
        # Send to your monitoring system
        self._send_to_monitoring(metrics)

    def _send_to_monitoring(self, metrics: RequestMetrics):
        # Example: Send to StatsD/Datadog
        # statsd.gauge('openrouter.latency', metrics.latency_ms)
        # statsd.increment('openrouter.requests')
        pass

collector = MetricsCollector()

def monitored_chat(prompt: str, model: str):
    start = time.time()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )

        collector.record(RequestMetrics(
            model=model,
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            latency_ms=(time.time() - start) * 1000,
            success=True
        ))

        return response

    except Exception as e:
        collector.record(RequestMetrics(
            model=model,
            prompt_tokens=0,
            completion_tokens=0,
            latency_ms=(time.time() - start) * 1000,
            success=False,
            error=str(e)
        ))
        raise
```

### Health Check Endpoint
```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/health/openrouter")
def openrouter_health():
    try:
        # Quick health check
        response = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5,
            timeout=5.0
        )

        return jsonify({
            "status": "healthy",
            "model": "openai/gpt-3.5-turbo",
            "response_received": True
        })

    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 503
```

## Scaling Considerations

### Connection Pooling
```python
import httpx

# Use connection pooling for high-volume
http_client = httpx.Client(
    limits=httpx.Limits(
        max_keepalive_connections=20,
        max_connections=100
    )
)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    http_client=http_client
)
```

### Async for High Throughput
```python
from openai import AsyncOpenAI
import asyncio

async_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"]
)

async def process_batch(prompts: list, max_concurrent: int = 10):
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_one(prompt):
        async with semaphore:
            return await async_client.chat.completions.create(
                model="openai/gpt-4-turbo",
                messages=[{"role": "user", "content": prompt}]
            )

    return await asyncio.gather(*[process_one(p) for p in prompts])
```

## Launch Verification

### Pre-Launch Tests
```python
def run_production_verification():
    """Run before going live."""
    tests = []

    # Test 1: API connectivity
    try:
        models = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        tests.append(("API Connectivity", models.status_code == 200))
    except:
        tests.append(("API Connectivity", False))

    # Test 2: Primary model works
    try:
        response = client.chat.completions.create(
            model="anthropic/claude-3.5-sonnet",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
        tests.append(("Primary Model", True))
    except:
        tests.append(("Primary Model", False))

    # Test 3: Fallback models work
    for fallback in ["openai/gpt-4-turbo", "meta-llama/llama-3.1-70b-instruct"]:
        try:
            response = client.chat.completions.create(
                model=fallback,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            tests.append((f"Fallback: {fallback}", True))
        except:
            tests.append((f"Fallback: {fallback}", False))

    # Test 4: Credit balance
    try:
        key_info = requests.get(
            "https://openrouter.ai/api/v1/auth/key",
            headers={"Authorization": f"Bearer {api_key}"}
        ).json()
        has_credits = key_info["data"]["limit_remaining"] > 10
        tests.append(("Sufficient Credits", has_credits))
    except:
        tests.append(("Sufficient Credits", False))

    # Print results
    print("\nProduction Verification Results:")
    print("-" * 40)
    all_passed = True
    for name, passed in tests:
        status = "✓" if passed else "✗"
        print(f"  {status} {name}")
        if not passed:
            all_passed = False

    return all_passed

if not run_production_verification():
    print("\n⚠️  Some checks failed. Review before going live.")
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
