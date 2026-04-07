---
name: lucidchart-upgrade-migration
description: |
  Upgrade Migration for Lucidchart.
  Trigger: "lucidchart upgrade migration".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, lucidchart, diagramming]
compatible-with: claude-code
---

# Lucidchart Upgrade & Migration

## Overview

Lucidchart (Lucid) provides a diagramming and visual collaboration platform with APIs for document management, shape manipulation, and data linking. The API uses version headers and evolves its document schema, shape library definitions, and permission models. Tracking API versions is critical because Lucid's document format changes affect embedded diagram exports, shape coordinate systems shift between API versions, and breaking changes to the data linking API can corrupt live-data diagrams connected to external databases.

## Version Detection

```typescript
const LUCID_BASE = "https://api.lucid.co/v1";

async function detectLucidApiVersion(apiKey: string): Promise<void> {
  const res = await fetch(`${LUCID_BASE}/documents`, {
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Lucid-Api-Version": "2",
      "Content-Type": "application/json",
    },
  });
  const serverVersion = res.headers.get("x-lucid-api-version") ?? "unknown";
  const minSupported = res.headers.get("x-lucid-min-version");
  console.log(`Lucid API version: ${serverVersion}, min supported: ${minSupported}`);

  // Check if current version header is being accepted or forced up
  const requestedVersion = "2";
  if (serverVersion !== requestedVersion) {
    console.warn(`Requested v${requestedVersion} but server responded with v${serverVersion}`);
  }

  const deprecation = res.headers.get("x-lucid-deprecation-notice");
  if (deprecation) console.warn(`Deprecation: ${deprecation}`);
}
```

## Migration Checklist

- [ ] Review Lucid developer changelog for API version bumps
- [ ] Update `Lucid-Api-Version` header in all API calls to target version
- [ ] Audit document export code — SVG/PNG render parameters may change
- [ ] Verify shape library IDs are still valid (deprecated shapes removed)
- [ ] Check document permission model for new sharing/access level fields
- [ ] Update data linking configuration if external data source schema changed
- [ ] Test page/layer structure — nested page support may affect document queries
- [ ] Validate webhook event payloads for document change notifications
- [ ] Check if coordinate system units changed (points vs. pixels)
- [ ] Run export comparison: render same document with old and new API versions

## Schema Migration

```typescript
// Lucid document schema: flat shape list → page-grouped shape hierarchy
interface OldDocument {
  id: string;
  title: string;
  shapes: Array<{ id: string; type: string; x: number; y: number; width: number; height: number; text?: string }>;
  lastModified: string;
}

interface NewDocument {
  id: string;
  title: string;
  pages: Array<{
    id: string;
    title: string;
    layers: Array<{
      id: string;
      shapes: Array<{
        id: string;
        type: string;
        bounds: { x: number; y: number; width: number; height: number };
        text?: { content: string; style: Record<string, any> };
      }>;
    }>;
  }>;
  lastModified: string;
  version: number;
}

function migrateDocument(old: OldDocument): NewDocument {
  return {
    id: old.id,
    title: old.title,
    pages: [{
      id: "page-1",
      title: "Page 1",
      layers: [{
        id: "layer-1",
        shapes: old.shapes.map((s) => ({
          id: s.id,
          type: s.type,
          bounds: { x: s.x, y: s.y, width: s.width, height: s.height },
          text: s.text ? { content: s.text, style: {} } : undefined,
        })),
      }],
    }],
    lastModified: old.lastModified,
    version: 2,
  };
}
```

## Rollback Strategy

```typescript
class LucidClient {
  private apiVersion: number;

  constructor(private apiKey: string, version: number = 2) {
    this.apiVersion = version;
  }

  async getDocument(docId: string): Promise<any> {
    try {
      const res = await fetch(`https://api.lucid.co/v1/documents/${docId}`, {
        headers: {
          Authorization: `Bearer ${this.apiKey}`,
          "Lucid-Api-Version": String(this.apiVersion),
        },
      });
      if (!res.ok) throw new Error(`Lucid API ${res.status}`);
      return await res.json();
    } catch (err) {
      if (this.apiVersion > 1) {
        console.warn(`Falling back Lucid API from v${this.apiVersion} to v${this.apiVersion - 1}`);
        this.apiVersion -= 1;
        return this.getDocument(docId);
      }
      throw err;
    }
  }
}
```

## Error Handling

| Migration Issue | Symptom | Fix |
|----------------|---------|-----|
| API version header missing | `400` with `Lucid-Api-Version header required` | Add `Lucid-Api-Version` header to all requests |
| Shape ID format changed | `404` when referencing shapes by old numeric ID | Migrate to new UUID-based shape identifiers |
| Document export dimensions wrong | SVG exports render at unexpected scale | Check if coordinate units changed from points to pixels in new version |
| Data link schema invalid | `422` on data linking update | Re-map external data columns to new document field schema |
| Permission model expanded | `403` on previously accessible documents | Request updated OAuth scopes for new permission levels |

## Resources

- [Lucid Developer Portal](https://developer.lucid.co/reference/overview)
- [Lucid API Changelog](https://developer.lucid.co/changelog)

## Next Steps

For CI pipeline integration, see `lucidchart-ci-integration`.
