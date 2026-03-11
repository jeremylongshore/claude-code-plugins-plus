---
name: vastai-multi-env-setup
description: |
  Configure Vast.ai GPU cloud across development, staging, and production environments.
  Use when setting up isolated GPU pools per team, managing API key separation by env,
  or implementing spending controls and GPU type restrictions per deployment tier.
  Trigger with phrases like "vastai environments", "vastai staging", "vastai dev prod",
  "vastai environment setup", "vastai multi-env gpu config".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Vast.ai Multi-Environment Setup

## Overview
Vast.ai "environments" for GPU workloads map to separate API keys with different spending limits, allowed GPU types, and maximum instance counts. Development experiments should be restricted to cost-efficient spot instances with low spending caps.

## Prerequisites
- Vast.ai account with API key from cloud.vast.ai
- `vastai` CLI installed (`pip install vastai`)
- Different API keys or spending limits configured per team/environment

## Environment Strategy

| Environment | GPU Types | Max Instances | Spending Cap | Instance Type |
|-------------|-----------|---------------|--------------|---------------|
| Development | RTX 3090, RTX 4090 | 2 | $50/month | Spot only |
| Staging | RTX 4090, A6000 | 5 | $200/month | Spot preferred |
| Production | A100, H100 | 20 | $5000/month | On-demand + spot |

## Instructions

### Step 1: API Key Management Per Environment
```bash
# Development: store in .env.local
echo "VAST_API_KEY=dev_key_abc123" >> .env.local
echo "VAST_MAX_PRICE_PER_HR=0.40" >> .env.local   # max $/hr for dev instances

# Staging: GitHub Actions environment secrets
# Add VAST_API_KEY_STAGING to staging environment

# Production: AWS Secrets Manager or similar
aws secretsmanager create-secret \
  --name vast/production/api-key \
  --secret-string "prod_key_xyz789"
```

### Step 2: Environment-Aware Vast.ai Configuration
```python
# config/vastai.py
import os
from dataclasses import dataclass

@dataclass
class VastAIConfig:
    api_key: str
    max_price_per_hr: float       # maximum $/hr to spend on an instance
    allowed_gpu_types: list[str]  # GPU whitelist
    max_instances: int
    spot_only: bool               # restrict to interruptible spot instances

ENV_CONFIGS = {
    "development": VastAIConfig(
        api_key=os.environ.get("VAST_API_KEY", ""),
        max_price_per_hr=0.40,    # RTX 3090 range
        allowed_gpu_types=["RTX_3090", "RTX_4090", "RTX_3080"],
        max_instances=2,
        spot_only=True,           # spot only in dev to minimize cost
    ),
    "staging": VastAIConfig(
        api_key=os.environ.get("VAST_API_KEY_STAGING", ""),
        max_price_per_hr=1.00,
        allowed_gpu_types=["RTX_4090", "A6000", "A100_PCIE_40GB"],
        max_instances=5,
        spot_only=False,
    ),
    "production": VastAIConfig(
        api_key=os.environ.get("VAST_API_KEY_PROD", ""),
        max_price_per_hr=4.00,    # up to H100 range
        allowed_gpu_types=["A100_SXM4_80GB", "H100_SXM5_80GB", "A100_PCIE_40GB"],
        max_instances=20,
        spot_only=False,
    ),
}

def get_vastai_config() -> VastAIConfig:
    env = os.environ.get("APP_ENV", "development")
    config = ENV_CONFIGS.get(env, ENV_CONFIGS["development"])
    if not config.api_key:
        raise ValueError(f"VAST_API_KEY not configured for {env}")
    return config
```

### Step 3: Policy-Enforced Instance Creation
```python
# lib/vastai_service.py
import vastai
from config.vastai import get_vastai_config

def find_cheapest_valid_instance(gpu_count: int = 1):
    """Find cheapest instance matching environment policy."""
    cfg = get_vastai_config()
    vastai.api_key = cfg.api_key

    # Build search query respecting environment policy
    gpu_filter = " || ".join(f"gpu_name={g}" for g in cfg.allowed_gpu_types)
    query = f"({gpu_filter}) num_gpus={gpu_count} dph_total<{cfg.max_price_per_hr}"

    if cfg.spot_only:
        query += " reliability>0.9"  # spot instances with high reliability

    offers = vastai.search_offers(query, order="dph_total", limit=5)

    if not offers:
        raise ValueError(f"No instances matching policy under ${cfg.max_price_per_hr}/hr")

    return offers[0]
```

### Step 4: Environment Variable Setup
```bash
# .env.local (development)
VAST_API_KEY=dev_key_abc123
APP_ENV=development

# GitHub Actions staging
VAST_API_KEY_STAGING=staging_key_def456
APP_ENV=staging

# GitHub Actions production
VAST_API_KEY_PROD=prod_key_xyz789
APP_ENV=production
```

### Step 5: Startup Validation
```python
# scripts/validate-vastai-env.py
from config.vastai import get_vastai_config

cfg = get_vastai_config()
print(f"Environment: {os.environ.get('APP_ENV', 'development')}")
print(f"Max price/hr: ${cfg.max_price_per_hr}")
print(f"Allowed GPUs: {', '.join(cfg.allowed_gpu_types)}")
print(f"Max instances: {cfg.max_instances}")
print(f"Spot only: {cfg.spot_only}")

# Verify key is valid
import vastai
vastai.api_key = cfg.api_key
try:
    vastai.whoami()
    print("API key: VALID")
except Exception as e:
    print(f"API key: INVALID - {e}")
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `insufficient_funds` | Account balance depleted | Add credits to vast.ai account |
| No instances found | GPU type not available | Broaden allowed GPU types or wait |
| Policy violation: GPU not allowed | Wrong env config loaded | Check `APP_ENV` variable is set correctly |
| Spending cap exceeded | Max instances hit | Destroy idle instances before provisioning new ones |

## Examples

### Quick Environment Validation
```bash
APP_ENV=production python3 scripts/validate-vastai-env.py
```

### Find Cheapest Dev Instance
```bash
# Development: find RTX 3090 under $0.40/hr
vastai search offers 'gpu_name=RTX_3090 num_gpus=1 dph_total<0.40' --order dph_total --limit 3
```

## Resources
- [Vast.ai API Documentation](https://vast.ai/docs/api)
- [Vast.ai CLI Reference](https://vast.ai/docs/cli)
- [Vast.ai Python API](https://github.com/vast-ai/vast-python)

## Next Steps
For enterprise access control, see `vastai-enterprise-rbac`.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale