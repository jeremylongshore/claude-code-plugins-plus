---
name: openrouter-model-routing
description: |
  Advanced model routing strategies. Triggers on "openrouter intelligent routing",
  "openrouter model selection", "dynamic model routing", "openrouter smart routing".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# OpenRouter Model Routing

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

## Cost-Quality Optimization

### Adaptive Quality Router
```python
class AdaptiveQualityRouter:
    """Adjust model quality based on request importance."""

    def __init__(self):
        self.quality_levels = {
            "low": ["anthropic/claude-3-haiku", "openai/gpt-3.5-turbo"],
            "medium": ["anthropic/claude-3.5-sonnet", "openai/gpt-4-turbo"],
            "high": ["anthropic/claude-3-opus", "openai/gpt-4"],
        }

    def route(
        self,
        prompt: str,
        importance: str = "medium",
        user_tier: str = "standard"
    ) -> str:
        # Adjust quality based on user tier
        if user_tier == "free":
            importance = "low"
        elif user_tier == "enterprise":
            importance = max(importance, "medium")

        # Get models for quality level
        models = self.quality_levels.get(importance, self.quality_levels["medium"])

        # Select based on task
        task = detect_task_type(prompt)
        if task == "code" and importance != "low":
            return "anthropic/claude-3.5-sonnet"
        if task == "simple":
            return models[0]  # Cheapest

        return models[0]  # First available at quality level

adaptive_router = AdaptiveQualityRouter()
```

### Budget-Aware Routing
```python
class BudgetRouter:
    """Route while respecting budget constraints."""

    def __init__(self, daily_budget: float):
        self.daily_budget = daily_budget
        self.spent_today = 0.0

    def route(self, prompt: str, preferred_model: str = None) -> str:
        remaining = self.daily_budget - self.spent_today
        estimated_cost = self._estimate_cost(prompt, preferred_model)

        # If preferred model fits budget, use it
        if preferred_model and estimated_cost < remaining * 0.1:
            return preferred_model

        # Otherwise, find best model within budget
        models_by_cost = sorted(
            MODEL_PROFILES.values(),
            key=lambda p: p.cost_per_1k
        )

        for profile in models_by_cost:
            cost = self._estimate_cost(prompt, profile.id)
            if cost < remaining * 0.1:  # Don't use more than 10% of remaining
                return profile.id

        # Return cheapest available
        return models_by_cost[0].id

    def _estimate_cost(self, prompt: str, model: str) -> float:
        tokens = len(prompt) // 4 + 500  # Rough estimate
        profile = MODEL_PROFILES.get(model)
        if not profile:
            return 0.01  # Default estimate
        return tokens * profile.cost_per_1k / 1000

    def record_spend(self, cost: float):
        self.spent_today += cost

budget_router = BudgetRouter(daily_budget=50.0)
```

## Cascading Router

### Try Cheap, Fall Back to Premium
```python
class CascadeRouter:
    """Try cheaper model first, escalate if needed."""

    def __init__(self):
        self.cascade = [
            ("anthropic/claude-3-haiku", self._is_sufficient_simple),
            ("anthropic/claude-3.5-sonnet", self._is_sufficient_complex),
            ("anthropic/claude-3-opus", lambda r: True),  # Final fallback
        ]

    def _is_sufficient_simple(self, response: str) -> bool:
        """Check if simple model response is sufficient."""
        # Too short might mean model struggled
        if len(response) < 50:
            return False
        # Check for uncertainty markers
        uncertainty = ["i'm not sure", "i cannot", "unclear", "don't know"]
        if any(u in response.lower() for u in uncertainty):
            return False
        return True

    def _is_sufficient_complex(self, response: str) -> bool:
        """Check if complex model response is sufficient."""
        if len(response) < 20:
            return False
        return True

    def chat(self, prompt: str, **kwargs):
        """Try models in cascade until sufficient response."""
        for model, is_sufficient in self.cascade:
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    **kwargs
                )
                content = response.choices[0].message.content

                if is_sufficient(content):
                    return response, model

            except Exception:
                continue

        raise Exception("All cascade models failed")

cascade = CascadeRouter()
response, used_model = cascade.chat("What is 2+2?")
```

## Context-Aware Routing

### Conversation History Router
```python
class ConversationRouter:
    """Route based on conversation state."""

    def __init__(self):
        self.turn_count = 0
        self.complexity_score = 0

    def route(self, messages: list) -> str:
        self.turn_count = len([m for m in messages if m["role"] == "user"])

        # Analyze conversation complexity
        total_length = sum(len(m["content"]) for m in messages)
        has_code = any("```" in m["content"] for m in messages)
        question_count = sum(
            m["content"].count("?")
            for m in messages if m["role"] == "user"
        )

        # Simple: short conversation, no code, few questions
        if total_length < 1000 and not has_code and question_count <= 2:
            return "anthropic/claude-3-haiku"

        # Complex: long conversation or code
        if total_length > 10000 or has_code:
            return "anthropic/claude-3.5-sonnet"

        # Medium: default
        return "openai/gpt-4-turbo"

conv_router = ConversationRouter()

def chat_multi_turn(messages: list, **kwargs):
    model = conv_router.route(messages)
    return client.chat.completions.create(
        model=model,
        messages=messages,
        **kwargs
    )
```

## A/B Testing Router

### Experiment-Driven Selection
```python
import random
import hashlib

class ABTestRouter:
    """A/B test different models."""

    def __init__(self):
        self.experiments = {}
        self.results = {}

    def add_experiment(
        self,
        name: str,
        control: str,
        variant: str,
        traffic_percent: int = 10
    ):
        self.experiments[name] = {
            "control": control,
            "variant": variant,
            "traffic": traffic_percent
        }
        self.results[name] = {"control": [], "variant": []}

    def route(self, experiment: str, user_id: str = None) -> tuple[str, str]:
        """Route and return (model, variant_name)."""
        exp = self.experiments.get(experiment)
        if not exp:
            return ("anthropic/claude-3.5-sonnet", "default")

        # Deterministic assignment based on user_id
        if user_id:
            hash_val = int(hashlib.md5(
                f"{experiment}:{user_id}".encode()
            ).hexdigest(), 16)
            in_variant = (hash_val % 100) < exp["traffic"]
        else:
            in_variant = random.randint(1, 100) <= exp["traffic"]

        if in_variant:
            return (exp["variant"], "variant")
        return (exp["control"], "control")

    def record_result(
        self,
        experiment: str,
        variant: str,
        latency_ms: float,
        success: bool,
        quality_score: float = None
    ):
        self.results[experiment][variant].append({
            "latency": latency_ms,
            "success": success,
            "quality": quality_score
        })

    def get_stats(self, experiment: str) -> dict:
        """Get experiment statistics."""
        exp_results = self.results.get(experiment, {})
        stats = {}

        for variant, data in exp_results.items():
            if not data:
                continue
            stats[variant] = {
                "count": len(data),
                "success_rate": sum(1 for d in data if d["success"]) / len(data),
                "avg_latency": sum(d["latency"] for d in data) / len(data),
                "avg_quality": (
                    sum(d["quality"] for d in data if d["quality"])
                    / len([d for d in data if d["quality"]])
                    if any(d["quality"] for d in data) else None
                )
            }

        return stats

ab_router = ABTestRouter()
ab_router.add_experiment(
    "sonnet_vs_gpt4",
    control="openai/gpt-4-turbo",
    variant="anthropic/claude-3.5-sonnet",
    traffic_percent=20
)
```
