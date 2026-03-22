---
name: klingai-usage-analytics
description: |
  Build usage analytics and reporting for Kling AI video generation. Use when tracking patterns,
  analyzing costs, or building dashboards. Trigger with phrases like 'klingai analytics',
  'kling ai usage report', 'klingai metrics', 'video generation stats'.
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, kling-ai, analytics, reporting]

---
# Kling AI Usage Analytics

## Overview

Track video generation usage with structured logging, aggregate metrics, daily reports, and cost analysis. Built on JSONL event logs that can feed into any analytics platform.

## Event Logger

```python
import json
import time
from datetime import datetime
from pathlib import Path

class KlingEventLogger:
    """Append-only JSONL event log for Kling AI operations."""

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

    def _write(self, event: dict):
        date = datetime.utcnow().strftime("%Y-%m-%d")
        filepath = self.log_dir / f"kling-{date}.jsonl"
        event["timestamp"] = datetime.utcnow().isoformat()
        with open(filepath, "a") as f:
            f.write(json.dumps(event) + "\n")

    def log_submission(self, task_id, prompt, model, duration, mode):
        self._write({
            "event": "task_submitted",
            "task_id": task_id,
            "model": model,
            "duration": int(duration),
            "mode": mode,
            "prompt_len": len(prompt),
        })

    def log_completion(self, task_id, status, elapsed_sec, credits_used):
        self._write({
            "event": "task_completed",
            "task_id": task_id,
            "status": status,
            "elapsed_sec": elapsed_sec,
            "credits_used": credits_used,
        })

    def log_error(self, task_id, error_type, message):
        self._write({
            "event": "task_error",
            "task_id": task_id,
            "error_type": error_type,
            "message": message[:200],
        })
```

## Analytics Aggregator

```python
from collections import defaultdict

class UsageAnalytics:
    """Aggregate metrics from JSONL event logs."""

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)

    def _read_events(self, date: str = None):
        pattern = f"kling-{date}.jsonl" if date else "kling-*.jsonl"
        events = []
        for filepath in sorted(self.log_dir.glob(pattern)):
            with open(filepath) as f:
                for line in f:
                    events.append(json.loads(line))
        return events

    def daily_summary(self, date: str = None) -> dict:
        date = date or datetime.utcnow().strftime("%Y-%m-%d")
        events = self._read_events(date)

        submitted = [e for e in events if e["event"] == "task_submitted"]
        completed = [e for e in events if e["event"] == "task_completed"]
        errors = [e for e in events if e["event"] == "task_error"]

        succeeded = [e for e in completed if e["status"] == "succeed"]
        failed = [e for e in completed if e["status"] == "failed"]

        total_credits = sum(e.get("credits_used", 0) for e in completed)
        avg_elapsed = (sum(e["elapsed_sec"] for e in succeeded) / len(succeeded)
                      if succeeded else 0)

        by_model = defaultdict(int)
        for e in submitted:
            by_model[e["model"]] += 1

        return {
            "date": date,
            "total_submitted": len(submitted),
            "succeeded": len(succeeded),
            "failed": len(failed),
            "errors": len(errors),
            "success_rate": f"{len(succeeded) / max(len(completed), 1) * 100:.1f}%",
            "total_credits": total_credits,
            "avg_generation_sec": round(avg_elapsed),
            "by_model": dict(by_model),
        }

    def print_report(self, date: str = None):
        s = self.daily_summary(date)
        print(f"\n=== Kling AI Usage Report: {s['date']} ===")
        print(f"Submitted:    {s['total_submitted']}")
        print(f"Succeeded:    {s['succeeded']}")
        print(f"Failed:       {s['failed']}")
        print(f"Success rate: {s['success_rate']}")
        print(f"Credits used: {s['total_credits']}")
        print(f"Avg time:     {s['avg_generation_sec']}s")
        print(f"By model:")
        for model, count in s["by_model"].items():
            print(f"  {model}: {count}")
```

## Cost Analysis

```python
def cost_analysis(analytics: UsageAnalytics, days: int = 7):
    """Analyze cost trends over recent days."""
    from datetime import timedelta

    daily_costs = []
    for i in range(days):
        date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
        summary = analytics.daily_summary(date)
        daily_costs.append({
            "date": date,
            "credits": summary["total_credits"],
            "videos": summary["total_submitted"],
            "estimated_usd": summary["total_credits"] * 0.14,
        })

    total_credits = sum(d["credits"] for d in daily_costs)
    total_videos = sum(d["videos"] for d in daily_costs)
    total_cost = sum(d["estimated_usd"] for d in daily_costs)

    print(f"\n=== {days}-Day Cost Summary ===")
    print(f"Total credits: {total_credits}")
    print(f"Total videos:  {total_videos}")
    print(f"Est. cost:     ${total_cost:.2f}")
    print(f"Avg/day:       ${total_cost / days:.2f}")

    for d in daily_costs:
        print(f"  {d['date']}: {d['credits']} credits, {d['videos']} videos, ${d['estimated_usd']:.2f}")
```

## Export to CSV

```python
import csv

def export_usage_csv(analytics: UsageAnalytics, output: str = "kling_usage.csv"):
    events = analytics._read_events()
    with open(output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "event", "task_id",
                                                "model", "status", "credits_used",
                                                "elapsed_sec"])
        writer.writeheader()
        for e in events:
            writer.writerow({k: e.get(k, "") for k in writer.fieldnames})
    print(f"Exported {len(events)} events to {output}")
```

## Resources

- [Developer Portal](https://app.klingai.com/global/dev)
- [Pricing Reference](https://app.klingai.com/global/dev/document-api/productBilling/prePaidResourcePackage)
