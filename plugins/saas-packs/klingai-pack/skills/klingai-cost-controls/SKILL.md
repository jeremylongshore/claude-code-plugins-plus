---
name: klingai-cost-controls
description: |
  Implement cost controls and budget management for Kling AI. Use when managing spending limits,
  tracking costs, or preventing budget overruns. Trigger with phrases like 'klingai cost',
  'kling ai budget', 'klingai spending', 'video generation costs'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Kling AI Cost Controls

## Overview

This skill teaches how to implement cost controls, budget tracking, usage alerts, and spending limits for Kling AI video generation to prevent unexpected charges.

## Prerequisites

- Kling AI API key configured
- Understanding of Kling AI pricing model
- Python 3.8+

## Instructions

Follow these steps for cost management:

1. **Understand Pricing**: Learn cost structure
2. **Set Budgets**: Define spending limits
3. **Track Usage**: Monitor consumption
4. **Create Alerts**: Set up notifications
5. **Enforce Limits**: Implement hard stops

## Pricing Structure

```
Kling AI Pricing (typical):

Credits per video:
- 5-second video: 10 credits
- 10-second video: 20 credits
- kling-pro model: 2x multiplier

Credit packages:
- 100 credits: $10 ($0.10/credit)
- 500 credits: $40 ($0.08/credit)
- 2000 credits: $120 ($0.06/credit)
- 10000 credits: $500 ($0.05/credit)

Cost calculation:
cost = base_credits × model_multiplier × resolution_multiplier

Example:
- 10-second kling-pro video at 1080p
- 20 × 2.0 × 1.0 = 40 credits
- At $0.06/credit = $2.40
```

## Cost Tracker Class

```python
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum
import json
import os

class BudgetPeriod(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

@dataclass
class UsageRecord:
    timestamp: datetime
    job_id: str
    credits_used: int
    cost_usd: float
    model: str
    duration: int
    user_id: Optional[str] = None
    project_id: Optional[str] = None

@dataclass
class Budget:
    period: BudgetPeriod
    limit_credits: int
    limit_usd: float
    alert_threshold: float = 0.8  # Alert at 80% usage

class CostTracker:
    """Track and control Kling AI costs."""

    # Credit rates by model
    MODEL_MULTIPLIERS = {
        "kling-v1": 1.0,
        "kling-v1.5": 1.0,
        "kling-pro": 2.0
    }

    # Base credits by duration
    DURATION_CREDITS = {
        5: 10,
        10: 20
    }

    # Credit cost (tiered)
    CREDIT_COSTS = [
        (100, 0.10),
        (500, 0.08),
        (2000, 0.06),
        (10000, 0.05)
    ]

    def __init__(self, storage_path: str = "cost_tracking.json"):
        self.storage_path = storage_path
        self.records: List[UsageRecord] = []
        self.budgets: Dict[str, Budget] = {}
        self.load()

    def load(self):
        """Load tracking data from file."""
        if os.path.exists(self.storage_path):
            with open(self.storage_path) as f:
                data = json.load(f)
                self.records = [
                    UsageRecord(
                        timestamp=datetime.fromisoformat(r["timestamp"]),
                        **{k: v for k, v in r.items() if k != "timestamp"}
                    )
                    for r in data.get("records", [])
                ]
                self.budgets = {
                    k: Budget(
                        period=BudgetPeriod(v["period"]),
                        limit_credits=v["limit_credits"],
                        limit_usd=v["limit_usd"],
                        alert_threshold=v.get("alert_threshold", 0.8)
                    )
                    for k, v in data.get("budgets", {}).items()
                }

    def save(self):
        """Save tracking data to file."""
        with open(self.storage_path, "w") as f:
            json.dump({
                "records": [
                    {
                        "timestamp": r.timestamp.isoformat(),
                        "job_id": r.job_id,
                        "credits_used": r.credits_used,
                        "cost_usd": r.cost_usd,
                        "model": r.model,
                        "duration": r.duration,
                        "user_id": r.user_id,
                        "project_id": r.project_id
                    }
                    for r in self.records
                ],
                "budgets": {
                    k: {
                        "period": v.period.value,
                        "limit_credits": v.limit_credits,
                        "limit_usd": v.limit_usd,
                        "alert_threshold": v.alert_threshold
                    }
                    for k, v in self.budgets.items()
                }
            }, f, indent=2)

    def calculate_credits(self, duration: int, model: str) -> int:
        """Calculate credits for a video generation."""
        base = self.DURATION_CREDITS.get(duration, duration * 2)
        multiplier = self.MODEL_MULTIPLIERS.get(model, 1.0)
        return int(base * multiplier)

    def calculate_cost(self, credits: int, tier_credits: int = 2000) -> float:
        """Calculate USD cost for credits."""
        # Find applicable rate based on tier
        rate = 0.10  # Default rate
        for threshold, r in self.CREDIT_COSTS:
            if tier_credits >= threshold:
                rate = r
        return credits * rate

    def record_usage(
        self,
        job_id: str,
        duration: int,
        model: str,
        user_id: str = None,
        project_id: str = None
    ) -> UsageRecord:
        """Record a video generation usage."""
        credits = self.calculate_credits(duration, model)
        cost = self.calculate_cost(credits)

        record = UsageRecord(
            timestamp=datetime.utcnow(),
            job_id=job_id,
            credits_used=credits,
            cost_usd=cost,
            model=model,
            duration=duration,
            user_id=user_id,
            project_id=project_id
        )

        self.records.append(record)
        self.save()

        # Check budget alerts
        self._check_alerts(project_id or "default")

        return record

    def set_budget(self, key: str, budget: Budget):
        """Set a budget limit."""
        self.budgets[key] = budget
        self.save()
        print(f"Budget set for {key}: {budget.limit_credits} credits / {budget.period.value}")

    def get_usage(
        self,
        period: BudgetPeriod,
        key: str = None,
        key_type: str = "project"
    ) -> Dict:
        """Get usage for a period."""
        now = datetime.utcnow()

        # Calculate period start
        if period == BudgetPeriod.DAILY:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == BudgetPeriod.WEEKLY:
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        else:  # Monthly
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Filter records
        filtered = [r for r in self.records if r.timestamp >= start]

        if key:
            if key_type == "project":
                filtered = [r for r in filtered if r.project_id == key]
            elif key_type == "user":
                filtered = [r for r in filtered if r.user_id == key]

        total_credits = sum(r.credits_used for r in filtered)
        total_cost = sum(r.cost_usd for r in filtered)

        return {
            "period": period.value,
            "start": start.isoformat(),
            "end": now.isoformat(),
            "total_credits": total_credits,
            "total_cost_usd": round(total_cost, 2),
            "record_count": len(filtered)
        }

    def check_budget(self, key: str) -> Dict:
        """Check budget status."""
        budget = self.budgets.get(key)
        if not budget:
            return {"has_budget": False}

        usage = self.get_usage(budget.period, key)

        credits_pct = usage["total_credits"] / budget.limit_credits
        cost_pct = usage["total_cost_usd"] / budget.limit_usd

        return {
            "has_budget": True,
            "budget": {
                "period": budget.period.value,
                "limit_credits": budget.limit_credits,
                "limit_usd": budget.limit_usd
            },
            "usage": usage,
            "credits_remaining": budget.limit_credits - usage["total_credits"],
            "usd_remaining": round(budget.limit_usd - usage["total_cost_usd"], 2),
            "credits_percent": round(credits_pct * 100, 1),
            "cost_percent": round(cost_pct * 100, 1),
            "over_budget": credits_pct >= 1 or cost_pct >= 1,
            "alert_triggered": credits_pct >= budget.alert_threshold
        }

    def can_generate(self, key: str, duration: int, model: str) -> Dict:
        """Check if generation is allowed under budget."""
        budget_status = self.check_budget(key)

        if not budget_status["has_budget"]:
            return {"allowed": True, "reason": "No budget set"}

        credits_needed = self.calculate_credits(duration, model)
        cost_needed = self.calculate_cost(credits_needed)

        credits_ok = budget_status["credits_remaining"] >= credits_needed
        cost_ok = budget_status["usd_remaining"] >= cost_needed

        return {
            "allowed": credits_ok and cost_ok,
            "credits_needed": credits_needed,
            "credits_remaining": budget_status["credits_remaining"],
            "cost_needed": cost_needed,
            "cost_remaining": budget_status["usd_remaining"],
            "reason": None if (credits_ok and cost_ok) else "Budget exceeded"
        }

    def _check_alerts(self, key: str):
        """Check and trigger budget alerts."""
        status = self.check_budget(key)

        if status.get("has_budget"):
            if status["over_budget"]:
                print(f"ALERT: Budget exceeded for {key}!")
                # In production: send email, Slack, etc.
            elif status["alert_triggered"]:
                print(f"WARNING: Budget threshold reached for {key} ({status['credits_percent']}%)")

# Usage
tracker = CostTracker()

# Set monthly budget
tracker.set_budget("marketing", Budget(
    period=BudgetPeriod.MONTHLY,
    limit_credits=10000,
    limit_usd=600.00,
    alert_threshold=0.8
))

# Check before generating
check = tracker.can_generate("marketing", duration=10, model="kling-pro")
if check["allowed"]:
    # Generate video
    tracker.record_usage(
        job_id="vid_abc123",
        duration=10,
        model="kling-pro",
        project_id="marketing"
    )
else:
    print(f"Generation blocked: {check['reason']}")

# View usage
print(tracker.get_usage(BudgetPeriod.MONTHLY, "marketing"))
print(tracker.check_budget("marketing"))
```

## Budget Enforcing Wrapper

```python
class BudgetEnforcedClient:
    """Kling AI client with budget enforcement."""

    def __init__(self, api_key: str, tracker: CostTracker, project_id: str):
        self.api_key = api_key
        self.tracker = tracker
        self.project_id = project_id
        self.base_url = "https://api.klingai.com/v1"

    def generate_video(self, prompt: str, duration: int = 5, model: str = "kling-v1.5") -> dict:
        """Generate video with budget check."""
        # Pre-flight budget check
        check = self.tracker.can_generate(self.project_id, duration, model)

        if not check["allowed"]:
            raise BudgetExceededError(
                f"Budget exceeded for {self.project_id}. "
                f"Need {check['credits_needed']} credits, "
                f"have {check['credits_remaining']}"
            )

        # Make API request
        response = requests.post(
            f"{self.base_url}/videos/text-to-video",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "prompt": prompt,
                "duration": duration,
                "model": model
            }
        )
        response.raise_for_status()
        result = response.json()

        # Record usage
        self.tracker.record_usage(
            job_id=result["job_id"],
            duration=duration,
            model=model,
            project_id=self.project_id
        )

        return result

class BudgetExceededError(Exception):
    """Raised when budget is exceeded."""
    pass
```

## Output

Successful execution produces:
- Cost tracking records
- Budget limit enforcement
- Usage alerts at thresholds
- Prevented budget overruns

## Error Handling

Common errors and solutions:
1. **Budget Exceeded**: Wait for period reset or increase budget
2. **Missing Records**: Ensure all API calls go through tracker
3. **Incorrect Rates**: Verify pricing tier matches account

## Examples

See code examples above for complete, runnable implementations.

## Resources

- [Kling AI Pricing](https://klingai.com/pricing)
- [Usage Dashboard](https://console.klingai.com/usage)
- [Billing Documentation](https://docs.klingai.com/billing)
