# Debug Bundle — Runnable Examples

## Python — Collect a Debug Bundle

```python
import os
import json
import time
import platform
import importlib.metadata
from datetime import datetime, timezone
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)


def collect_debug_bundle(prompt: str, model: str = "openai/gpt-3.5-turbo") -> dict:
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    messages = [{"role": "user", "content": prompt}]
    bundle: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "python_version": platform.python_version(),
            "openai_sdk_version": importlib.metadata.version("openai"),
        },
        "request": {
            "url": "https://openrouter.ai/api/v1/chat/completions",
            "model": model,
            "messages": messages,
            "api_key_preview": f"{api_key[:8]}...",
        },
        "response": None,
        "error": None,
        "generation_id": None,
        "latency_ms": None,
    }

    start = time.perf_counter()
    try:
        response = client.chat.completions.create(
            model=model, messages=messages, max_tokens=300,
        )
        elapsed = (time.perf_counter() - start) * 1000
        bundle["latency_ms"] = round(elapsed, 1)
        bundle["generation_id"] = response.id
        bundle["response"] = {
            "status_code": 200,
            "id": response.id,
            "model": response.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
        }
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        bundle["latency_ms"] = round(elapsed, 1)
        bundle["error"] = {
            "type": type(e).__name__,
            "message": str(e),
            "status_code": getattr(e, "status_code", None),
        }
    return bundle


if __name__ == "__main__":
    bundle = collect_debug_bundle("What is 2 + 2?")
    json.dump(bundle, open("openrouter-debug.json", "w"), indent=2)
    print(f"Generation ID: {bundle.get('generation_id')}")
    print(f"Latency: {bundle.get('latency_ms')}ms")
    print(json.dumps(bundle, indent=2))
```

## TypeScript — Request/Response Logger

```typescript
import OpenAI from "openai";
import fs from "fs";

const client = new OpenAI({
  baseURL: "https://openrouter.ai/api/v1",
  apiKey: process.env.OPENROUTER_API_KEY!,
});

interface DebugBundle {
  timestamp: string;
  request: { model: string; messagesCount: number };
  response?: { id: string; model: string; totalTokens: number; latencyMs: number };
  error?: { type: string; status: number | null; message: string };
}

async function trackedCompletion(prompt: string, model = "openai/gpt-3.5-turbo") {
  const bundle: DebugBundle = {
    timestamp: new Date().toISOString(),
    request: { model, messagesCount: 1 },
  };
  const start = performance.now();
  try {
    const res = await client.chat.completions.create({
      model, messages: [{ role: "user", content: prompt }], max_tokens: 300,
    });
    bundle.response = {
      id: res.id, model: res.model,
      totalTokens: res.usage?.total_tokens ?? 0,
      latencyMs: Math.round(performance.now() - start),
    };
    return { result: res.choices[0].message.content || "", bundle };
  } catch (err) {
    bundle.error = {
      type: (err as Error).constructor.name,
      status: (err as any).status ?? null,
      message: (err as Error).message,
    };
    throw Object.assign(err as Error, { bundle });
  }
}

const { result, bundle } = await trackedCompletion("Explain async/await briefly.");
console.log("Result:", result);
fs.writeFileSync("debug-bundle.json", JSON.stringify(bundle, null, 2));
console.log(`Generation ID: ${bundle.response?.id}`);
```

## Python — Diff Failing vs Working Request

```python
def diff_requests(working: dict, failing: dict) -> list[str]:
    diffs = []

    def compare(path: str, a, b):
        if type(a) != type(b):
            diffs.append(f"TYPE MISMATCH at {path}: {type(a).__name__} -> {type(b).__name__}")
            return
        if isinstance(a, dict):
            for key in set(list(a.keys()) + list(b.keys())):
                if key not in a:
                    diffs.append(f"ADDED   {path}.{key}: {b[key]!r}")
                elif key not in b:
                    diffs.append(f"REMOVED {path}.{key}: {a[key]!r}")
                else:
                    compare(f"{path}.{key}", a[key], b[key])
        elif a != b:
            diffs.append(f"CHANGED {path}: {a!r} -> {b!r}")

    compare("request", working, failing)
    return diffs


working_request = {
    "model": "openai/gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 100,
}
failing_request = {
    "model": "gpt-3.5-turbo",  # Missing provider prefix!
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 100,
}

for d in diff_requests(working_request, failing_request):
    print(d)
# CHANGED request.model: 'openai/gpt-3.5-turbo' -> 'gpt-3.5-turbo'
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
