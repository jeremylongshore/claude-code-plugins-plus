# Performance Profiler

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
