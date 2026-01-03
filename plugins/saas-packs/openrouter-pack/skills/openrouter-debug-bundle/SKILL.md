---
name: openrouter-debug-bundle
description: |
  Set up comprehensive logging and debugging for OpenRouter. Use when investigating issues or monitoring requests. Trigger with phrases like 'openrouter debug', 'openrouter logging', 'openrouter trace', 'monitor openrouter'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# OpenRouter Debug Bundle

## Overview

This skill shows how to implement request/response logging, timing metrics, and debugging utilities for OpenRouter integrations.

## Prerequisites

- OpenRouter integration
- Logging infrastructure (optional but recommended)

## Instructions

Follow these steps to implement this skill:

1. **Verify Prerequisites**: Ensure all prerequisites listed above are met
2. **Review the Implementation**: Study the code examples and patterns below
3. **Adapt to Your Environment**: Modify configuration values for your setup
4. **Test the Integration**: Run the verification steps to confirm functionality
5. **Monitor in Production**: Set up appropriate logging and monitoring

## Overview

This skill shows how to implement request/response logging, timing metrics, and debugging utilities for OpenRouter integrations.

## Prerequisites

- OpenRouter integration
- Logging infrastructure (optional but recommended)

## Request Logging

### Python Debug Wrapper
```python
import json
import time
from datetime import datetime
from openai import OpenAI

class DebugOpenRouterClient:
    def __init__(self, api_key: str, log_file: str = "openrouter_debug.log"):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )
        self.log_file = log_file

    def _log(self, data: dict):
        with open(self.log_file, "a") as f:
            f.write(json.dumps(data, indent=2) + "\n---\n")

    def chat(self, model: str, messages: list, **kwargs):
        request_id = datetime.now().isoformat()
        start_time = time.time()

        # Log request
        self._log({
            "type": "request",
            "id": request_id,
            "timestamp": request_id,
            "model": model,
            "messages": messages,
            "kwargs": kwargs
        })

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs
            )
            elapsed = time.time() - start_time

            # Log success
            self._log({
                "type": "response",
                "id": request_id,
                "elapsed_seconds": elapsed,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "finish_reason": response.choices[0].finish_reason,
                "content_preview": response.choices[0].message.content[:200]
            })

            return response

        except Exception as e:
            elapsed = time.time() - start_time

            # Log error
            self._log({
                "type": "error",
                "id": request_id,
                "elapsed_seconds": elapsed,
                "error_type": type(e).__name__,
                "error_message": str(e)
            })
            raise

# Usage
client = DebugOpenRouterClient(api_key=os.environ["OPENROUTER_API_KEY"])
response = client.chat("openai/gpt-4-turbo", [{"role": "user", "content": "Hello"}])
```

### TypeScript Debug Wrapper
```typescript
import OpenAI from 'openai';
import fs from 'fs';

class DebugOpenRouterClient {
  private client: OpenAI;
  private logFile: string;

  constructor(apiKey: string, logFile = 'openrouter_debug.log') {
    this.client = new OpenAI({
      baseURL: 'https://openrouter.ai/api/v1',
      apiKey,
    });
    this.logFile = logFile;
  }

  private log(data: object) {
    fs.appendFileSync(
      this.logFile,
      JSON.stringify(data, null, 2) + '\n---\n'
    );
  }

  async chat(
    model: string,
    messages: OpenAI.Chat.ChatCompletionMessageParam[],
    options: Partial<OpenAI.Chat.ChatCompletionCreateParams> = {}
  ) {
    const requestId = new Date().toISOString();
    const startTime = Date.now();

    this.log({
      type: 'request',
      id: requestId,
      timestamp: requestId,
      model,
      messages,
      options,
    });

    try {
      const response = await this.client.chat.completions.create({
        model,
        messages,
        ...options,
      });

      const elapsed = (Date.now() - startTime) / 1000;

      this.log({
        type: 'response',
        id: requestId,
        elapsed_seconds: elapsed,
        model: response.model,
        usage: response.usage,
        finish_reason: response.choices[0].finish_reason,
        content_preview: response.choices[0].message.content?.slice(0, 200),
      });

      return response;
    } catch (error) {
      const elapsed = (Date.now() - startTime) / 1000;

      this.log({
        type: 'error',
        id: requestId,
        elapsed_seconds: elapsed,
        error_type: error.constructor.name,
        error_message: String(error),
      });

      throw error;
    }
  }
}
```

## HTTP-Level Debugging

### cURL Verbose Mode
```bash
curl -v https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello"}]
  }' 2>&1 | tee openrouter_debug.txt
```

### Python httpx Logging
```python
import httpx
import logging

# Enable HTTP debug logging
logging.basicConfig(level=logging.DEBUG)
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.DEBUG)

# Now all OpenAI SDK requests are logged
from openai import OpenAI
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"]
)
```

## Response Analysis

### Token Usage Tracking
```python
class UsageTracker:
    def __init__(self):
        self.requests = []

    def track(self, response, model: str, estimated_cost: float):
        self.requests.append({
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
            "estimated_cost": estimated_cost
        })

    def summary(self):
        total_tokens = sum(r["total_tokens"] for r in self.requests)
        total_cost = sum(r["estimated_cost"] for r in self.requests)
        return {
            "total_requests": len(self.requests),
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "by_model": self._group_by_model()
        }

    def _group_by_model(self):
        models = {}
        for r in self.requests:
            model = r["model"]
            if model not in models:
                models[model] = {"requests": 0, "tokens": 0, "cost": 0}
            models[model]["requests"] += 1
            models[model]["tokens"] += r["total_tokens"]
            models[model]["cost"] += r["estimated_cost"]
        return models

tracker = UsageTracker()
```

### Latency Monitoring
```python
import statistics

class LatencyMonitor:
    def __init__(self):
        self.latencies = {}

    def record(self, model: str, latency_ms: float):
        if model not in self.latencies:
            self.latencies[model] = []
        self.latencies[model].append(latency_ms)

    def stats(self, model: str):
        if model not in self.latencies:
            return None
        data = self.latencies[model]
        return {
            "count": len(data),
            "mean": statistics.mean(data),
            "median": statistics.median(data),
            "stdev": statistics.stdev(data) if len(data) > 1 else 0,
            "min": min(data),
            "max": max(data),
            "p95": sorted(data)[int(len(data) * 0.95)] if len(data) > 20 else max(data)
        }
```

## Debug Information Gathering

### System Debug Function
```python
def gather_debug_info():
    """Collect all relevant debug information."""
    import platform
    import sys

    info = {
        "python_version": sys.version,
        "platform": platform.platform(),
        "openai_sdk_version": None,
        "api_key_set": bool(os.environ.get("OPENROUTER_API_KEY")),
        "api_key_prefix": os.environ.get("OPENROUTER_API_KEY", "")[:10] + "...",
    }

    try:
        import openai
        info["openai_sdk_version"] = openai.__version__
    except:
        pass

    # Test connectivity
    try:
        response = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {os.environ.get('OPENROUTER_API_KEY')}"},
            timeout=10
        )
        info["api_connectivity"] = response.status_code == 200
        info["models_count"] = len(response.json().get("data", []))
    except Exception as e:
        info["api_connectivity"] = False
        info["connectivity_error"] = str(e)

    return info

# Print debug info
import json
print(json.dumps(gather_debug_info(), indent=2))
```

### Request Debug Template
```python
def debug_request(model, messages, **kwargs):
    """Create a debug-friendly request."""
    print("=" * 50)
    print("DEBUG REQUEST")
    print("=" * 50)
    print(f"Model: {model}")
    print(f"Messages: {json.dumps(messages, indent=2)}")
    print(f"Options: {json.dumps(kwargs, indent=2)}")
    print("=" * 50)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs
        )

        print("SUCCESS")
        print(f"Response model: {response.model}")
        print(f"Tokens: {response.usage.total_tokens}")
        print(f"Finish reason: {response.choices[0].finish_reason}")
        print(f"Content: {response.choices[0].message.content[:500]}...")

        return response

    except Exception as e:
        print("ERROR")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        raise
```

## Log Analysis

### Parse Debug Log
```python
def analyze_debug_log(log_file: str):
    """Analyze debug log file."""
    with open(log_file) as f:
        content = f.read()

    entries = content.split("---\n")
    requests = []
    responses = []
    errors = []

    for entry in entries:
        if not entry.strip():
            continue
        try:
            data = json.loads(entry)
            if data["type"] == "request":
                requests.append(data)
            elif data["type"] == "response":
                responses.append(data)
            elif data["type"] == "error":
                errors.append(data)
        except:
            pass

    return {
        "total_requests": len(requests),
        "successful": len(responses),
        "failed": len(errors),
        "error_rate": len(errors) / max(len(requests), 1),
        "avg_latency": sum(r["elapsed_seconds"] for r in responses) / max(len(responses), 1),
        "error_types": list(set(e["error_type"] for e in errors))
    }
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
