---
name: openrouter-routing-rules
description: 'Define custom routing rules for OpenRouter requests based on user tier,
  task type, cost budget, and availability. Triggers: ''openrouter rules'', ''routing
  rules'', ''custom routing openrouter'', ''conditional model selection''.

  '
allowed-tools: Read, Write, Edit, Grep, Bash(python3:*)
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- openrouter
- routing
- rules-engine
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# OpenRouter Routing Rules

## Overview

Beyond simple task-based model selection, production systems need configurable routing rules that consider user tier, cost budget, time of day, model availability, and feature requirements. This skill covers building a rules engine for OpenRouter model selection with config-driven rules, dynamic conditions, and override capabilities.

## Prerequisites

- An OpenRouter API key (`sk-or-v1-...`) exported as `OPENROUTER_API_KEY` — see the `openrouter-install-auth` skill for setup
- Python 3.8+ with the OpenAI SDK — the rules engine itself is stdlib (`dataclasses`, `json`, `random`) layered on top
- Per-request metadata available in your app: user tier, task type, remaining budget, tool/vision needs, latency SLA (the `RoutingContext` fields)
- Budget tracking wired up (see `openrouter-cost-controls`) if you use budget-conditioned rules like `low-budget`

## Instructions

1. Model each request's metadata as a `RoutingContext` (user tier, task type, budget remaining, tools/vision flags, latency SLA) per Rules Engine.
2. Define `RoutingRule` entries in priority order — free-tier first, then budget, capability (tools/vision), task type, latency, and always a `priority=99` default catch-all.
3. Resolve the winning rule with `evaluate_rules(ctx)`: first match by ascending priority wins; failing conditions return False instead of raising.
4. Execute through `routed_completion()` per Routed Completion — it applies the rule's model, fallback chain (`models` + `route: "fallback"`), and `max_tokens`.
5. To make rules hot-reloadable, express them as JSON per Config-Driven Rules and match with `match_config_rule()` instead of lambdas.
6. Validate any rule change on a slice of traffic with `ab_test_routing()` per A/B Testing Rules before full rollout.

## Rules Engine

```python
import os, json, time
from dataclasses import dataclass
from typing import Optional, Callable
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    default_headers={"HTTP-Referer": "https://my-app.com", "X-Title": "my-app"},
)

@dataclass
class RoutingContext:
    user_tier: str = "free"        # "free" | "basic" | "pro" | "enterprise"
    task_type: str = "general"     # "chat" | "code" | "analysis" | "classification"
    budget_remaining: float = 0.0  # Remaining daily budget in dollars
    prompt_tokens_est: int = 0     # Estimated prompt tokens
    needs_tools: bool = False      # Requires function calling
    needs_vision: bool = False     # Requires image input
    max_latency_ms: int = 30000    # Latency SLA

@dataclass
class RoutingRule:
    name: str
    priority: int                  # Lower = higher priority
    condition: Callable[[RoutingContext], bool]
    model: str
    fallbacks: list[str] = None
    max_tokens: int = 1024

    def matches(self, ctx: RoutingContext) -> bool:
        try:
            return self.condition(ctx)
        except Exception:
            return False

# Define rules in priority order
RULES = [
    # Rule 1: Free users get free models only
    RoutingRule(
        name="free-tier",
        priority=1,
        condition=lambda ctx: ctx.user_tier == "free",
        model="google/gemma-2-9b-it:free",
        fallbacks=["meta-llama/llama-3.1-8b-instruct"],
        max_tokens=512,
    ),
    # Rule 2: Low budget → cheap models
    RoutingRule(
        name="low-budget",
        priority=2,
        condition=lambda ctx: ctx.budget_remaining < 1.0 and ctx.user_tier != "enterprise",
        model="openai/gpt-4o-mini",
        fallbacks=["meta-llama/llama-3.1-8b-instruct"],
        max_tokens=512,
    ),
    # Rule 3: Tool calling required → tool-capable models
    RoutingRule(
        name="tools-required",
        priority=3,
        condition=lambda ctx: ctx.needs_tools,
        model="openai/gpt-4o",
        fallbacks=["anthropic/claude-3.5-sonnet"],
    ),
    # Rule 4: Vision required
    RoutingRule(
        name="vision-required",
        priority=4,
        condition=lambda ctx: ctx.needs_vision,
        model="openai/gpt-4o",
        fallbacks=["anthropic/claude-3.5-sonnet", "google/gemini-2.0-flash-001"],
    ),
    # Rule 5: Code tasks → Claude
    RoutingRule(
        name="code-tasks",
        priority=5,
        condition=lambda ctx: ctx.task_type == "code",
        model="anthropic/claude-3.5-sonnet",
        fallbacks=["openai/gpt-4o"],
    ),
    # Rule 6: Latency-sensitive → fast models
    RoutingRule(
        name="low-latency",
        priority=6,
        condition=lambda ctx: ctx.max_latency_ms < 3000,
        model="openai/gpt-4o-mini",
        fallbacks=["anthropic/claude-3-haiku"],
    ),
    # Rule 7: Enterprise gets premium
    RoutingRule(
        name="enterprise-default",
        priority=7,
        condition=lambda ctx: ctx.user_tier == "enterprise",
        model="anthropic/claude-3.5-sonnet",
        fallbacks=["openai/gpt-4o", "openai/gpt-4o-mini"],
    ),
    # Rule 8: Default catch-all
    RoutingRule(
        name="default",
        priority=99,
        condition=lambda ctx: True,  # Always matches
        model="openai/gpt-4o-mini",
        fallbacks=["meta-llama/llama-3.1-8b-instruct"],
    ),
]

def evaluate_rules(ctx: RoutingContext) -> RoutingRule:
    """Find the first matching rule (sorted by priority)."""
    sorted_rules = sorted(RULES, key=lambda r: r.priority)
    for rule in sorted_rules:
        if rule.matches(ctx):
            return rule
    return sorted_rules[-1]  # Default catch-all
```

## Config-Driven Rules (JSON)

```python
RULES_CONFIG = {
    "rules": [
        {
            "name": "free-tier",
            "priority": 1,
            "conditions": {"user_tier": "free"},
            "model": "google/gemma-2-9b-it:free",
            "max_tokens": 512,
        },
        {
            "name": "code-pro",
            "priority": 5,
            "conditions": {"task_type": "code", "user_tier": ["pro", "enterprise"]},
            "model": "anthropic/claude-3.5-sonnet",
            "max_tokens": 2048,
        },
        {
            "name": "default",
            "priority": 99,
            "conditions": {},
            "model": "openai/gpt-4o-mini",
        },
    ]
}

def match_config_rule(ctx: RoutingContext, rule_config: dict) -> bool:
    """Match a context against config-driven conditions."""
    conditions = rule_config.get("conditions", {})
    for key, expected in conditions.items():
        actual = getattr(ctx, key, None)
        if isinstance(expected, list):
            if actual not in expected:
                return False
        elif actual != expected:
            return False
    return True
```

## Routed Completion

```python
def routed_completion(messages: list[dict], ctx: RoutingContext, **kwargs):
    """Execute completion with rule-based routing."""
    rule = evaluate_rules(ctx)

    extra_body = {}
    if rule.fallbacks:
        extra_body = {
            "models": [rule.model] + rule.fallbacks,
            "route": "fallback",
        }

    response = client.chat.completions.create(
        model=rule.model,
        messages=messages,
        max_tokens=rule.max_tokens,
        extra_body=extra_body or None,
        **kwargs,
    )

    return {
        "content": response.choices[0].message.content,
        "model": response.model,
        "rule": rule.name,
        "tokens": response.usage.prompt_tokens + response.usage.completion_tokens,
    }

# Usage
ctx = RoutingContext(user_tier="pro", task_type="code", budget_remaining=50.0)
result = routed_completion(
    [{"role": "user", "content": "Refactor this function..."}],
    ctx=ctx,
)
print(f"Rule: {result['rule']}, Model: {result['model']}")
```

## A/B Testing Rules

```python
import random

def ab_test_routing(ctx: RoutingContext, test_name: str, variant_b_pct: float = 0.10):
    """Route a percentage of traffic to variant B for comparison."""
    rule = evaluate_rules(ctx)

    if random.random() < variant_b_pct:
        # Variant B: try a different model
        return RoutingRule(
            name=f"{rule.name}:variant-b",
            priority=rule.priority,
            condition=rule.condition,
            model="openai/gpt-4o",  # Test against a different model
            fallbacks=rule.fallbacks,
            max_tokens=rule.max_tokens,
        )
    return rule
```

## Output

- A resolved `RoutingRule` per request — name, model, fallbacks, `max_tokens` — from `evaluate_rules()`
- A completion result dict from `routed_completion()`: `{content, model, rule, tokens}`; the `rule` field makes every routing decision auditable
- A JSON rules config (Config-Driven Rules) that can be hot-reloaded without redeployment
- A/B variant assignments (`<rule-name>:variant-b`) for a configurable percentage of traffic

## Examples

A pro-tier code request falls through the free-tier, budget, tools, and vision rules and matches `code-tasks`:

```python
ctx = RoutingContext(user_tier="pro", task_type="code", budget_remaining=50.0)
result = routed_completion([{"role": "user", "content": "Refactor this function..."}], ctx=ctx)
print(f"Rule: {result['rule']}, Model: {result['model']}")
# Rule: code-tasks, Model: anthropic/claude-3.5-sonnet
```

The same context with `user_tier="free"` matches the priority-1 `free-tier` rule instead, landing on `google/gemma-2-9b-it:free` capped at 512 tokens. More worked examples: `references/examples.md`.

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| No rule matched | Missing default catch-all | Always include a `priority=99` default rule |
| Rule condition error | Dynamic check raised exception | Wrap condition in try/catch; return False on error |
| Wrong model selected | Rule priority incorrect | Log matching rule name; review priority ordering |
| Config parse error | Invalid JSON rule definition | Validate config at startup; fail fast |

## Enterprise Considerations

- Store rules in a config file or database for hot-reloading without redeployment
- Log every routing decision (rule name, model, context) for analytics and debugging
- Use A/B testing to validate rule changes before full rollout
- Always include a default catch-all rule with a reliable, affordable model
- Version your rule configurations and track changes alongside code deployments
- Combine routing rules with budget enforcement (see openrouter-cost-controls)

## References

- Examples | Errors
- [Model Routing](https://openrouter.ai/docs/features/model-routing) | [Provider Routing](https://openrouter.ai/docs/features/provider-routing)
