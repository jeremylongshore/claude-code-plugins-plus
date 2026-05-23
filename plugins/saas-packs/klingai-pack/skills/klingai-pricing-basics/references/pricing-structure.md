# Pricing Structure

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
