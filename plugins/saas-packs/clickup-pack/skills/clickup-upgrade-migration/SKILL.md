---
name: clickup-upgrade-migration
description: |
  Migrate between ClickUp API versions (v2 to v3) and handle breaking changes.
  Use when upgrading API versions, adapting to endpoint changes,
  or migrating between ClickUp plan tiers.
  Trigger: "upgrade clickup API", "clickup v2 to v3", "clickup breaking changes",
  "clickup API migration", "clickup deprecation".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, clickup]
compatible-with: claude-code
---

# ClickUp Upgrade & Migration

## Overview

Guide for migrating between ClickUp API versions. API v2 is the current stable version (`/api/v2/`). API v3 endpoints are gradually being introduced with terminology and structural changes.

## Key v2 vs v3 Terminology Changes

| Concept | API v2 Term | API v3 Term |
|---------|-------------|-------------|
| Workspace | Team (`team_id`) | Workspace (`workspace_id`) |
| User Group | Team | Group (`group_id`) |
| Get workspaces | `GET /team` | `GET /v3/workspaces` |

## Pre-Migration Assessment

```bash
#!/bin/bash
# Audit current ClickUp API usage
echo "=== ClickUp API Usage Audit ==="

# Find all API v2 calls in codebase
echo "API v2 endpoints found:"
grep -rn "api/v2/" src/ --include="*.ts" --include="*.js" | \
  sed 's/.*api\/v2\///' | cut -d'"' -f1 | cut -d"'" -f1 | \
  sort | uniq -c | sort -rn

# Count unique endpoints
echo ""
echo "Unique endpoints:"
grep -rohn "api/v2/[a-z_/]*" src/ --include="*.ts" | sort -u

# Check for deprecated patterns
echo ""
echo "Deprecated patterns:"
grep -rn "team_id\|getauthorizedteams" src/ --include="*.ts" -i || echo "  None found"
```

## Migration Strategy: Adapter Pattern

```typescript
// src/clickup/adapter.ts
// Abstract away API version so you can swap v2 -> v3 per-endpoint

interface ClickUpAdapter {
  getWorkspaces(): Promise<Workspace[]>;
  getSpaces(workspaceId: string): Promise<Space[]>;
  createTask(listId: string, task: CreateTaskInput): Promise<Task>;
}

class ClickUpV2Adapter implements ClickUpAdapter {
  async getWorkspaces() {
    const data = await this.request('/team');
    return data.teams.map((t: any) => ({ id: t.id, name: t.name }));
  }

  async getSpaces(workspaceId: string) {
    const data = await this.request(`/team/${workspaceId}/space`);
    return data.spaces;
  }

  async createTask(listId: string, task: CreateTaskInput) {
    return this.request(`/list/${listId}/task`, {
      method: 'POST',
      body: JSON.stringify(task),
    });
  }

  private async request(path: string, options?: RequestInit) {
    const res = await fetch(`https://api.clickup.com/api/v2${path}`, {
      ...options,
      headers: {
        'Authorization': process.env.CLICKUP_API_TOKEN!,
        'Content-Type': 'application/json',
      },
    });
    return res.json();
  }
}

// When v3 endpoints are available, add:
class ClickUpV3Adapter implements ClickUpAdapter {
  async getWorkspaces() {
    // v3 uses /v3/workspaces instead of /v2/team
    const data = await this.request('/workspaces');
    return data.workspaces;
  }
  // ... implement other methods with v3 endpoints
}
```

## Feature Flag for Gradual Migration

```typescript
function getAdapter(): ClickUpAdapter {
  const useV3 = process.env.CLICKUP_API_V3 === 'true';
  return useV3 ? new ClickUpV3Adapter() : new ClickUpV2Adapter();
}

// All calling code uses the adapter interface
const adapter = getAdapter();
const workspaces = await adapter.getWorkspaces();
```

## Testing Migration

```typescript
import { describe, it, expect } from 'vitest';

describe('API Version Migration', () => {
  const adapters = [
    { name: 'v2', adapter: new ClickUpV2Adapter() },
    // Uncomment when v3 adapter is ready:
    // { name: 'v3', adapter: new ClickUpV3Adapter() },
  ];

  adapters.forEach(({ name, adapter }) => {
    it(`${name}: returns workspaces with id and name`, async () => {
      const workspaces = await adapter.getWorkspaces();
      expect(workspaces[0]).toHaveProperty('id');
      expect(workspaces[0]).toHaveProperty('name');
    });
  });
});
```

## Rollback Procedure

```bash
# If v3 migration causes issues:
# 1. Set feature flag back to v2
export CLICKUP_API_V3=false

# 2. Verify v2 still works
curl -sf https://api.clickup.com/api/v2/user \
  -H "Authorization: $CLICKUP_API_TOKEN" | jq '.user.username'

# 3. Redeploy with v2 adapter
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Endpoint 404 | v3 endpoint not yet available | Fall back to v2 equivalent |
| Field name mismatch | v3 changed response shape | Update type definitions |
| `team_id` not recognized | v3 expects `workspace_id` | Use adapter to translate |

## Resources

- [ClickUp API v2/v3 Terminology](https://developer.clickup.com/docs/general-v2-v3-api)
- [ClickUp Developer Portal](https://developer.clickup.com/)
- [ClickUp API FAQ](https://developer.clickup.com/docs/faq)

## Next Steps

For CI integration during upgrades, see `clickup-ci-integration`.
