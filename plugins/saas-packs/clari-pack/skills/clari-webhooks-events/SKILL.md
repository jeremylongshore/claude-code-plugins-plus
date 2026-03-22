---
name: clari-webhooks-events
description: |
  Monitor Clari forecast changes using export job polling and change detection.
  Use when tracking forecast submission changes, building alerts
  for significant forecast movements, or syncing Clari data in near-real-time.
  Trigger with phrases like "clari webhooks", "clari notifications",
  "clari forecast alerts", "clari change detection".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(python3:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, revenue-intelligence, forecasting, clari]
compatible-with: claude-code
---

# Clari Webhooks & Events

## Overview

Clari does not provide real-time webhooks. Instead, build change detection by comparing periodic exports. This skill covers scheduled export diffing, Slack alerts for forecast movements, and Copilot webhook integration.

## Instructions

### Step 1: Forecast Change Detection Pipeline

```python
# forecast_monitor.py
import json
from pathlib import Path
from datetime import datetime

def detect_changes(
    current: list[dict],
    previous: list[dict],
    threshold_pct: float = 10.0,
) -> list[dict]:
    prev_map = {e["ownerEmail"]: e for e in previous}
    changes = []

    for entry in current:
        prev = prev_map.get(entry["ownerEmail"])
        if not prev:
            continue

        prev_fc = prev["forecastAmount"]
        curr_fc = entry["forecastAmount"]
        if prev_fc == 0:
            continue

        change_pct = ((curr_fc - prev_fc) / prev_fc) * 100
        if abs(change_pct) >= threshold_pct:
            changes.append({
                "rep": entry["ownerName"],
                "previous": prev_fc,
                "current": curr_fc,
                "change_pct": round(change_pct, 1),
                "direction": "increased" if change_pct > 0 else "decreased",
                "detected_at": datetime.utcnow().isoformat(),
            })

    return sorted(changes, key=lambda x: abs(x["change_pct"]), reverse=True)

def save_snapshot(entries: list[dict], path: str = "data/latest.json"):
    Path(path).parent.mkdir(exist_ok=True)
    with open(path, "w") as f:
        json.dump(entries, f)

def load_snapshot(path: str = "data/latest.json") -> list[dict]:
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return []
```

### Step 2: Slack Alert for Forecast Changes

```python
import requests

def send_forecast_alert(changes: list[dict], slack_webhook: str):
    if not changes:
        return

    blocks = [f"*Clari Forecast Changes Detected*\n"]
    for c in changes[:10]:
        emoji = ":chart_with_upwards_trend:" if c["direction"] == "increased" else ":chart_with_downwards_trend:"
        blocks.append(
            f"{emoji} *{c['rep']}*: ${c['previous']:,.0f} -> ${c['current']:,.0f} "
            f"({c['change_pct']:+.1f}%)"
        )

    requests.post(slack_webhook, json={"text": "\n".join(blocks)})
```

### Step 3: Scheduled Monitor (Cron)

```bash
#!/bin/bash
# Run every 4 hours: 0 */4 * * * /path/to/clari-monitor.sh
cd /opt/clari-integration
python3 -c "
from clari_client import ClariClient
from forecast_monitor import detect_changes, save_snapshot, load_snapshot, send_forecast_alert
import os

client = ClariClient()
data = client.export_and_download('company_forecast', '2026_Q1')
current = data.get('entries', [])
previous = load_snapshot()

changes = detect_changes(current, previous)
if changes:
    send_forecast_alert(changes, os.environ['SLACK_WEBHOOK_URL'])
    print(f'Detected {len(changes)} changes')

save_snapshot(current)
"
```

### Step 4: Copilot Webhook (Conversation Intelligence)

The Clari Copilot API supports real-time webhooks for call events:

```bash
# Register webhook with Copilot API
curl -X POST https://api.copilot.clari.com/v1/webhooks \
  -H "Authorization: Bearer ${COPILOT_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app.com/webhooks/clari-copilot",
    "events": ["call.completed", "call.analyzed"]
  }'
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| False change alerts | Data timing differences | Increase threshold to 15% |
| Snapshot file missing | First run | Initialize with empty list |
| Slack post fails | Bad webhook URL | Test URL with `curl` |

## Resources

- [Clari Copilot API](https://api-doc.copilot.clari.com)
- [Clari Developer Portal](https://developer.clari.com)

## Next Steps

For performance optimization, see `clari-performance-tuning`.
