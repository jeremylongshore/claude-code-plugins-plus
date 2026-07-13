# Model Availability — Runnable Examples

## Python — Model Health Check

```python
import os
import time
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

CRITICAL_MODELS = [
    "anthropic/claude-3.5-sonnet",
    "openai/gpt-3.5-turbo",
    "google/gemma-2-9b-it:free",
]

FALLBACK_MAP = {
    "anthropic/claude-3.5-sonnet": "openai/gpt-4-turbo",
    "openai/gpt-3.5-turbo": "google/gemma-2-9b-it:free",
}


def probe_model(model_id: str) -> dict:
    start = time.perf_counter()
    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=1,
        )
        latency = (time.perf_counter() - start) * 1000
        return {"model": model_id, "status": "ok", "latency_ms": round(latency, 1)}
    except Exception as e:
        latency = (time.perf_counter() - start) * 1000
        return {
            "model": model_id,
            "status": "error",
            "error": str(e)[:100],
            "latency_ms": round(latency, 1),
        }


def run_health_checks() -> dict[str, dict]:
    results = {}
    for model in CRITICAL_MODELS:
        result = probe_model(model)
        results[model] = result
        status_icon = "OK" if result["status"] == "ok" else "FAIL"
        print(f"[{status_icon}] {model}: {result['latency_ms']}ms")
        if result["status"] != "ok":
            fallback = FALLBACK_MAP.get(model)
            if fallback:
                print(f"       -> Fallback: {fallback}")
    return results


def get_available_model(preferred: str) -> str:
    probe = probe_model(preferred)
    if probe["status"] == "ok":
        return preferred
    fallback = FALLBACK_MAP.get(preferred, "openai/gpt-3.5-turbo")
    print(f"[WARN] {preferred} unavailable — using {fallback}")
    return fallback


if __name__ == "__main__":
    results = run_health_checks()
    ok = [m for m, r in results.items() if r["status"] == "ok"]
    failed = [m for m, r in results.items() if r["status"] != "ok"]
    print(f"\n{len(ok)}/{len(CRITICAL_MODELS)} models healthy")
    if failed:
        print(f"Failed: {failed}")
```

## TypeScript — Availability Monitor

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://openrouter.ai/api/v1",
  apiKey: process.env.OPENROUTER_API_KEY!,
});

interface ModelStatus {
  model: string;
  available: boolean;
  latencyMs: number;
  consecutiveFailures: number;
}

const modelStatusMap = new Map<string, ModelStatus>();
const ALERT_THRESHOLD = 3;

async function checkModel(modelId: string): Promise<ModelStatus> {
  const previous = modelStatusMap.get(modelId);
  const start = performance.now();
  try {
    await client.chat.completions.create({
      model: modelId,
      messages: [{ role: "user", content: "1" }],
      max_tokens: 1,
    });
    const status: ModelStatus = {
      model: modelId, available: true,
      latencyMs: Math.round(performance.now() - start),
      consecutiveFailures: 0,
    };
    modelStatusMap.set(modelId, status);
    return status;
  } catch {
    const failures = (previous?.consecutiveFailures ?? 0) + 1;
    const status: ModelStatus = {
      model: modelId, available: false,
      latencyMs: Math.round(performance.now() - start),
      consecutiveFailures: failures,
    };
    modelStatusMap.set(modelId, status);
    if (failures >= ALERT_THRESHOLD) {
      console.error(`[ALERT] ${modelId} failed ${failures} consecutive checks`);
    }
    return status;
  }
}

const models = ["anthropic/claude-3.5-sonnet", "openai/gpt-3.5-turbo", "google/gemma-2-9b-it:free"];
const results = await Promise.allSettled(models.map(checkModel));
results.forEach((r) => {
  if (r.status === "fulfilled") {
    const s = r.value;
    console.log(`[${s.available ? "OK" : "FAIL"}] ${s.model} (${s.latencyMs}ms)`);
  }
});
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
