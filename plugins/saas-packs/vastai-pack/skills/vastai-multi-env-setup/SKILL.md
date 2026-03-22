---
name: vastai-multi-env-setup
description: |
  Configure Vast.ai GPU cloud across dev, staging, and production environments.
  Use when isolating GPU pools per team, managing API key separation by env,
  or implementing spending controls per deployment tier.
  Trigger with phrases like "vastai environments", "vastai staging",
  "vastai dev prod", "vastai multi-env".
allowed-tools: Read, Write, Edit, Bash(vastai:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vast-ai, deployment]

---
# Vast.ai Multi-Environment Setup

## Overview
Configure separate Vast.ai environments for development, staging, and production by using different API keys, GPU profiles, and spending limits. Vast.ai does not have built-in environment isolation, so you implement it through configuration.

## Prerequisites
- Vast.ai accounts or API keys per environment
- Secrets manager for key storage
- Understanding of GPU profile requirements per tier

## Instructions

### Step 1: Environment Configuration

```python
# config.py — environment-specific Vast.ai settings
import os
from dataclasses import dataclass

@dataclass
class VastEnvConfig:
    name: str
    api_key: str
    max_dph: float           # Maximum $/hr per instance
    max_instances: int       # Concurrent instance limit
    max_daily_spend: float   # Daily budget cap
    gpu_whitelist: list      # Allowed GPU types
    reliability_min: float   # Minimum reliability score
    auto_destroy_hours: int  # Auto-destroy timeout

ENVIRONMENTS = {
    "development": VastEnvConfig(
        name="development",
        api_key=os.environ.get("VASTAI_DEV_KEY", ""),
        max_dph=0.25,
        max_instances=2,
        max_daily_spend=5.00,
        gpu_whitelist=["RTX_3090", "RTX_4090"],
        reliability_min=0.90,
        auto_destroy_hours=2,
    ),
    "staging": VastEnvConfig(
        name="staging",
        api_key=os.environ.get("VASTAI_STAGING_KEY", ""),
        max_dph=2.00,
        max_instances=4,
        max_daily_spend=50.00,
        gpu_whitelist=["RTX_4090", "A100"],
        reliability_min=0.95,
        auto_destroy_hours=12,
    ),
    "production": VastEnvConfig(
        name="production",
        api_key=os.environ.get("VASTAI_PROD_KEY", ""),
        max_dph=4.00,
        max_instances=16,
        max_daily_spend=500.00,
        gpu_whitelist=["A100", "H100_SXM"],
        reliability_min=0.98,
        auto_destroy_hours=48,
    ),
}

def get_config(env=None):
    env = env or os.environ.get("VASTAI_ENV", "development")
    return ENVIRONMENTS[env]
```

### Step 2: Environment-Aware Client

```python
class EnvAwareVastClient:
    def __init__(self, env="development"):
        self.config = get_config(env)
        self.client = VastClient(api_key=self.config.api_key)

    def search_offers(self, **overrides):
        query = {
            "rentable": {"eq": True},
            "reliability2": {"gte": self.config.reliability_min},
            "dph_total": {"lte": overrides.get("max_dph", self.config.max_dph)},
        }
        gpu = overrides.get("gpu_name", self.config.gpu_whitelist[0])
        query["gpu_name"] = {"eq": gpu}
        return self.client.search_offers(query)

    def create_instance(self, offer_id, image, disk_gb=20):
        # Enforce instance limit
        current = len([i for i in self.client.show_instances()
                      if i.get("actual_status") == "running"])
        if current >= self.config.max_instances:
            raise RuntimeError(
                f"{self.config.name}: Instance limit reached ({current}/{self.config.max_instances})")
        return self.client.create_instance(offer_id, image, disk_gb)
```

### Step 3: Environment Variables

```bash
# .env.development
VASTAI_ENV=development
VASTAI_DEV_KEY=dev-api-key-here

# .env.staging
VASTAI_ENV=staging
VASTAI_STAGING_KEY=staging-api-key-here

# .env.production (in secrets manager, never in files)
VASTAI_ENV=production
VASTAI_PROD_KEY=prod-api-key-here
```

### Step 4: Docker Image Tagging by Environment

```bash
# Dev: use latest for quick iteration
docker tag training:latest ghcr.io/org/training:dev

# Staging: use specific commit hash
docker tag training:latest ghcr.io/org/training:stg-$(git rev-parse --short HEAD)

# Production: use semantic version
docker tag training:latest ghcr.io/org/training:v1.2.3
```

## Output
- Environment-specific configuration (dev, staging, production)
- Instance limits and budget caps per environment
- GPU whitelist enforcement
- Docker image tagging strategy
- Environment-aware client wrapper

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Wrong environment selected | `VASTAI_ENV` not set | Default to `development` for safety |
| Instance limit exceeded | Too many concurrent instances | Destroy idle instances or increase limit |
| Daily budget exceeded | Expensive GPUs running too long | Implement auto-destroy timeout |
| Dev key used in prod | Environment variable misconfigured | Validate key matches expected account |

## Resources
- [Vast.ai CLI](https://docs.vast.ai/cli/get-started)
- [REST API](https://vast.ai/developers/api)

## Next Steps
For observability and monitoring, see `vastai-observability`.

## Examples

**Dev workflow**: `VASTAI_ENV=development python deploy.py --gpu RTX_4090` — enforces $0.25/hr max, 2 instance limit, auto-destroy after 2 hours.

**Prod deployment**: `VASTAI_ENV=production python deploy.py --gpu H100_SXM --gpus 4` — allows up to 16 instances at $4/hr with 48-hour timeout.
