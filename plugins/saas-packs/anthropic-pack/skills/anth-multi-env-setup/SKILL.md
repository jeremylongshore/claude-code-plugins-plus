---
name: anth-multi-env-setup
description: |
  Configure Claude API across dev, staging, and production environments
  with isolated keys, model routing, and spend controls per environment.
  Trigger with phrases like "anthropic environments", "claude multi-env",
  "anthropic staging setup", "claude dev vs prod config".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, anthropic]
compatible-with: claude-code
---

# Anthropic Multi-Environment Setup

## Overview

Configure isolated Claude API environments with per-env API keys, model selection, and spend controls using Anthropic Workspaces.

## Environment Configuration

```python
# config.py
import os
from dataclasses import dataclass

@dataclass
class ClaudeConfig:
    api_key: str
    model: str
    max_tokens: int
    max_retries: int
    timeout: float
    monthly_budget_usd: float

CONFIGS = {
    "development": ClaudeConfig(
        api_key=os.environ["ANTHROPIC_API_KEY_DEV"],
        model="claude-haiku-4-20250514",       # Cheap for dev
        max_tokens=256,
        max_retries=1,
        timeout=15.0,
        monthly_budget_usd=10.0,
    ),
    "staging": ClaudeConfig(
        api_key=os.environ["ANTHROPIC_API_KEY_STAGING"],
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        max_retries=2,
        timeout=30.0,
        monthly_budget_usd=50.0,
    ),
    "production": ClaudeConfig(
        api_key=os.environ["ANTHROPIC_API_KEY_PROD"],
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        max_retries=5,
        timeout=120.0,
        monthly_budget_usd=5000.0,
    ),
}

def get_config() -> ClaudeConfig:
    env = os.getenv("APP_ENV", "development")
    return CONFIGS[env]
```

## Anthropic Workspaces (Key Isolation)

Create separate Workspaces in [console.anthropic.com](https://console.anthropic.com/settings/workspaces):

| Workspace | Purpose | Rate Limit Tier |
|-----------|---------|-----------------|
| `dev` | Development & testing | Tier 1 |
| `staging` | Pre-production validation | Tier 2 |
| `production` | Live traffic | Tier 3+ |

Each workspace has independent API keys, usage tracking, and rate limits.

## Environment Files

```bash
# .env.development
ANTHROPIC_API_KEY_DEV=sk-ant-api03-dev-...
APP_ENV=development

# .env.staging
ANTHROPIC_API_KEY_STAGING=sk-ant-api03-stg-...
APP_ENV=staging

# .env.production (stored in secret manager, not files)
ANTHROPIC_API_KEY_PROD=sk-ant-api03-prd-...
APP_ENV=production
```

## Client Factory

```python
import anthropic

def create_client() -> anthropic.Anthropic:
    config = get_config()
    return anthropic.Anthropic(
        api_key=config.api_key,
        max_retries=config.max_retries,
        timeout=config.timeout,
    )
```

## Per-Environment Model Override

```python
# Development: always use Haiku (cheapest)
# Staging: use production model for accuracy testing
# Production: use configured model

def get_model(override: str | None = None) -> str:
    if override:
        return override
    return get_config().model
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| Dev key used in prod | Wrong env loaded | Validate key prefix matches environment |
| Staging rate limited | Low tier workspace | Upgrade staging workspace tier |
| Cost overrun in dev | No budget guard | Add per-env spend limits |

## Resources

- [Workspaces](https://docs.anthropic.com/en/docs/administration/workspaces)
- [Console](https://console.anthropic.com)

## Next Steps

For monitoring, see `anth-observability`.
