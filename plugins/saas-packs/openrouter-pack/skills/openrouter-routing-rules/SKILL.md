---
name: openrouter-routing-rules
description: |
  Configure OpenRouter model routing rules. Triggers on "openrouter routing",
  "openrouter model selection", "route requests openrouter", "openrouter rules".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# OpenRouter Routing Rules

## Basic Routing Strategies

### Content-Based Routing
```python
def route_by_content(prompt: str) -> str:
    """Route to appropriate model based on content analysis."""
    prompt_lower = prompt.lower()

    # Code-related
    if any(word in prompt_lower for word in ["code", "function", "debug", "python", "javascript"]):
        return "anthropic/claude-3.5-sonnet"

    # Creative writing
    if any(word in prompt_lower for word in ["write", "story", "creative", "poem"]):
        return "anthropic/claude-3-opus"

    # Quick questions
    if len(prompt) < 100 and prompt.endswith("?"):
        return "anthropic/claude-3-haiku"

    # Default
    return "openai/gpt-4-turbo"

def chat_routed(prompt: str, **kwargs):
    model = route_by_content(prompt)
    return client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        **kwargs
    )
```

### Token-Length Routing
```python
def estimate_tokens(text: str) -> int:
    """Rough token estimate (4 chars = 1 token)."""
    return len(text) // 4

def route_by_length(prompt: str, expected_output: int = 500) -> str:
    """Route based on context requirements."""
    prompt_tokens = estimate_tokens(prompt)
    total_tokens = prompt_tokens + expected_output

    # Short context
    if total_tokens < 4000:
        return "openai/gpt-3.5-turbo"

    # Medium context
    if total_tokens < 32000:
        return "openai/gpt-4-turbo"

    # Long context
    if total_tokens < 128000:
        return "anthropic/claude-3.5-sonnet"

    # Very long context
    return "anthropic/claude-3-opus"  # 200K context
```

## Rule-Based Router

### Configurable Router
```python
from dataclasses import dataclass
from typing import Callable, Optional
import re

@dataclass
class RoutingRule:
    name: str
    condition: Callable[[str], bool]
    model: str
    priority: int = 0

class ModelRouter:
    def __init__(self, default_model: str):
        self.rules: list[RoutingRule] = []
        self.default_model = default_model

    def add_rule(self, rule: RoutingRule):
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.priority, reverse=True)

    def route(self, prompt: str) -> str:
        for rule in self.rules:
            if rule.condition(prompt):
                return rule.model
        return self.default_model

# Build router with rules
router = ModelRouter(default_model="openai/gpt-4-turbo")

# Code detection
router.add_rule(RoutingRule(
    name="code",
    condition=lambda p: bool(re.search(r"```|def |function |class ", p)),
    model="anthropic/claude-3.5-sonnet",
    priority=10
))

# Quick question
router.add_rule(RoutingRule(
    name="quick",
    condition=lambda p: len(p) < 50 and p.strip().endswith("?"),
    model="anthropic/claude-3-haiku",
    priority=5
))

# JSON output
router.add_rule(RoutingRule(
    name="json_output",
    condition=lambda p: "json" in p.lower() and "output" in p.lower(),
    model="openai/gpt-4-turbo",
    priority=8
))

# Usage
model = router.route("Write a Python function to sort a list")
# Returns: anthropic/claude-3.5-sonnet
```

## Cost-Aware Routing

### Budget Router
```python
MODEL_COSTS = {
    "anthropic/claude-3-opus": 15.0,      # $/M tokens
    "openai/gpt-4": 30.0,
    "anthropic/claude-3.5-sonnet": 3.0,
    "openai/gpt-4-turbo": 10.0,
    "anthropic/claude-3-haiku": 0.25,
    "openai/gpt-3.5-turbo": 0.5,
    "meta-llama/llama-3.1-8b-instruct": 0.06,
}

class BudgetRouter:
    def __init__(self, budget_per_request: float):
        self.budget = budget_per_request

    def route(self, prompt: str, expected_tokens: int) -> str:
        estimated_cost = {}

        for model, cost_per_m in MODEL_COSTS.items():
            # Cost = tokens * price_per_million / 1_000_000
            request_cost = expected_tokens * cost_per_m / 1_000_000
            if request_cost <= self.budget:
                estimated_cost[model] = request_cost

        if not estimated_cost:
            # Return cheapest if nothing fits budget
            return min(MODEL_COSTS, key=MODEL_COSTS.get)

        # Return best model within budget
        quality_order = [
            "anthropic/claude-3-opus",
            "openai/gpt-4",
            "anthropic/claude-3.5-sonnet",
            "openai/gpt-4-turbo",
            "anthropic/claude-3-haiku",
            "openai/gpt-3.5-turbo",
            "meta-llama/llama-3.1-8b-instruct",
        ]

        for model in quality_order:
            if model in estimated_cost:
                return model

        return list(estimated_cost.keys())[0]

# $0.01 budget per request
budget_router = BudgetRouter(budget_per_request=0.01)
model = budget_router.route("Hello", expected_tokens=1000)
```

## Latency-Aware Routing

### Fast Response Router
```python
import time
from statistics import mean

class LatencyRouter:
    def __init__(self, models: list):
        self.models = models
        self.latency_history: dict[str, list[float]] = {m: [] for m in models}
        self.latency_budget: float = 5.0  # seconds

    def record_latency(self, model: str, latency: float):
        self.latency_history[model].append(latency)
        # Keep last 10
        self.latency_history[model] = self.latency_history[model][-10:]

    def get_avg_latency(self, model: str) -> float:
        history = self.latency_history[model]
        if not history:
            return 2.0  # Default assumption
        return mean(history)

    def route_for_speed(self) -> str:
        """Return fastest model that fits latency budget."""
        candidates = []
        for model in self.models:
            avg_latency = self.get_avg_latency(model)
            if avg_latency <= self.latency_budget:
                candidates.append((model, avg_latency))

        if not candidates:
            # Return fastest regardless
            return min(self.models, key=lambda m: self.get_avg_latency(m))

        # Sort by latency, return fastest
        candidates.sort(key=lambda x: x[1])
        return candidates[0][0]

    def chat(self, prompt: str, **kwargs):
        model = self.route_for_speed()
        start = time.time()

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            self.record_latency(model, time.time() - start)
            return response
        except Exception as e:
            self.record_latency(model, 30.0)  # Record as slow on error
            raise
```

## User-Based Routing

### Tier-Based Routing
```python
USER_TIERS = {
    "free": ["meta-llama/llama-3.1-8b-instruct", "mistralai/mistral-7b-instruct"],
    "basic": ["anthropic/claude-3-haiku", "openai/gpt-3.5-turbo"],
    "pro": ["anthropic/claude-3.5-sonnet", "openai/gpt-4-turbo"],
    "enterprise": ["anthropic/claude-3-opus", "openai/gpt-4"],
}

def route_by_user_tier(user_tier: str, task_type: str = "general") -> str:
    """Route based on user subscription tier."""
    available_models = USER_TIERS.get(user_tier, USER_TIERS["free"])

    # Task-specific preferences within tier
    if task_type == "code" and "anthropic/claude-3.5-sonnet" in available_models:
        return "anthropic/claude-3.5-sonnet"

    # Return first (best) available
    return available_models[0]

def chat_for_user(prompt: str, user_tier: str, task_type: str = "general"):
    model = route_by_user_tier(user_tier, task_type)
    return client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
```

## A/B Testing Router

### Experiment Router
```python
import random
import hashlib

class ABRouter:
    def __init__(self):
        self.experiments = {}

    def add_experiment(
        self,
        name: str,
        control_model: str,
        variant_model: str,
        variant_percentage: int = 10
    ):
        self.experiments[name] = {
            "control": control_model,
            "variant": variant_model,
            "percentage": variant_percentage,
        }

    def route(self, experiment_name: str, user_id: str = None) -> tuple[str, str]:
        """Return (model, variant_name) for tracking."""
        exp = self.experiments.get(experiment_name)
        if not exp:
            return ("openai/gpt-4-turbo", "default")

        # Deterministic routing for user
        if user_id:
            hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
            in_variant = (hash_value % 100) < exp["percentage"]
        else:
            in_variant = random.randint(1, 100) <= exp["percentage"]

        if in_variant:
            return (exp["variant"], "variant")
        return (exp["control"], "control")

ab_router = ABRouter()
ab_router.add_experiment(
    "sonnet_vs_gpt4",
    control_model="openai/gpt-4-turbo",
    variant_model="anthropic/claude-3.5-sonnet",
    variant_percentage=20
)

# Route and track
model, variant = ab_router.route("sonnet_vs_gpt4", user_id="user123")
# Log variant for analysis
```

## Configuration-Driven Routing

### YAML Rules Config
```yaml
# routing-rules.yaml
routing:
  default_model: openai/gpt-4-turbo

  rules:
    - name: code_detection
      pattern: "```|def |function |class "
      model: anthropic/claude-3.5-sonnet
      priority: 10

    - name: quick_question
      max_length: 50
      ends_with: "?"
      model: anthropic/claude-3-haiku
      priority: 5

    - name: json_output
      contains:
        - json
        - output
      model: openai/gpt-4-turbo
      priority: 8

  cost_limits:
    free_tier: 0.001
    pro_tier: 0.01
    enterprise: 0.10
```

### Load and Apply Rules
```python
import yaml
import re

def load_routing_rules(path: str):
    with open(path) as f:
        return yaml.safe_load(f)

def apply_rules(prompt: str, config: dict) -> str:
    """Apply routing rules from config."""
    for rule in sorted(config["routing"]["rules"], key=lambda r: -r.get("priority", 0)):
        # Pattern match
        if "pattern" in rule:
            if re.search(rule["pattern"], prompt):
                return rule["model"]

        # Length check
        if "max_length" in rule:
            if len(prompt) <= rule["max_length"]:
                if "ends_with" in rule:
                    if prompt.strip().endswith(rule["ends_with"]):
                        return rule["model"]
                else:
                    return rule["model"]

        # Contains check
        if "contains" in rule:
            prompt_lower = prompt.lower()
            if all(word in prompt_lower for word in rule["contains"]):
                return rule["model"]

    return config["routing"]["default_model"]
```
