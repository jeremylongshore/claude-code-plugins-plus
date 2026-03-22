---
name: anth-enterprise-rbac
description: |
  Configure Anthropic enterprise organization management, Workspaces,
  and role-based access control for teams.
  Trigger with phrases like "anthropic enterprise", "claude rbac",
  "anthropic workspaces", "claude team access", "anthropic organization".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, anthropic]
compatible-with: claude-code
---

# Anthropic Enterprise RBAC

## Overview

Anthropic provides organization-level access control through Workspaces, API key scoping, and member roles via the Console at [console.anthropic.com](https://console.anthropic.com).

## Organization Structure

```
Organization (billing entity)
├── Workspace: Production
│   ├── API Key: sk-ant-api03-prod-main-...
│   ├── API Key: sk-ant-api03-prod-batch-...
│   └── Rate limits: Tier 4
├── Workspace: Staging
│   ├── API Key: sk-ant-api03-stg-...
│   └── Rate limits: Tier 2
└── Workspace: Development
    ├── API Key: sk-ant-api03-dev-...
    └── Rate limits: Tier 1
```

## Console Roles

| Role | Capabilities |
|------|-------------|
| Owner | Full access, billing, member management |
| Admin | Manage workspaces, API keys, view usage |
| Developer | Create/revoke own API keys, view own usage |
| Billing | View invoices and usage reports only |

## Application-Level RBAC

```python
# Implement your own RBAC on top of Anthropic Workspaces
from enum import Enum
import anthropic

class UserRole(Enum):
    VIEWER = "viewer"       # Can read Claude responses (no direct API)
    USER = "user"           # Can send prompts (rate limited)
    POWER_USER = "power"    # Can use Opus, higher limits
    ADMIN = "admin"         # Can access all models, no limits

ROLE_CONFIG = {
    UserRole.VIEWER: {"allowed": False},
    UserRole.USER: {
        "allowed": True,
        "models": ["claude-haiku-4-20250514"],
        "max_tokens": 512,
        "rpm_limit": 10,
    },
    UserRole.POWER_USER: {
        "allowed": True,
        "models": ["claude-haiku-4-20250514", "claude-sonnet-4-20250514", "claude-opus-4-20250514"],
        "max_tokens": 4096,
        "rpm_limit": 60,
    },
    UserRole.ADMIN: {
        "allowed": True,
        "models": ["claude-haiku-4-20250514", "claude-sonnet-4-20250514", "claude-opus-4-20250514"],
        "max_tokens": 8192,
        "rpm_limit": 200,
    },
}

def create_message(user_role: UserRole, model: str, **kwargs):
    config = ROLE_CONFIG[user_role]
    if not config["allowed"]:
        raise PermissionError("Role does not allow API access")
    if model not in config["models"]:
        raise PermissionError(f"Role cannot access model: {model}")
    kwargs["max_tokens"] = min(kwargs.get("max_tokens", 1024), config["max_tokens"])

    client = anthropic.Anthropic()
    return client.messages.create(model=model, **kwargs)
```

## Key Management Best Practices

| Practice | Implementation |
|----------|---------------|
| One key per service | `prod-auth-service`, `prod-search-service` |
| Rotate quarterly | Calendar reminder + automated rotation |
| Least privilege | Dev workspace for dev keys only |
| Audit trail | Log which key made each request |
| Revoke immediately | On employee departure or compromise |

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| Key works in dev, fails in prod | Wrong workspace key | Verify key belongs to prod workspace |
| New team member can't access | Not added to workspace | Invite via Console > Members |
| Usage not visible | Viewing wrong workspace | Switch workspace in Console |

## Resources

- [Console](https://console.anthropic.com)
- [Workspaces](https://docs.anthropic.com/en/docs/administration/workspaces)

## Next Steps

For major migration strategies, see `anth-migration-deep-dive`.
