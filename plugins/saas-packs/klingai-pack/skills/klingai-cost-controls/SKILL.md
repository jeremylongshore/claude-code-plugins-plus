---
name: klingai-cost-controls
description: |
  Implement budget limits, usage alerts, and spending controls for Kling AI. Use when managing
  costs or preventing overruns. Trigger with phrases like 'klingai cost', 'kling ai budget',
  'klingai spending limit', 'video generation costs'.
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, kling-ai, cost-controls, budget]

---
# Kling AI Cost Controls

## Overview

Prevent unexpected spending with per-request cost estimation, daily budget enforcement, threshold alerts, and usage dashboards. Credits are consumed per task based on duration, mode, and audio.

## Credit Cost Reference

| Config | Credits |
|--------|---------|
| 5s standard | 10 |
| 5s professional | 35 |
| 10s standard | 20 |
| 10s professional | 70 |
| 5s standard + audio (v2.6) | 50 |
| 10s professional + audio (v2.6) | 200 |
| Image generation (Kolors) | 1 |
| Virtual try-on | 5 |

## Budget Guard

```python
import time
from dataclasses import dataclass, field

@dataclass
class BudgetGuard:
    """Enforce daily credit budget with alerting."""
    daily_limit: int = 1000
    alert_threshold: float = 0.8  # alert at 80%
    _used: int = 0
    _reset_time: float = field(default_factory=time.time)
    _alerts_sent: set = field(default_factory=set)

    def _check_reset(self):
        if time.time() - self._reset_time > 86400:
            self._used = 0
            self._reset_time = time.time()
            self._alerts_sent.clear()

    def estimate_credits(self, duration: int = 5, mode: str = "standard",
                         audio: bool = False) -> int:
        base = {(5, "standard"): 10, (5, "professional"): 35,
                (10, "standard"): 20, (10, "professional"): 70}
        credits = base.get((duration, mode), 10)
        if audio:
            credits *= 5
        return credits

    def check(self, credits_needed: int) -> bool:
        self._check_reset()

        # Check alert threshold
        usage_pct = (self._used + credits_needed) / self.daily_limit
        if usage_pct >= self.alert_threshold and "80pct" not in self._alerts_sent:
            self._alerts_sent.add("80pct")
            self._on_alert(f"Budget at {usage_pct:.0%} ({self._used + credits_needed}/{self.daily_limit})")

        if self._used + credits_needed > self.daily_limit:
            raise RuntimeError(
                f"Daily budget exceeded: {self._used} + {credits_needed} > {self.daily_limit} credits"
            )
        return True

    def record(self, credits: int):
        self._used += credits

    def _on_alert(self, message: str):
        """Override for custom alerting (Slack, email, PagerDuty)."""
        print(f"ALERT: {message}")

    @property
    def remaining(self) -> int:
        self._check_reset()
        return max(0, self.daily_limit - self._used)

    @property
    def usage_report(self) -> dict:
        self._check_reset()
        return {
            "used": self._used,
            "limit": self.daily_limit,
            "remaining": self.remaining,
            "usage_pct": f"{(self._used / self.daily_limit) * 100:.1f}%",
        }
```

## Pre-Batch Cost Check

```python
def pre_batch_check(prompts: list, budget: BudgetGuard,
                    duration: int = 5, mode: str = "standard"):
    """Estimate and validate batch cost before submission."""
    per_video = budget.estimate_credits(duration, mode)
    total = len(prompts) * per_video

    print(f"Batch estimate: {len(prompts)} videos x {per_video} credits = {total} credits")
    print(f"Budget remaining: {budget.remaining}")

    if total > budget.remaining:
        raise RuntimeError(
            f"Batch needs {total} credits but only {budget.remaining} remaining. "
            f"Reduce to {budget.remaining // per_video} videos or lower mode."
        )
    return total
```

## Cost-Aware Client

```python
class CostAwareKlingClient:
    """Kling client that enforces budget on every request."""

    def __init__(self, base_client, budget: BudgetGuard):
        self.client = base_client
        self.budget = budget

    def text_to_video(self, prompt: str, **kwargs):
        credits = self.budget.estimate_credits(
            kwargs.get("duration", 5),
            kwargs.get("mode", "standard"),
            kwargs.get("audio", False),
        )
        self.budget.check(credits)

        result = self.client.text_to_video(prompt, **kwargs)
        self.budget.record(credits)
        return result
```

## Optimization Strategies

| Strategy | Savings | Implementation |
|----------|---------|---------------|
| Standard for drafts | 3.5x cheaper | `mode: "standard"` for iterations |
| 5s clips, extend later | 50% per clip | Generate 5s, use `video-extend` selectively |
| v2.5 Turbo over v2.6 | Faster (less queue cost) | `model: "kling-v2-5-turbo"` |
| Skip audio, add in post | 5x cheaper | `motion_has_audio: false` |
| Batch off-peak | Faster processing | Schedule overnight |
| Cache prompts | Avoid duplicates | Hash prompt + params, check before submitting |

## Usage Tracking

```python
import json
from datetime import datetime

class UsageTracker:
    """Log every generation for cost analysis."""

    def __init__(self, log_file: str = "kling_usage.jsonl"):
        self.log_file = log_file

    def log(self, task_id: str, credits: int, model: str,
            duration: int, mode: str, prompt: str):
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "task_id": task_id,
            "credits": credits,
            "model": model,
            "duration": duration,
            "mode": mode,
            "prompt_preview": prompt[:100],
        }
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
```

## Resources

- [Pricing](https://app.klingai.com/global/dev/document-api/productBilling/prePaidResourcePackage)
- [Developer Portal](https://app.klingai.com/global/dev)
