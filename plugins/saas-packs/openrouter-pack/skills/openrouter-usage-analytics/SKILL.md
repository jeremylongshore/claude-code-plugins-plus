---
name: openrouter-usage-analytics
description: |
  Track and analyze OpenRouter API usage patterns, costs, and performance. Use when building dashboards, optimizing spend, or reporting on AI usage. Triggers: 'openrouter analytics', 'openrouter usage', 'openrouter metrics', 'track openrouter spend'.
allowed-tools: Read, Write, Edit, Bash, Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, openrouter, analytics, cost-optimization, monitoring]

---
# OpenRouter Usage Analytics

## Overview

OpenRouter provides usage data through three endpoints: `GET /api/v1/auth/key` (credit balance and rate limits), `GET /api/v1/generation?id=` (per-request cost and metadata), and response `usage` fields (token counts). This skill covers collecting metrics from these sources, building analytics pipelines, cost reporting, and performance dashboards.

## Collect Per-Request Metrics

```python
import os, time, json, logging
from datetime import datetime, timezone
from openai import OpenAI
import requests as http_requests

log = logging.getLogger("openrouter.analytics")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    default_headers={"HTTP-Referer": "https://my-app.com", "X-Title": "my-app"},
)

def tracked_completion(messages, model="openai/gpt-4o-mini", user_id="system", **kwargs):
    """Make a completion and capture full analytics."""
    start = time.monotonic()
    response = client.chat.completions.create(
        model=model, messages=messages, **kwargs
    )
    latency = (time.monotonic() - start) * 1000

    # Fetch exact cost from generation endpoint
    cost = 0.0
    try:
        gen = http_requests.get(
            f"https://openrouter.ai/api/v1/generation?id={response.id}",
            headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"},
            timeout=5,
        ).json()
        cost = float(gen.get("data", {}).get("total_cost", 0))
    except Exception:
        pass

    metric = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "generation_id": response.id,
        "model_requested": model,
        "model_used": response.model,
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_cost": cost,
        "latency_ms": round(latency, 1),
        "user_id": user_id,
    }
    log.info(json.dumps(metric))
    return response, metric
```

## Analytics Database

```python
import sqlite3

def init_analytics_db(db_path: str = "openrouter_analytics.db"):
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            generation_id TEXT UNIQUE,
            model_requested TEXT,
            model_used TEXT,
            prompt_tokens INTEGER,
            completion_tokens INTEGER,
            total_cost REAL,
            latency_ms REAL,
            user_id TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_ts ON metrics(timestamp)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_model ON metrics(model_used)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_user ON metrics(user_id)")
    conn.commit()
    return conn

def store_metric(conn, metric: dict):
    conn.execute(
        """INSERT OR IGNORE INTO metrics
           (timestamp, generation_id, model_requested, model_used,
            prompt_tokens, completion_tokens, total_cost, latency_ms, user_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (metric["timestamp"], metric["generation_id"], metric["model_requested"],
         metric["model_used"], metric["prompt_tokens"], metric["completion_tokens"],
         metric["total_cost"], metric["latency_ms"], metric["user_id"]),
    )
    conn.commit()
```

## Analytics Queries

```sql
-- Daily cost summary
SELECT date(timestamp) as day,
       COUNT(*) as requests,
       SUM(prompt_tokens + completion_tokens) as total_tokens,
       ROUND(SUM(total_cost), 4) as total_cost,
       ROUND(AVG(latency_ms)) as avg_latency_ms
FROM metrics
WHERE timestamp > datetime('now', '-7 days')
GROUP BY day ORDER BY day DESC;

-- Cost by model (this week)
SELECT model_used,
       COUNT(*) as requests,
       ROUND(SUM(total_cost), 4) as cost,
       ROUND(AVG(latency_ms)) as avg_ms,
       SUM(prompt_tokens) as total_prompt,
       SUM(completion_tokens) as total_completion
FROM metrics
WHERE timestamp > datetime('now', '-7 days')
GROUP BY model_used ORDER BY cost DESC;

-- Top users by spend
SELECT user_id, COUNT(*) as requests,
       ROUND(SUM(total_cost), 4) as total_cost,
       ROUND(AVG(total_cost), 6) as avg_cost_per_request
FROM metrics
WHERE timestamp > datetime('now', '-30 days')
GROUP BY user_id ORDER BY total_cost DESC LIMIT 20;

-- Hourly request pattern (for capacity planning)
SELECT strftime('%H', timestamp) as hour,
       COUNT(*) as requests,
       ROUND(AVG(latency_ms)) as avg_latency
FROM metrics
WHERE timestamp > datetime('now', '-7 days')
GROUP BY hour ORDER BY hour;

-- Cost trend (daily, last 30 days)
SELECT date(timestamp) as day, ROUND(SUM(total_cost), 4) as cost
FROM metrics
WHERE timestamp > datetime('now', '-30 days')
GROUP BY day ORDER BY day;
```

## Credit Balance Monitoring

```bash
# Current credit status
curl -s https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" | jq '{
    credits_used: .data.usage,
    credit_limit: .data.limit,
    remaining: ((.data.limit // 0) - .data.usage),
    daily_burn_rate: "check analytics DB"
  }'
```

## Weekly Report Generator

```python
def weekly_report(conn) -> str:
    """Generate a text-based weekly analytics report."""
    summary = conn.execute("""
        SELECT COUNT(*) as requests,
               ROUND(SUM(total_cost), 2) as cost,
               ROUND(AVG(latency_ms)) as avg_latency,
               SUM(prompt_tokens + completion_tokens) as tokens
        FROM metrics WHERE timestamp > datetime('now', '-7 days')
    """).fetchone()

    top_models = conn.execute("""
        SELECT model_used, COUNT(*) as n, ROUND(SUM(total_cost), 4) as cost
        FROM metrics WHERE timestamp > datetime('now', '-7 days')
        GROUP BY model_used ORDER BY cost DESC LIMIT 5
    """).fetchall()

    report = f"""
=== OpenRouter Weekly Report ===
Period: Last 7 days
Requests: {summary[0]:,}
Total Cost: ${summary[1]:.2f}
Avg Latency: {summary[2]:.0f}ms
Total Tokens: {summary[3]:,}
Avg Cost/Request: ${summary[1]/max(summary[0],1):.4f}

Top Models by Cost:
"""
    for model, count, cost in top_models:
        report += f"  {model}: {count} requests, ${cost:.4f}\n"

    return report
```

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| Missing cost data | Generation endpoint fetch failed | Retry after 1-2s; log warning |
| Metric storage growing too fast | No aggregation or retention | Aggregate to hourly/daily; retain raw data 30 days |
| Stale dashboard | Query pipeline lagging | Add data freshness check; alert on >5 min staleness |
| Duplicate metrics | Retry caused duplicate generation_ids | Use `INSERT OR IGNORE` with generation_id unique constraint |

## Enterprise Considerations

- Query `/api/v1/generation?id=` after each request for exact cost (don't estimate from token counts)
- Aggregate raw metrics to hourly/daily summaries after 30 days to manage storage growth
- Build automated weekly reports with cost trends, top users, and anomaly detection
- Set alerts on daily cost exceeding 2x historical average (anomaly detection)
- Track `model_requested` vs `model_used` to monitor fallback frequency
- Use the hourly request pattern to capacity-plan API key rate limits

## References

- [Examples](${CLAUDE_SKILL_DIR}/references/examples.md) | [Errors](${CLAUDE_SKILL_DIR}/references/errors.md)
- [Generation API](https://openrouter.ai/docs/api/api-reference/generation-queries/query-a-generation) | [Auth API](https://openrouter.ai/docs/api/reference/authentication)
