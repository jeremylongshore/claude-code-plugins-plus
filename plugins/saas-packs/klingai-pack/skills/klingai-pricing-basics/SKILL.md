---
name: klingai-pricing-basics
description: |
  Understand Kling AI pricing, credits, and cost optimization. Use when budgeting or optimizing
  costs for video generation. Trigger with phrases like 'kling ai pricing', 'klingai credits',
  'kling ai cost', 'klingai budget'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Kling AI Pricing Basics

## Overview

This skill explains the Kling AI pricing model, credit system, cost estimation techniques, and strategies for optimizing your video generation costs.

## Prerequisites

- Kling AI account
- Understanding of your video generation needs
- Budget parameters defined

## Instructions

Follow these steps to understand and optimize costs:

1. **Understand Credit System**: Learn how credits work
2. **Calculate Costs**: Estimate costs for your projects
3. **Select Optimal Model**: Choose cost-effective models
4. **Monitor Usage**: Track spending in real-time
5. **Optimize Workflow**: Reduce costs without sacrificing quality

## Pricing Structure

### Credit-Based Pricing
```
Kling AI uses a credit system where:
- Credits are purchased in advance
- Each generation consumes credits based on:
  - Model tier (Standard, Enhanced, Pro)
  - Video duration
  - Resolution
  - Special features used

Base rates (approximate):
- Kling 1.0 (Standard): ~5 credits/second
- Kling 1.5 (Enhanced): ~10 credits/second
- Kling Pro: ~20 credits/second

Credit packages:
- 100 credits: $5 (~20 seconds standard video)
- 500 credits: $20 (10% bonus)
- 1000 credits: $35 (15% bonus)
- 5000 credits: $150 (20% bonus)
```

### Cost Calculator

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class PricingTier:
    name: str
    credits_per_second: int
    max_duration: int
    max_resolution: str

PRICING_TIERS = {
    "kling-v1": PricingTier("Standard", 5, 10, "1080p"),
    "kling-v1.5": PricingTier("Enhanced", 10, 30, "4k"),
    "kling-pro": PricingTier("Pro", 20, 60, "4k")
}

RESOLUTION_MULTIPLIERS = {
    "720p": 0.8,
    "1080p": 1.0,
    "4k": 1.5
}

def calculate_credits(
    model: str,
    duration: int,
    resolution: str = "1080p"
) -> int:
    """Calculate credits needed for video generation."""
    tier = PRICING_TIERS[model]
    base_credits = tier.credits_per_second * duration
    resolution_multiplier = RESOLUTION_MULTIPLIERS.get(resolution, 1.0)
    return int(base_credits * resolution_multiplier)

def calculate_cost(
    credits: int,
    credit_price: float = 0.05  # $0.05 per credit
) -> float:
    """Calculate dollar cost from credits."""
    return credits * credit_price

# Usage
credits = calculate_credits("kling-v1.5", duration=10, resolution="1080p")
cost = calculate_cost(credits)
print(f"Credits needed: {credits}")
print(f"Estimated cost: ${cost:.2f}")
```

## Budget Management

```python
class BudgetManager:
    """Track and manage video generation budget."""

    def __init__(self, monthly_budget: float):
        self.monthly_budget = monthly_budget
        self.spent = 0.0
        self.generations = []

    def can_afford(self, estimated_cost: float) -> bool:
        """Check if generation is within budget."""
        return (self.spent + estimated_cost) <= self.monthly_budget

    def record_generation(self, cost: float, metadata: dict):
        """Record a generation and its cost."""
        self.spent += cost
        self.generations.append({
            "cost": cost,
            "remaining": self.monthly_budget - self.spent,
            **metadata
        })

    def get_remaining(self) -> float:
        """Get remaining budget."""
        return self.monthly_budget - self.spent

    def get_usage_report(self) -> dict:
        """Generate usage report."""
        return {
            "budget": self.monthly_budget,
            "spent": self.spent,
            "remaining": self.get_remaining(),
            "utilization": (self.spent / self.monthly_budget) * 100,
            "generations": len(self.generations)
        }

# Usage
budget = BudgetManager(monthly_budget=100.0)

if budget.can_afford(5.0):
    # Generate video
    budget.record_generation(5.0, {"prompt": "...", "duration": 10})

print(budget.get_usage_report())
```

## Cost Optimization Strategies

### 1. Model Selection
```python
def select_cost_effective_model(
    required_quality: str,
    duration: int,
    budget: float
) -> str:
    """Select the most cost-effective model for requirements."""

    # Calculate costs for each model
    options = []
    for model, tier in PRICING_TIERS.items():
        if duration <= tier.max_duration:
            credits = calculate_credits(model, duration)
            cost = calculate_cost(credits)
            if cost <= budget:
                options.append({
                    "model": model,
                    "cost": cost,
                    "quality": tier.name
                })

    # Sort by cost (cheapest first)
    options.sort(key=lambda x: x["cost"])

    # Return cheapest that meets quality requirement
    quality_rank = {"Standard": 1, "Enhanced": 2, "Pro": 3}
    required_rank = quality_rank.get(required_quality, 1)

    for opt in options:
        if quality_rank[opt["quality"]] >= required_rank:
            return opt["model"]

    return options[0]["model"] if options else "kling-v1"
```

### 2. Duration Optimization
```python
def optimize_duration(content_type: str) -> int:
    """Get optimal duration for content type."""

    OPTIMAL_DURATIONS = {
        "social_media_clip": 5,
        "product_showcase": 10,
        "story_segment": 15,
        "full_scene": 30,
        "extended_content": 60
    }

    return OPTIMAL_DURATIONS.get(content_type, 10)

# Avoid paying for unused duration
# - TikTok/Reels: 5-15 seconds is optimal
# - Product videos: 10-15 seconds
# - Longer content: Generate in segments
```

### 3. Resolution Strategy
```python
def select_resolution(target_platform: str) -> str:
    """Select appropriate resolution for platform."""

    # Don't pay for 4K if platform compresses anyway
    PLATFORM_RESOLUTIONS = {
        "tiktok": "1080p",      # 1080p is max
        "instagram": "1080p",   # 1080p compressed
        "youtube": "4k",        # Supports 4K
        "twitter": "720p",      # Heavy compression
        "presentation": "1080p",
        "broadcast": "4k"
    }

    return PLATFORM_RESOLUTIONS.get(target_platform, "1080p")
```

### 4. Batch Planning
```python
def plan_batch_generation(
    videos: list[dict],
    budget: float
) -> list[dict]:
    """Plan batch generation within budget."""

    planned = []
    remaining_budget = budget

    # Sort by priority
    videos.sort(key=lambda v: v.get("priority", 0), reverse=True)

    for video in videos:
        credits = calculate_credits(
            video.get("model", "kling-v1"),
            video["duration"]
        )
        cost = calculate_cost(credits)

        if cost <= remaining_budget:
            planned.append({**video, "estimated_cost": cost})
            remaining_budget -= cost

    return planned
```

## Monitoring Usage

```python
import requests
import os

def get_account_usage() -> dict:
    """Get current account usage and balance."""
    response = requests.get(
        "https://api.klingai.com/v1/account",
        headers={"Authorization": f"Bearer {os.environ['KLINGAI_API_KEY']}"}
    )
    return response.json()

def get_usage_history(days: int = 30) -> list:
    """Get generation history for cost analysis."""
    response = requests.get(
        f"https://api.klingai.com/v1/account/usage?days={days}",
        headers={"Authorization": f"Bearer {os.environ['KLINGAI_API_KEY']}"}
    )
    return response.json()["generations"]

# Generate usage report
usage = get_account_usage()
print(f"Credits remaining: {usage['credits']}")
print(f"Credits used this month: {usage['monthly_usage']}")
```

## Cost Alerts

```python
def check_budget_alerts(
    current_usage: float,
    budget: float,
    thresholds: list[float] = [0.5, 0.75, 0.9]
) -> list[str]:
    """Generate budget alerts."""

    alerts = []
    utilization = current_usage / budget

    for threshold in thresholds:
        if utilization >= threshold:
            alerts.append(
                f"Budget alert: {utilization*100:.0f}% of ${budget} budget used"
            )

    return alerts
```

## Output

Successful execution produces:
- Cost estimates for video generation
- Budget tracking and reporting
- Optimization recommendations

## Error Handling

Common errors and solutions:
1. **Insufficient Credits**: Purchase more credits or reduce scope
2. **Budget Exceeded**: Review and adjust generation parameters
3. **Unexpected Costs**: Check for resolution/feature multipliers

## Examples

See code examples above for complete, runnable implementations.

## Resources

- [Kling AI Pricing](https://klingai.com/pricing)
- [Credit Packages](https://klingai.com/credits)
- [Usage Dashboard](https://klingai.com/dashboard/usage)
