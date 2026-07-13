# Intelligent Model Selection

## Intelligent Model Selection

### Multi-Criteria Router

```python
from dataclasses import dataclass
from typing import Callable, Optional
import re

@dataclass
class ModelProfile:
    id: str
    strengths: list[str]
    cost_per_1k: float  # Approximate cost per 1K tokens
    max_context: int
    speed_tier: str  # "fast", "medium", "slow"
    quality_tier: str  # "budget", "standard", "premium", "enterprise"

MODEL_PROFILES = {
    "anthropic/claude-3-opus": ModelProfile(
        id="anthropic/claude-3-opus",
        strengths=["reasoning", "analysis", "creative", "code"],
        cost_per_1k=0.075,
        max_context=200000,
        speed_tier="slow",
        quality_tier="enterprise"
    ),
    "anthropic/claude-3.5-sonnet": ModelProfile(
        id="anthropic/claude-3.5-sonnet",
        strengths=["code", "analysis", "general", "fast-premium"],
        cost_per_1k=0.018,
        max_context=200000,
        speed_tier="medium",
        quality_tier="premium"
    ),
    "anthropic/claude-3-haiku": ModelProfile(
        id="anthropic/claude-3-haiku",
        strengths=["speed", "classification", "extraction", "simple"],
        cost_per_1k=0.001,
        max_context=200000,
        speed_tier="fast",
        quality_tier="budget"
    ),
    "openai/gpt-4-turbo": ModelProfile(
        id="openai/gpt-4-turbo",
        strengths=["general", "code", "json", "function-calling"],
        cost_per_1k=0.030,
        max_context=128000,
        speed_tier="medium",
        quality_tier="premium"
    ),
    "openai/gpt-3.5-turbo": ModelProfile(
        id="openai/gpt-3.5-turbo",
        strengths=["speed", "simple", "chat"],
        cost_per_1k=0.002,
        max_context=16000,
        speed_tier="fast",
        quality_tier="standard"
    ),
    "meta-llama/llama-3.1-70b-instruct": ModelProfile(
        id="meta-llama/llama-3.1-70b-instruct",
        strengths=["general", "code", "open-source"],
        cost_per_1k=0.001,
        max_context=131000,
        speed_tier="medium",
        quality_tier="standard"
    ),
}

class IntelligentRouter:
    """Route requests to optimal model based on task."""

    def __init__(self, profiles: dict = None):
        self.profiles = profiles or MODEL_PROFILES

    def route(
        self,
        prompt: str,
        task_type: str = None,
        max_cost_per_1k: float = None,
        required_context: int = None,
        speed_priority: bool = False,
        quality_priority: bool = False
    ) -> str:
        """Select best model for request."""
        candidates = list(self.profiles.values())

        # Filter by context requirement
        if required_context:
            candidates = [
                p for p in candidates
                if p.max_context >= required_context
            ]

        # Filter by cost
        if max_cost_per_1k:
            candidates = [
                p for p in candidates
                if p.cost_per_1k <= max_cost_per_1k
            ]

        # Filter by task type strengths
        if task_type:
            task_candidates = [
                p for p in candidates
                if task_type in p.strengths
            ]
            if task_candidates:
                candidates = task_candidates

        if not candidates:
            return "anthropic/claude-3.5-sonnet"  # Default fallback

        # Sort by priority
        if speed_priority:
            candidates.sort(key=lambda p: (
                {"fast": 0, "medium": 1, "slow": 2}[p.speed_tier],
                p.cost_per_1k
            ))
        elif quality_priority:
            candidates.sort(key=lambda p: (
                {"enterprise": 0, "premium": 1, "standard": 2, "budget": 3}[p.quality_tier],
                -p.cost_per_1k
            ))
        else:
            # Balance quality and cost
            candidates.sort(key=lambda p: (
                {"premium": 0, "standard": 1, "enterprise": 2, "budget": 3}[p.quality_tier],
                p.cost_per_1k
            ))

        return candidates[0].id

router = IntelligentRouter()
```

### Task Detection

```python
def detect_task_type(prompt: str) -> str:
    """Analyze prompt to determine task type."""
    prompt_lower = prompt.lower()

    # Code-related
    code_indicators = [
        r"```",
        r"\bdef\s+\w+",
        r"\bfunction\s+\w+",
        r"\bclass\s+\w+",
        r"\bcode\b",
        r"\bprogram\b",
        r"\bdebug\b",
        r"\brefactor\b",
    ]
    if any(re.search(p, prompt) for p in code_indicators):
        return "code"

    # Analysis/reasoning
    analysis_indicators = [
        r"\banalyze\b",
        r"\bexplain\b",
        r"\bcompare\b",
        r"\bevaluate\b",
        r"\bwhy\b.*\?",
        r"\bhow\b.*\?",
    ]
    if any(re.search(p, prompt_lower) for p in analysis_indicators):
        return "analysis"

    # Creative
    creative_indicators = [
        r"\bwrite\b.*\b(story|poem|essay|article)\b",
        r"\bcreate\b",
        r"\bimagine\b",
        r"\bcreative\b",
    ]
    if any(re.search(p, prompt_lower) for p in creative_indicators):
        return "creative"

    # Classification/extraction
    extraction_indicators = [
        r"\bextract\b",
        r"\bclassify\b",
        r"\bcategorize\b",
        r"\blist\b.*\bfrom\b",
    ]
    if any(re.search(p, prompt_lower) for p in extraction_indicators):
        return "extraction"

    # JSON output
    if "json" in prompt_lower:
        return "json"

    # Simple Q&A
    if len(prompt) < 100 and prompt.strip().endswith("?"):
        return "simple"

    return "general"

def auto_route(prompt: str, **kwargs) -> str:
    """Automatically route based on prompt analysis."""
    task_type = detect_task_type(prompt)
    context_needed = len(prompt) // 4 + kwargs.get("max_tokens", 1000)

    return router.route(
        prompt=prompt,
        task_type=task_type,
        required_context=context_needed,
        **kwargs
    )
```
