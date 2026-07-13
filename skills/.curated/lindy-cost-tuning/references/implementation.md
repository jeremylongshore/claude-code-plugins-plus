# Lindy Cost Tuning -- Implementation Details

## Understanding Cost Drivers

Lindy charges are based on agent runs, AI model token usage, and integration calls.

## Advanced Patterns

### Monitor Run Frequency

```python
import os
import requests
from datetime import datetime, timedelta, timezone
from collections import defaultdict

LINDY_API_BASE = "https://api.lindy.ai/v1"
HEADERS = {"Authorization": f"Bearer {os.environ['LINDY_API_KEY']}"}

def get_run_history(agent_id: str, days: int = 7) -> list[dict]:
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    resp = requests.get(
        f"{LINDY_API_BASE}/agents/{agent_id}/runs",
        headers=HEADERS,
        params={"since": since, "limit": 500},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("runs", [])


def analyze_run_frequency(agent_id: str) -> dict:
    runs = get_run_history(agent_id, days=7)
    by_hour = defaultdict(int)
    by_day = defaultdict(int)

    for run in runs:
        ts = datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))
        by_hour[ts.hour] += 1
        by_day[ts.strftime("%A")] += 1

    return {
        "total_runs_7d": len(runs),
        "daily_average": round(len(runs) / 7, 1),
        "peak_hour": max(by_hour, key=by_hour.get) if by_hour else None,
        "peak_day": max(by_day, key=by_day.get) if by_day else None,
    }
```

### Deduplication to Reduce Redundant Runs

```python
import hashlib
import json
import time
import requests
import os

_dedup_cache: dict[str, float] = {}
DEDUP_WINDOW_SECONDS = 300
LINDY_API_BASE = "https://api.lindy.ai/v1"
HEADERS = {"Authorization": f"Bearer {os.environ['LINDY_API_KEY']}"}

def deduplicated_trigger(agent_id: str, inputs: dict) -> dict | None:
    key = f"{agent_id}:{hashlib.md5(json.dumps(inputs, sort_keys=True).encode()).hexdigest()[:16]}"
    now = time.time()
    if key in _dedup_cache and now - _dedup_cache[key] < DEDUP_WINDOW_SECONDS:
        print(f"[DEDUP] Skipped duplicate trigger ({now - _dedup_cache[key]:.0f}s ago)")
        return None
    _dedup_cache[key] = now
    resp = requests.post(
        f"{LINDY_API_BASE}/agents/{agent_id}/runs",
        headers={**HEADERS, "Content-Type": "application/json"},
        json={"inputs": inputs},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()
```

### Optimize AI Step Prompts

Keep system prompts concise to reduce token consumption per run:

```python
# Before: verbose (~400 tokens per run)
VERBOSE_SYSTEM = """You are a helpful AI assistant that specializes in analyzing
customer support tickets. Your role is to carefully read each support ticket...
[continues for 300 more tokens]"""

# After: concise (~60 tokens)
CONCISE_SYSTEM = """Classify support tickets. Output JSON:
{"category": "billing|technical|general", "urgency": "low|medium|high", "summary": "1-2 sentences"}"""

# Savings: 340 tokens per run -> at 10,000 runs/month: 3.4M tokens saved
```

## Troubleshooting

### Run Count Higher Than Expected

1. Check if multiple triggers fire for the same event
2. Look for infinite loops: agents triggering other agents that trigger back
3. Review trigger conditions for unnecessary breadth
4. Set daily run limits in agent settings

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
