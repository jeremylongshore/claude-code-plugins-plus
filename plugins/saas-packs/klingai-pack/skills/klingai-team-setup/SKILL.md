---
name: klingai-team-setup
description: |
  Configure Kling AI for teams with per-project API keys, usage quotas, and role-based access.
  Trigger with phrases like 'klingai team', 'kling ai organization', 'klingai multi-user',
  'shared klingai access'.
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, kling-ai, teams, access-control]

---
# Kling AI Team Setup

## Overview

Manage team access to the Kling AI API using separate API keys, environment-based routing, usage quotas per team member, and centralized credential management.

## Per-Environment API Keys

Create separate API key pairs in the [Kling AI developer console](https://app.klingai.com/global/dev/api-key) for each environment:

| Environment | Key Naming Convention | Purpose |
|------------|----------------------|---------|
| Development | `dev-<project>` | Local testing, free tier |
| Staging | `staging-<project>` | Integration testing |
| Production | `prod-<project>` | Live traffic |

```bash
# .env.development
KLING_ACCESS_KEY="ak_dev_..."
KLING_SECRET_KEY="sk_dev_..."

# .env.production
KLING_ACCESS_KEY="ak_prod_..."
KLING_SECRET_KEY="sk_prod_..."
```

## Team Configuration

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class TeamMember:
    name: str
    email: str
    role: str  # admin, editor, viewer
    daily_credit_limit: int
    allowed_models: list[str]

@dataclass
class TeamConfig:
    name: str
    members: list[TeamMember]
    total_daily_limit: int = 1000
    default_model: str = "kling-v2-master"
    default_mode: str = "standard"

    def get_member(self, email: str) -> Optional[TeamMember]:
        return next((m for m in self.members if m.email == email), None)

# Example team configuration
team = TeamConfig(
    name="marketing",
    total_daily_limit=5000,
    members=[
        TeamMember("Alice", "alice@co.com", "admin", 2000,
                   ["kling-v2-6", "kling-v2-master", "kling-v2-5-turbo"]),
        TeamMember("Bob", "bob@co.com", "editor", 500,
                   ["kling-v2-master", "kling-v2-5-turbo"]),
        TeamMember("Carol", "carol@co.com", "viewer", 100,
                   ["kling-v2-5-turbo"]),
    ],
)
```

## Usage Quotas Per Member

```python
import time
from collections import defaultdict

class TeamQuotaManager:
    """Enforce per-member and team-wide credit limits."""

    def __init__(self, config: TeamConfig):
        self.config = config
        self._usage = defaultdict(int)  # email -> credits used today
        self._reset_time = time.time()

    def _check_reset(self):
        if time.time() - self._reset_time > 86400:
            self._usage.clear()
            self._reset_time = time.time()

    def authorize(self, email: str, credits_needed: int, model: str) -> bool:
        self._check_reset()
        member = self.config.get_member(email)
        if not member:
            raise PermissionError(f"Unknown user: {email}")

        if model not in member.allowed_models:
            raise PermissionError(f"{email} not authorized for {model}")

        if self._usage[email] + credits_needed > member.daily_credit_limit:
            raise RuntimeError(f"{email} exceeds daily limit "
                             f"({self._usage[email]} + {credits_needed} > {member.daily_credit_limit})")

        team_total = sum(self._usage.values()) + credits_needed
        if team_total > self.config.total_daily_limit:
            raise RuntimeError(f"Team daily limit exceeded ({team_total} > {self.config.total_daily_limit})")

        return True

    def record_usage(self, email: str, credits: int):
        self._usage[email] += credits

    def usage_report(self) -> dict:
        return {
            "team_total": sum(self._usage.values()),
            "team_limit": self.config.total_daily_limit,
            "by_member": dict(self._usage),
        }
```

## Secrets Management

| Tool | How to Store AK/SK |
|------|-------------------|
| AWS Secrets Manager | `aws secretsmanager create-secret --name kling/prod` |
| GCP Secret Manager | `gcloud secrets create kling-prod` |
| HashiCorp Vault | `vault kv put secret/kling ak=... sk=...` |
| 1Password CLI | `op item create --category login --title "Kling API"` |

```python
# Load from AWS Secrets Manager
import boto3
import json

def get_kling_credentials(secret_name="kling/prod"):
    client = boto3.client("secretsmanager")
    secret = client.get_secret_value(SecretId=secret_name)
    creds = json.loads(secret["SecretString"])
    return creds["access_key"], creds["secret_key"]
```

## Access Control Wrapper

```python
class TeamKlingClient:
    """Kling client with team-level access control."""

    def __init__(self, base_client, quota_manager: TeamQuotaManager):
        self.client = base_client
        self.quotas = quota_manager

    def text_to_video(self, email: str, prompt: str, **kwargs):
        model = kwargs.get("model", "kling-v2-master")
        credits = 10 if kwargs.get("mode") != "professional" else 35
        self.quotas.authorize(email, credits, model)

        result = self.client.text_to_video(prompt, **kwargs)
        self.quotas.record_usage(email, credits)
        return result
```

## Resources

- [API Key Management](https://app.klingai.com/global/dev/api-key)
- [Developer Portal](https://app.klingai.com/global/dev)
