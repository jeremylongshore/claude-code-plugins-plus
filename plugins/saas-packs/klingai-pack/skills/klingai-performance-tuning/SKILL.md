---
name: klingai-performance-tuning
description: |
  Optimize Kling AI performance for speed and quality. Use when improving generation times,
  reducing costs, or enhancing output quality. Trigger with phrases like 'klingai performance',
  'kling ai optimization', 'faster klingai', 'klingai quality settings'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Kling AI Performance Tuning

## Overview

This skill demonstrates optimizing Kling AI for better performance including faster generation, improved quality, cost optimization, and efficient resource usage.

## Prerequisites

- Kling AI API key configured
- Understanding of performance tradeoffs
- Python 3.8+

## Instructions

Follow these steps for performance tuning:

1. **Benchmark Baseline**: Measure current performance
2. **Identify Bottlenecks**: Find slow areas
3. **Apply Optimizations**: Implement improvements
4. **Measure Results**: Compare before/after
5. **Balance Tradeoffs**: Find optimal settings

## Performance Factors

```
Kling AI Performance Factors:

GENERATION SPEED:
- Model selection (kling-v1 faster, kling-pro slower)
- Duration (5s faster than 10s)
- Resolution (lower = faster)
- Queue position (varies)

QUALITY:
- Model selection (kling-pro highest quality)
- Duration (longer = more coherent)
- Prompt clarity (specific = better)
- Resolution (higher = more detail)

COST:
- Model (kling-v1 cheapest, kling-pro expensive)
- Duration (linear cost increase)
- Retries (failed jobs still cost)
- Resolution multiplier

TRADEOFF PROFILES:
- Speed: kling-v1, 5s, 720p
- Quality: kling-pro, 10s, 1080p
- Balanced: kling-v1.5, 5s, 1080p
- Budget: kling-v1, 5s, 720p
```

## Performance Profiler

```python
import time
import statistics
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
import requests
import os

@dataclass
class PerformanceMetric:
    job_id: str
    model: str
    duration: int
    resolution: str
    submit_time: float
    complete_time: Optional[float] = None
    total_time: Optional[float] = None
    status: str = "pending"
    credits_used: int = 0

@dataclass
class PerformanceProfile:
    name: str
    metrics: List[PerformanceMetric] = field(default_factory=list)

    def add_metric(self, metric: PerformanceMetric):
        self.metrics.append(metric)

    def get_stats(self) -> Dict:
        completed = [m for m in self.metrics if m.total_time is not None]
        if not completed:
            return {"no_data": True}

        times = [m.total_time for m in completed]
        credits = [m.credits_used for m in completed]

        return {
            "count": len(completed),
            "avg_time": statistics.mean(times),
            "min_time": min(times),
            "max_time": max(times),
            "std_dev": statistics.stdev(times) if len(times) > 1 else 0,
            "p50_time": statistics.median(times),
            "p95_time": sorted(times)[int(len(times) * 0.95)] if len(times) > 1 else times[0],
            "total_credits": sum(credits),
            "avg_credits": statistics.mean(credits),
            "success_rate": len(completed) / len(self.metrics) * 100
        }

class KlingAIPerformanceProfiler:
    """Profile and optimize Kling AI performance."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ["KLINGAI_API_KEY"]
        self.base_url = "https://api.klingai.com/v1"
        self.profiles: Dict[str, PerformanceProfile] = {}

    def create_profile(self, name: str) -> PerformanceProfile:
        """Create a new performance profile."""
        profile = PerformanceProfile(name=name)
        self.profiles[name] = profile
        return profile

    def benchmark(
        self,
        profile_name: str,
        prompt: str,
        model: str = "kling-v1.5",
        duration: int = 5,
        resolution: str = "1080p",
        iterations: int = 3
    ) -> Dict:
        """Run benchmark tests."""
        if profile_name not in self.profiles:
            self.create_profile(profile_name)

        profile = self.profiles[profile_name]
        results = []

        for i in range(iterations):
            print(f"Benchmark iteration {i+1}/{iterations}...")

            metric = self._run_single_benchmark(prompt, model, duration, resolution)
            profile.add_metric(metric)
            results.append(metric)

            # Small delay between tests
            time.sleep(2)

        return {
            "profile": profile_name,
            "iterations": iterations,
            "config": {
                "model": model,
                "duration": duration,
                "resolution": resolution
            },
            "stats": profile.get_stats()
        }

    def _run_single_benchmark(
        self,
        prompt: str,
        model: str,
        duration: int,
        resolution: str
    ) -> PerformanceMetric:
        """Run a single benchmark iteration."""
        submit_time = time.time()

        # Submit job
        response = requests.post(
            f"{self.base_url}/videos/text-to-video",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "prompt": prompt,
                "duration": duration,
                "model": model,
                "resolution": resolution
            }
        )

        if response.status_code != 200:
            return PerformanceMetric(
                job_id="failed",
                model=model,
                duration=duration,
                resolution=resolution,
                submit_time=submit_time,
                status="failed"
            )

        job_id = response.json()["job_id"]

        metric = PerformanceMetric(
            job_id=job_id,
            model=model,
            duration=duration,
            resolution=resolution,
            submit_time=submit_time
        )

        # Poll until complete
        while True:
            status_response = requests.get(
                f"{self.base_url}/videos/{job_id}",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            status_data = status_response.json()

            if status_data["status"] == "completed":
                metric.complete_time = time.time()
                metric.total_time = metric.complete_time - metric.submit_time
                metric.status = "completed"
                metric.credits_used = status_data.get("credits_used", duration * 2)
                break
            elif status_data["status"] == "failed":
                metric.status = "failed"
                break

            time.sleep(5)

        return metric

    def compare_configs(
        self,
        prompt: str,
        configs: List[Dict],
        iterations: int = 2
    ) -> Dict:
        """Compare different configurations."""
        results = {}

        for config in configs:
            profile_name = f"{config['model']}_{config['duration']}s_{config.get('resolution', '1080p')}"

            result = self.benchmark(
                profile_name=profile_name,
                prompt=prompt,
                iterations=iterations,
                **config
            )

            results[profile_name] = result

        # Find optimal
        valid_results = {k: v for k, v in results.items() if "no_data" not in v["stats"]}

        if valid_results:
            fastest = min(valid_results.items(), key=lambda x: x[1]["stats"]["avg_time"])
            cheapest = min(valid_results.items(), key=lambda x: x[1]["stats"]["avg_credits"])

            return {
                "results": results,
                "recommendations": {
                    "fastest": fastest[0],
                    "fastest_time": fastest[1]["stats"]["avg_time"],
                    "cheapest": cheapest[0],
                    "cheapest_credits": cheapest[1]["stats"]["avg_credits"]
                }
            }

        return {"results": results, "recommendations": None}

# Usage
profiler = KlingAIPerformanceProfiler()

# Single benchmark
result = profiler.benchmark(
    profile_name="baseline",
    prompt="A peaceful forest scene with sunlight filtering through trees",
    model="kling-v1.5",
    duration=5,
    iterations=3
)

print(f"Average time: {result['stats']['avg_time']:.1f}s")

# Compare configurations
comparison = profiler.compare_configs(
    prompt="A serene mountain landscape",
    configs=[
        {"model": "kling-v1", "duration": 5},
        {"model": "kling-v1.5", "duration": 5},
        {"model": "kling-v1.5", "duration": 10},
    ],
    iterations=2
)

print(f"Fastest: {comparison['recommendations']['fastest']}")
print(f"Cheapest: {comparison['recommendations']['cheapest']}")
```

## Optimization Strategies

```python
class OptimizationStrategy:
    """Optimization strategies for different use cases."""

    @staticmethod
    def for_speed() -> Dict:
        """Optimize for fastest generation."""
        return {
            "model": "kling-v1",
            "duration": 5,
            "resolution": "720p",
            "tips": [
                "Use shortest duration",
                "Use base model",
                "Lower resolution reduces processing",
                "Simple prompts generate faster"
            ]
        }

    @staticmethod
    def for_quality() -> Dict:
        """Optimize for highest quality."""
        return {
            "model": "kling-pro",
            "duration": 10,
            "resolution": "1080p",
            "tips": [
                "Use pro model",
                "Longer duration = more coherent",
                "Detailed, specific prompts",
                "Include style and mood descriptors"
            ]
        }

    @staticmethod
    def for_cost() -> Dict:
        """Optimize for lowest cost."""
        return {
            "model": "kling-v1",
            "duration": 5,
            "resolution": "720p",
            "tips": [
                "Use base model (cheapest)",
                "5-second clips only",
                "Validate prompts before generation",
                "Cache and reuse successful outputs"
            ]
        }

    @staticmethod
    def balanced() -> Dict:
        """Balanced optimization."""
        return {
            "model": "kling-v1.5",
            "duration": 5,
            "resolution": "1080p",
            "tips": [
                "Mid-tier model for quality/speed",
                "5 seconds is usually enough",
                "Full HD resolution",
                "Good for most use cases"
            ]
        }

# Usage
print("Speed optimization:")
speed_config = OptimizationStrategy.for_speed()
print(f"  Config: {speed_config['model']}, {speed_config['duration']}s, {speed_config['resolution']}")
for tip in speed_config["tips"]:
    print(f"  - {tip}")
```

## Caching Layer

```python
import hashlib
import json
from pathlib import Path

class VideoCache:
    """Cache generated videos to avoid regeneration."""

    def __init__(self, cache_dir: str = ".video_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.index_file = self.cache_dir / "index.json"
        self.index = self._load_index()

    def _load_index(self) -> Dict:
        if self.index_file.exists():
            return json.loads(self.index_file.read_text())
        return {}

    def _save_index(self):
        self.index_file.write_text(json.dumps(self.index, indent=2))

    def _cache_key(self, prompt: str, model: str, duration: int) -> str:
        """Generate cache key from parameters."""
        data = f"{prompt}:{model}:{duration}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def get(self, prompt: str, model: str, duration: int) -> Optional[Dict]:
        """Get cached result if exists."""
        key = self._cache_key(prompt, model, duration)
        if key in self.index:
            entry = self.index[key]
            print(f"Cache hit: {key}")
            return entry
        return None

    def set(self, prompt: str, model: str, duration: int, result: Dict):
        """Cache a generation result."""
        key = self._cache_key(prompt, model, duration)
        self.index[key] = {
            "prompt": prompt,
            "model": model,
            "duration": duration,
            "video_url": result.get("video_url"),
            "job_id": result.get("job_id"),
            "cached_at": datetime.utcnow().isoformat()
        }
        self._save_index()
        print(f"Cached: {key}")

# Cached client wrapper
class CachedKlingAIClient:
    def __init__(self, api_key: str, cache: VideoCache):
        self.api_key = api_key
        self.cache = cache
        self.base_url = "https://api.klingai.com/v1"

    def generate(self, prompt: str, model: str = "kling-v1.5", duration: int = 5) -> Dict:
        # Check cache first
        cached = self.cache.get(prompt, model, duration)
        if cached:
            return cached

        # Generate new
        # ... generation code ...
        result = {"job_id": "...", "video_url": "..."}

        # Cache result
        self.cache.set(prompt, model, duration, result)

        return result
```

## Output

Successful execution produces:
- Performance benchmarks
- Optimization recommendations
- Configuration comparisons
- Cached generation results

## Error Handling

Common errors and solutions:
1. **Benchmark Variance**: Run more iterations
2. **Timeout**: Use longer timeout for pro model
3. **Cache Stale**: Implement cache expiry

## Examples

See code examples above for complete, runnable implementations.

## Resources

- [Kling AI Performance](https://docs.klingai.com/performance)
- [Optimization Best Practices](https://docs.klingai.com/best-practices)
- [Caching Strategies](https://cachetools.readthedocs.io/)
