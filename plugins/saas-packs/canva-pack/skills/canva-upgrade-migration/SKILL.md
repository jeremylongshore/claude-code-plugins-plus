---
name: canva-upgrade-migration
description: |
  Plan and execute Canva Connect API version upgrades and breaking change detection.
  Use when Canva releases API changes, migrating brand template IDs,
  or adapting to endpoint deprecations.
  Trigger with phrases like "upgrade canva", "canva API changes",
  "canva breaking changes", "canva deprecation", "canva changelog".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, canva]
compatible-with: claude-code
---

# Canva Upgrade & Migration

## Overview

Guide for handling Canva Connect API changes. Canva uses a single REST API version (`/rest/v1/`) but evolves endpoints over time. Monitor the [changelog](https://www.canva.dev/docs/connect/changelog/) for breaking changes.

## Known Migrations

### Brand Template ID Migration (September 2025)

Canva migrated brand templates to a new ID format. Old IDs accepted for 6 months.

```typescript
// Check if your stored template IDs need updating
async function migrateBrandTemplateIds(
  db: Database, token: string
): Promise<{ migrated: number; failed: string[] }> {
  const stored = await db.getBrandTemplateIds();
  let migrated = 0;
  const failed: string[] = [];

  // Fetch current templates from Canva
  const { items } = await canvaAPI('/brand-templates', token);
  const currentIds = new Set(items.map((t: any) => t.id));

  for (const oldId of stored) {
    if (!currentIds.has(oldId)) {
      // Old ID — try to find matching template by title
      const match = items.find((t: any) => t.title === await db.getTemplateName(oldId));
      if (match) {
        await db.updateTemplateId(oldId, match.id);
        migrated++;
      } else {
        failed.push(oldId);
      }
    }
  }

  return { migrated, failed };
}
```

### Comment API Migration

The Comment API endpoints were refactored — `Create Comment` and `Create Reply` are deprecated in favor of `Create Thread` and `Create Reply (v2)`.

```typescript
// OLD (deprecated)
// POST /v1/designs/{id}/comments — deprecated

// NEW
// POST /v1/designs/{id}/comment_threads — Create Thread
// POST /v1/designs/{id}/comment_threads/{threadId}/replies — Create Reply
```

## Pre-Upgrade Assessment

```typescript
async function assessCanvaIntegration(token: string): Promise<void> {
  const checks = [
    { name: 'Users API', path: '/users/me' },
    { name: 'Designs List', path: '/designs?limit=1' },
    { name: 'Brand Templates', path: '/brand-templates?limit=1' },
    { name: 'Exports', path: '/exports' },  // Will 405 (POST only) but confirms route exists
  ];

  for (const check of checks) {
    try {
      const res = await fetch(`https://api.canva.com/rest/v1${check.path}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      console.log(`[${res.ok || res.status === 405 ? 'OK' : 'WARN'}] ${check.name}: HTTP ${res.status}`);
    } catch (e: any) {
      console.log(`[FAIL] ${check.name}: ${e.message}`);
    }
  }
}
```

## Breaking Change Detection

```typescript
// Monitor API responses for deprecation signals
function checkForDeprecationWarnings(response: Response, endpoint: string): void {
  const deprecation = response.headers.get('Deprecation');
  const sunset = response.headers.get('Sunset');
  const link = response.headers.get('Link');

  if (deprecation) {
    console.warn(`[DEPRECATION] ${endpoint}: deprecated=${deprecation}, sunset=${sunset}`);
    console.warn(`  Migration guide: ${link}`);
    // Alert ops team
  }
}
```

## Upgrade Branch Workflow

```bash
# 1. Create upgrade branch
git checkout -b upgrade/canva-api-changes

# 2. Check Canva changelog for breaking changes
# https://www.canva.dev/docs/connect/changelog/

# 3. Download latest OpenAPI spec for diff
curl -o openapi-new.yml https://www.canva.dev/sources/connect/api/latest/api.yml
diff openapi-old.yml openapi-new.yml | head -100

# 4. Run integration tests against staging
CANVA_ACCESS_TOKEN=$STAGING_TOKEN npm test

# 5. Deploy to staging first
# 6. Monitor for 24 hours before production
```

## Rollback Procedure

```typescript
// Feature-flag controlled rollback
const USE_NEW_COMMENT_API = process.env.CANVA_NEW_COMMENT_API === 'true';

async function createComment(designId: string, message: string, token: string) {
  if (USE_NEW_COMMENT_API) {
    return canvaAPI(`/designs/${designId}/comment_threads`, token, {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
  }
  // Fallback to deprecated endpoint during transition
  return canvaAPI(`/designs/${designId}/comments`, token, {
    method: 'POST',
    body: JSON.stringify({ message }),
  });
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| 404 on endpoint | Endpoint removed or renamed | Check changelog for replacement |
| Old template IDs fail | ID format migration | Re-fetch template list |
| Deprecated header | Endpoint sunsetting | Migrate to replacement |
| Response schema changed | New/removed fields | Update Zod schemas, add optional chaining |

## Resources

- [Canva Changelog](https://www.canva.dev/docs/connect/changelog/)
- [OpenAPI Spec](https://www.canva.dev/sources/connect/api/latest/api.yml)
- [Canva API Reference](https://www.canva.dev/docs/connect/api-reference/)

## Next Steps

For CI integration during upgrades, see `canva-ci-integration`.
