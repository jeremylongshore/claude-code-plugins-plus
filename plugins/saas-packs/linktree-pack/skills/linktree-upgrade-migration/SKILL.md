---
name: linktree-upgrade-migration
description: |
  Upgrade Migration for Linktree.
  Trigger: "linktree upgrade migration".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, linktree, social]
compatible-with: claude-code
---

# Linktree Upgrade & Migration

## Overview

Linktree provides a link-in-bio platform with APIs for managing profiles, links, and click analytics. The API exposes endpoints for CRUD operations on link trees, individual links, and analytics data. Tracking API changes is critical because Linktree's link schema evolves with new link types (commerce, scheduling, music), analytics response formats change with new metric dimensions, and profile customization fields expand — breaking integrations that sync link performance data to marketing dashboards or automate link management across multiple profiles.

## Version Detection

```typescript
const LINKTREE_BASE = "https://api.linktr.ee/v1";

async function detectLinktreeApiVersion(apiKey: string): Promise<void> {
  const res = await fetch(`${LINKTREE_BASE}/profile`, {
    headers: { Authorization: `Bearer ${apiKey}`, "Content-Type": "application/json" },
  });
  const version = res.headers.get("x-linktree-api-version") ?? "v1";
  console.log(`Linktree API version: ${version}`);

  // Check for deprecated link type fields
  const linksRes = await fetch(`${LINKTREE_BASE}/links`, {
    headers: { Authorization: `Bearer ${apiKey}` },
  });
  const data = await linksRes.json();
  const knownTypes = ["classic", "header", "music", "video", "commerce", "scheduling"];
  const activeTypes = [...new Set(data.links?.map((l: any) => l.type) ?? [])];
  const unknown = activeTypes.filter((t: string) => !knownTypes.includes(t));
  if (unknown.length) console.log(`New link types detected: ${unknown.join(", ")}`);
}
```

## Migration Checklist

- [ ] Review Linktree developer changelog for API breaking changes
- [ ] Audit codebase for hardcoded link type enums (new types may be added)
- [ ] Verify analytics endpoint response structure (metrics, dimensions, date ranges)
- [ ] Check profile customization fields for new appearance options
- [ ] Update link creation payload if required fields were added
- [ ] Test link ordering API — sort mechanism may have changed
- [ ] Validate thumbnail/image upload endpoints for size or format changes
- [ ] Check OAuth token scopes if new permissions required for analytics
- [ ] Update webhook handlers for link click and profile view events
- [ ] Run analytics data export and compare old vs. new response shapes

## Schema Migration

```typescript
// Linktree links evolved: simple URL → typed link with metadata
interface OldLink {
  id: string;
  title: string;
  url: string;
  position: number;
  active: boolean;
}

interface NewLink {
  id: string;
  title: string;
  url: string;
  type: "classic" | "header" | "music" | "video" | "commerce" | "scheduling";
  position: number;
  active: boolean;
  metadata: {
    thumbnail_url?: string;
    schedule?: { start: string; end: string };
    price?: { amount: number; currency: string };
  };
  analytics: { total_clicks: number; unique_clicks: number };
}

function migrateLink(old: OldLink): NewLink {
  return {
    ...old,
    type: "classic",
    metadata: {},
    analytics: { total_clicks: 0, unique_clicks: 0 },
  };
}
```

## Rollback Strategy

```typescript
class LinktreeClient {
  private version: "v1" | "v2";

  constructor(private apiKey: string, version: "v1" | "v2" = "v2") {
    this.version = version;
  }

  async getLinks(): Promise<any> {
    try {
      const res = await fetch(`https://api.linktr.ee/${this.version}/links`, {
        headers: { Authorization: `Bearer ${this.apiKey}` },
      });
      if (!res.ok) throw new Error(`Linktree ${res.status}`);
      return await res.json();
    } catch (err) {
      if (this.version === "v2") {
        console.warn("Falling back to Linktree API v1");
        this.version = "v1";
        return this.getLinks();
      }
      throw err;
    }
  }
}
```

## Error Handling

| Migration Issue | Symptom | Fix |
|----------------|---------|-----|
| Link type enum expanded | `400` when filtering by type with old enum values | Fetch current types from `/link-types` and update filter logic |
| Analytics response restructured | `undefined` accessing `link.clicks` (now `link.analytics.total_clicks`) | Update property paths to new nested analytics object |
| Profile field renamed | `avatar_url` returns `null`, now `profile_image_url` | Update all references to use new field name |
| Thumbnail upload format changed | `415 Unsupported Media Type` on image upload | Check supported formats via `/upload/formats` endpoint |
| Rate limit per-endpoint | `429` on analytics but not links | Implement per-endpoint rate limiting instead of global |

## Resources

- [Linktree Developer Portal](https://linktr.ee/marketplace/developer)
- [Linktree API Documentation](https://developers.linktr.ee/)

## Next Steps

For CI pipeline integration, see `linktree-ci-integration`.
