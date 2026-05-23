# Optimization Strategies

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
