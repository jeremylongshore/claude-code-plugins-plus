---
name: openrouter-model-routing
description: |
  Implement advanced model routing with A/B testing. Use when optimizing model selection or running experiments. Trigger with phrases like 'openrouter a/b test', 'model experiment', 'openrouter routing', 'model comparison'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# OpenRouter Model Routing

## Overview

This skill covers advanced routing patterns including A/B testing, gradual rollouts, and performance-based model selection.

## Prerequisites

- OpenRouter integration
- Metrics collection capability

## Instructions

Follow these steps to implement this skill:

1. **Verify Prerequisites**: Ensure all prerequisites listed above are met
2. **Review the Implementation**: Study the code examples and patterns below
3. **Adapt to Your Environment**: Modify configuration values for your setup
4. **Test the Integration**: Run the verification steps to confirm functionality
5. **Monitor in Production**: Set up appropriate logging and monitoring

## Overview

This skill covers advanced routing patterns including A/B testing, gradual rollouts, and performance-based model selection.

## Prerequisites

- OpenRouter integration
- Metrics collection capability

## Intelligent Model Selection

### Multi-Criteria Router
```python
from dataclasses import dataclass
from typing import Callable, Optional
import re

@dataclass
class ModelProfile:
    id: str

## Detailed Reference

See `${CLAUDE_SKILL_DIR}/references/implementation.md` for complete implementation guide.
