# Cost Optimization Strategies

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
