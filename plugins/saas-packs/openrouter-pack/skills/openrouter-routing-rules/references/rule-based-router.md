# Rule-Based Router

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
