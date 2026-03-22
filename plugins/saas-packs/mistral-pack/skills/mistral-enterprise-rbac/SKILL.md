---
name: mistral-enterprise-rbac
description: |
  Configure Mistral AI enterprise access control and workspace management.
  Use when implementing role-based API key scoping, managing team access,
  or setting up organization-level controls for Mistral AI.
  Trigger with phrases like "mistral access control", "mistral RBAC",
  "mistral enterprise", "mistral roles", "mistral team".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, mistral, rbac]

---
# Mistral AI Enterprise RBAC

## Overview
Control access to Mistral AI at the organization level using La Plateforme workspace management: scoped API keys per team, model access restrictions, spending limits, key auditing, and automated rotation. Mistral organizes access via **Organizations > Workspaces > API Keys**, with rate limits set at the workspace level.

## Prerequisites
- Mistral La Plateforme organization account ([console.mistral.ai](https://console.mistral.ai/))
- Organization admin or owner role
- Understanding of workspace vs key-level controls

## Instructions

### Step 1: Workspace Strategy

| Workspace | Team | Models Allowed | RPM | Monthly Budget |
|-----------|------|----------------|-----|----------------|
| dev-workspace | All developers | mistral-small, codestral | 60 | $50 |
| ml-workspace | ML engineers | All models | 200 | $500 |
| prod-workspace | CI/CD only | Per-service scoped | 500 | $2000 |

Create workspaces via La Plateforme console: Organization > Workspaces > Create.

### Step 2: Scoped API Keys per Team

Create keys with model restrictions and rate limits in the console, or via API:

```bash
set -euo pipefail
# Dev team — restricted to cost-effective models
curl -X POST https://api.mistral.ai/v1/api-keys \
  -H "Authorization: Bearer $MISTRAL_ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "dev-team-key",
    "description": "Dev team — small models only",
    "workspace_id": "ws_dev_xxx"
  }'

# ML team — full model access
curl -X POST https://api.mistral.ai/v1/api-keys \
  -H "Authorization: Bearer $MISTRAL_ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ml-team-key",
    "description": "ML team — all models",
    "workspace_id": "ws_ml_xxx"
  }'
```

### Step 3: Application-Level Model Gateway

Enforce model access in your application layer:

```typescript
const ROLE_PERMISSIONS: Record<string, {
  allowedModels: string[];
  maxTokensPerRequest: number;
  dailyTokenBudget: number;
}> = {
  analyst: {
    allowedModels: ['mistral-small-latest', 'mistral-embed'],
    maxTokensPerRequest: 500,
    dailyTokenBudget: 100_000,
  },
  developer: {
    allowedModels: ['mistral-small-latest', 'codestral-latest', 'mistral-embed'],
    maxTokensPerRequest: 2000,
    dailyTokenBudget: 500_000,
  },
  senior: {
    allowedModels: ['mistral-small-latest', 'mistral-large-latest', 'codestral-latest', 'mistral-embed'],
    maxTokensPerRequest: 4000,
    dailyTokenBudget: 1_000_000,
  },
  admin: {
    allowedModels: ['*'],
    maxTokensPerRequest: 8000,
    dailyTokenBudget: Infinity,
  },
};

function authorizeRequest(role: string, model: string, estimatedTokens: number): boolean {
  const perms = ROLE_PERMISSIONS[role];
  if (!perms) return false;

  const modelAllowed = perms.allowedModels.includes('*') || perms.allowedModels.includes(model);
  const tokensAllowed = estimatedTokens <= perms.maxTokensPerRequest;

  return modelAllowed && tokensAllowed;
}
```

### Step 4: Spending Limits

Configure in La Plateforme console: Organization > Billing > Budget Alerts.

```typescript
// Application-level budget enforcement
class SpendingGuard {
  private hourlySpend = 0;
  private hourStart = Date.now();
  private readonly maxHourlyUsd: number;

  constructor(maxHourlyUsd: number) {
    this.maxHourlyUsd = maxHourlyUsd;
  }

  recordCost(costUsd: number): void {
    if (Date.now() - this.hourStart > 3_600_000) {
      this.hourlySpend = 0;
      this.hourStart = Date.now();
    }
    this.hourlySpend += costUsd;
  }

  canSpend(estimatedCostUsd: number): boolean {
    return this.hourlySpend + estimatedCostUsd <= this.maxHourlyUsd;
  }
}
```

### Step 5: Key Audit

```bash
set -euo pipefail
# List all API keys with metadata
curl -s https://api.mistral.ai/v1/api-keys \
  -H "Authorization: Bearer $MISTRAL_ADMIN_KEY" | \
  jq '.data[] | {name, id, created_at, last_used_at}'

# Identify unused keys (not used in 30+ days)
curl -s https://api.mistral.ai/v1/api-keys \
  -H "Authorization: Bearer $MISTRAL_ADMIN_KEY" | \
  jq '.data[] | select(.last_used_at < (now - 2592000 | todate)) | {name, id, last_used_at}'
```

### Step 6: Automated Key Rotation

```typescript
// Rotate keys on a 90-day schedule
async function rotateApiKey(oldKeyId: string, keyName: string): Promise<string> {
  // 1. Create new key
  const newKey = await createApiKey({ name: `${keyName}-${Date.now()}` });

  // 2. Update consuming services (secret manager)
  await updateSecret('mistral-api-key', newKey.apiKey);

  // 3. Wait for propagation (services pick up new secret)
  await new Promise(r => setTimeout(r, 60_000));

  // 4. Verify new key works
  const client = new Mistral({ apiKey: newKey.apiKey });
  await client.models.list(); // throws if invalid

  // 5. Revoke old key
  await revokeApiKey(oldKeyId);

  console.log(`Rotated key: ${keyName} (old: ${oldKeyId}, new: ${newKey.id})`);
  return newKey.id;
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Key revoked or invalid | Regenerate on La Plateforme |
| `403 Model not allowed` | Key restricted from model | Use key with broader scope |
| `429 Rate limit` | Workspace RPM exceeded | Distribute across workspaces |
| Spending alert | Monthly budget near cap | Review per-key usage, restrict heavy consumers |

## Resources
- [La Plateforme Console](https://console.mistral.ai/)
- [Organizations & Workspaces](https://docs.mistral.ai/deployment/ai-studio/organization/)
- [Rate Limits & Tiers](https://docs.mistral.ai/deployment/ai-studio/tier/)

## Output
- Workspace-based team isolation
- Scoped API keys with model restrictions
- Application-level model access gateway
- Spending limits and budget alerts
- Key audit and rotation automation
