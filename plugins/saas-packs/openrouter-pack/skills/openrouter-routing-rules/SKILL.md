---
name: openrouter-routing-rules
description: |
  Implement intelligent model routing based on request characteristics. Use when optimizing for cost, speed, or quality per request. Trigger with phrases like 'openrouter routing', 'model selection', 'smart routing', 'dynamic model'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# OpenRouter Routing Rules

## Overview

This skill covers implementing request-based routing logic to select optimal models based on content, urgency, or cost constraints.

## Prerequisites

- OpenRouter integration
- Understanding of model capabilities and pricing

## Instructions

Follow these steps to implement this skill:

1. **Verify Prerequisites**: Ensure all prerequisites listed above are met
2. **Review the Implementation**: Study the code examples and patterns below
3. **Adapt to Your Environment**: Modify configuration values for your setup
4. **Test the Integration**: Run the verification steps to confirm functionality
5. **Monitor in Production**: Set up appropriate logging and monitoring

## Overview

This skill covers implementing request-based routing logic to select optimal models based on content, urgency, or cost constraints.

## Prerequisites

- OpenRouter integration
- Understanding of model capabilities and pricing

## Basic Routing Strategies

### Content-Based Routing
```python
def route_by_content(prompt: str) -> str:
    """Route to appropriate model based on content analysis."""
    prompt_lower = prompt.lower()

    # Code-related
    if any(word in prompt_lower for word in ["code", "function", "debug", "python", "javascript"]):
        return "anthropic/claude-3.5-sonnet"

## Detailed Reference

See `${CLAUDE_SKILL_DIR}/references/implementation.md` for complete implementation guide.
