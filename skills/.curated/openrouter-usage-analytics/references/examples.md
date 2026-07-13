# Usage Analytics — Runnable Examples

## Python — Usage Tracking Middleware

```python
import os
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

MODEL_COST_PER_M = {
    "openai/gpt-3.5-turbo": 1.0,
    "openai/gpt-4": 60.0,
    "anthropic/claude-3.5-sonnet": 15.0,
    "anthropic/claude-3-haiku": 0.5,
    "google/gemma-2-9b-it:free": 0.0,
}

METRICS_FILE = Path("openrouter-metrics.jsonl")


def tracked_complete(prompt: str, model: str = "openai/gpt-3.5-turbo",
                     user_id: str | None = None) -> str:
    start = time.perf_counter()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
        )
        content = response.choices[0].message.content or ""
        latency_ms = round((time.perf_counter() - start) * 1000, 1)
        cost = response.usage.total_tokens * MODEL_COST_PER_M.get(response.model, 5.0) / 1_000_000

        metric = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "model": response.model,
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
            "cost_usd": cost,
            "latency_ms": latency_ms,
            "status": "ok",
        }
        with METRICS_FILE.open("a") as f:
            f.write(json.dumps(metric) + "\n")
        return content
    except Exception as e:
        latency_ms = round((time.perf_counter() - start) * 1000, 1)
        metric = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id, "model": model, "status": "error",
            "error": str(e)[:100], "latency_ms": latency_ms,
        }
        with METRICS_FILE.open("a") as f:
            f.write(json.dumps(metric) + "\n")
        raise


def daily_summary() -> dict:
    today = datetime.now(timezone.utc).date().isoformat()
    if not METRICS_FILE.exists():
        return {"date": today, "requests": 0}
    metrics = [json.loads(l) for l in METRICS_FILE.read_text().splitlines()
               if l.strip() and l.strip().startswith("{")]
    today_ok = [m for m in metrics if m.get("ts", "").startswith(today) and m.get("status") == "ok"]
    total_cost = sum(m.get("cost_usd", 0.0) for m in today_ok)
    total_tokens = sum(m.get("total_tokens", 0) for m in today_ok)
    avg_latency = sum(m.get("latency_ms", 0) for m in today_ok) / max(1, len(today_ok))
    return {
        "date": today,
        "requests": len(today_ok),
        "total_tokens": total_tokens,
        "total_cost": total_cost,
        "avg_latency_ms": round(avg_latency, 1),
    }


tracked_complete("What is machine learning?", user_id="alice")
tracked_complete("Write a haiku about Python", model="anthropic/claude-3-haiku", user_id="bob")

summary = daily_summary()
print(f"Today: {summary['requests']} requests, {summary['total_tokens']} tokens, ${summary['total_cost']:.4f}")
```

## TypeScript — Analytics Aggregator

```typescript
import fs from "fs";

interface MetricEntry {
  ts: string; model: string;
  total_tokens?: number; cost_usd?: number;
  latency_ms?: number; status: "ok" | "error";
}

function readMetrics(filePath: string): MetricEntry[] {
  if (!fs.existsSync(filePath)) return [];
  return fs.readFileSync(filePath, "utf8")
    .split("\n").filter(Boolean)
    .map((l) => { try { return JSON.parse(l); } catch { return null; } })
    .filter(Boolean) as MetricEntry[];
}

function aggregate(entries: MetricEntry[]) {
  const ok = entries.filter((e) => e.status === "ok");
  const models = [...new Set(ok.map((e) => e.model))];
  const byModel = Object.fromEntries(models.map((m) => {
    const me = ok.filter((e) => e.model === m);
    return [m, {
      requests: me.length,
      totalTokens: me.reduce((s, e) => s + (e.total_tokens ?? 0), 0),
      totalCost: me.reduce((s, e) => s + (e.cost_usd ?? 0), 0),
    }];
  }));
  return {
    totalRequests: ok.length,
    totalTokens: ok.reduce((s, e) => s + (e.total_tokens ?? 0), 0),
    totalCostUsd: ok.reduce((s, e) => s + (e.cost_usd ?? 0), 0),
    byModel,
  };
}

const entries = readMetrics("openrouter-metrics.jsonl");
const report = aggregate(entries);
console.log(`Requests: ${report.totalRequests}, Tokens: ${report.totalTokens}, Cost: $${report.totalCostUsd.toFixed(4)}`);
for (const [model, stats] of Object.entries(report.byModel)) {
  console.log(`  ${model}: ${stats.requests} reqs, $${stats.totalCost.toFixed(4)}`);
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
