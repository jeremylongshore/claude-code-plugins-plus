---
name: mistral-enterprise-rbac
description: |
  Configure Mistral AI enterprise access control and organization management.
  Use when implementing role-based permissions, managing team access,
  or setting up organization-level controls for Mistral AI.
  Trigger with phrases like "mistral access control", "mistral RBAC",
  "mistral enterprise", "mistral roles", "mistral permissions", "mistral team".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Mistral AI Enterprise RBAC

## Overview
Control access to Mistral AI models and API resources at the organization level. Mistral uses API key scoping and La Plateforme workspace management to separate environments. Access is governed through organization membership, API key permissions, and model-level restrictions that determine which team members can call which endpoints.

## Prerequisites
- Mistral La Plateforme organization account
- Organization admin or owner role
- At least one active API key with admin scope

## Instructions

### Step 1: Create Scoped API Keys per Team
```bash
# Create a key restricted to small models only (cost-safe for junior devs)
curl -X POST https://api.mistral.ai/v1/api-keys \
  -H "Authorization: Bearer $MISTRAL_ADMIN_KEY" \
  -d '{
    "name": "dev-team-small-only",
    "allowed_models": ["mistral-small-latest", "codestral-latest"],
    "rate_limit_rpm": 100
  }'

# Create an unrestricted key for the ML team
curl -X POST https://api.mistral.ai/v1/api-keys \
  -H "Authorization: Bearer $MISTRAL_ADMIN_KEY" \
  -d '{
    "name": "ml-team-full-access",
    "allowed_models": ["mistral-small-latest", "mistral-large-latest", "mistral-embed"],
    "rate_limit_rpm": 500
  }'
```

### Step 2: Implement a Gateway That Enforces Roles
```typescript
// mistral-gateway.ts - Proxy that checks roles before forwarding
const ROLE_MODEL_MAP: Record<string, string[]> = {
  analyst:   ['mistral-small-latest'],
  developer: ['mistral-small-latest', 'codestral-latest', 'mistral-embed'],
  senior:    ['mistral-small-latest', 'mistral-large-latest', 'mistral-embed'],
  admin:     ['*'],
};

function canUseModel(role: string, model: string): boolean {
  const allowed = ROLE_MODEL_MAP[role];
  return allowed?.includes('*') || allowed?.includes(model) || false;
}
```

### Step 3: Set Workspace Spending Limits
Navigate to La Plateforme > Organization > Billing and set monthly budget caps. Configure alerts at 50%, 80%, and 95% thresholds. Each API key can also have independent rate limits to prevent a single integration from consuming the entire budget.

### Step 4: Audit API Key Usage
```bash
# List all API keys and their last-used timestamps
curl https://api.mistral.ai/v1/api-keys \
  -H "Authorization: Bearer $MISTRAL_ADMIN_KEY" | \
  jq '.data[] | {name, created_at, last_used_at, allowed_models}'

# Revoke a compromised key
curl -X DELETE https://api.mistral.ai/v1/api-keys/key_abc123 \
  -H "Authorization: Bearer $MISTRAL_ADMIN_KEY"
```

### Step 5: Rotate Keys on Schedule
Automate 90-day key rotation. Create the new key, update consuming services, then delete the old key after a 24-hour overlap window.

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | API key revoked or invalid | Generate new key on La Plateforme |
| `403 model not allowed` | Key restricted from that model | Use a key with broader model scope |
| `429 rate limit` | Key RPM cap exceeded | Increase rate limit or distribute load across keys |
| Spending alert triggered | Monthly budget near cap | Review usage by key; restrict heavy consumers |

## Examples
```bash
# Quick check: which models can this key access?
curl https://api.mistral.ai/v1/models \
  -H "Authorization: Bearer $MISTRAL_API_KEY" | \
  jq '.data[].id'
```

```bash
# Rotate a key with zero-downtime overlap
NEW_KEY=$(curl -s -X POST https://api.mistral.ai/v1/api-keys \
  -H "Authorization: Bearer $MISTRAL_ADMIN_KEY" \
  -d '{"name": "service-v2", "allowed_models": ["mistral-small-latest"]}' | jq -r '.key')
echo "Deploy NEW_KEY=$NEW_KEY to services, then delete old key after 24h"
```
