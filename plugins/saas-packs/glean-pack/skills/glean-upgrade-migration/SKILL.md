---
name: glean-upgrade-migration
description: 'Check Glean developer changelog for API changes.

  Trigger: "glean upgrade migration", "upgrade-migration".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- enterprise-search
- glean
compatibility: Designed for Claude Code
---
# Glean Upgrade & Migration

## Overview

Glean is an enterprise search platform that indexes documents across SaaS tools via connectors and exposes Search and Indexing APIs. Migrations involve connector schema changes, search API response format updates, and document permission model upgrades. Tracking API versions is critical because Glean's Indexing API enforces document schema validation — adding required fields or changing permission structures in a new version will cause bulk indexing failures and stale search results if connectors are not updated in lockstep.

## Version Detection

```typescript
const GLEAN_BASE = "https://your-domain-be.glean.com/api";

async function detectGleanApiVersion(apiToken: string): Promise<void> {
  // Check indexing API health and version
  const indexRes = await fetch(`${GLEAN_BASE}/index/v1/status`, {
    headers: { Authorization: `Bearer ${apiToken}`, "Content-Type": "application/json" },
  });
  const indexStatus = await indexRes.json();
  console.log(`Indexing API version: ${indexRes.headers.get("x-glean-api-version") ?? "v1"}`);
  console.log(`Connector status: ${JSON.stringify(indexStatus.connectors)}`);

  // Check search API for deprecated query parameters
  const searchRes = await fetch(`${GLEAN_BASE}/client/v1/search`, {
    method: "POST",
    headers: { Authorization: `Bearer ${apiToken}`, "Content-Type": "application/json" },
    body: JSON.stringify({ query: "test", pageSize: 1 }),
  });
  const deprecationHeader = searchRes.headers.get("x-glean-deprecated-params");
  if (deprecationHeader) console.warn(`Deprecated parameters: ${deprecationHeader}`);
}
```

## Migration Checklist

- [ ] Review Glean developer changelog for Indexing API schema changes
- [ ] Audit custom connectors for deprecated document fields
- [ ] Verify `objectType` definitions match current Glean schema requirements
- [ ] Check if new required fields were added to document permission model
- [ ] Test search API response parsing — `results[].snippets` format may change
- [ ] Update datasource configuration if connector authentication method changed
- [ ] Validate bulk indexing with a small document batch before full re-index
- [ ] Check `people` API for identity resolution field changes
- [ ] Update search query syntax if faceted search operators were modified
- [ ] Monitor indexing error dashboard for 48 hours post-migration

## Schema Migration

```typescript
// Glean document schema evolved: flat permissions → structured ACL model
interface OldGleanDocument {
  id: string;
  datasource: string;
  title: string;
  body: { mimeType: string; textContent: string };
  permissions: { allowedUsers: string[] };
  updatedAt: string;
}

interface NewGleanDocument {
  id: string;
  datasource: string;
  title: string;
  body: { mimeType: string; textContent: string };
  permissions: {
    allowedUsers: Array<{ email: string; datasourceUserId?: string }>;
    allowedGroups: Array<{ name: string; datasourceGroupId?: string }>;
    allowAnonymousAccess: boolean;
  };
  viewURL: string;
  updatedAt: string;
}

function migrateDocument(old: OldGleanDocument): NewGleanDocument {
  return {
    ...old,
    permissions: {
      allowedUsers: old.permissions.allowedUsers.map((email) => ({ email })),
      allowedGroups: [],
      allowAnonymousAccess: false,
    },
    viewURL: `https://app.example.com/doc/${old.id}`,
  };
}
```

## Rollback Strategy

```typescript
class GleanIndexClient {
  constructor(
    private token: string,
    private baseUrl: string,
    private apiVersion: "v1" | "v2" = "v2"
  ) {}

  async indexDocuments(docs: any[]): Promise<any> {
    try {
      const res = await fetch(`${this.baseUrl}/index/${this.apiVersion}/indexdocuments`, {
        method: "POST",
        headers: { Authorization: `Bearer ${this.token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ documents: docs }),
      });
      if (!res.ok) throw new Error(`Glean indexing ${res.status}: ${await res.text()}`);
      return await res.json();
    } catch (err) {
      if (this.apiVersion === "v2") {
        console.warn("Falling back to Glean Indexing API v1");
        this.apiVersion = "v1";
        return this.indexDocuments(docs);
      }
      throw err;
    }
  }
}
```

## Error Handling

| Migration Issue | Symptom | Fix |
|----------------|---------|-----|
| Document schema validation failure | `400` with `missing required field: viewURL` | Add `viewURL` to all documents before re-indexing |
| Permission model mismatch | Documents indexed but not searchable by expected users | Migrate flat `allowedUsers` strings to structured user objects |
| Connector auth expired | `401 Unauthorized` on bulk index | Rotate API token in Glean admin and update connector config |
| Search response format changed | Client crashes parsing `snippets` as string instead of array | Handle both `string` and `Snippet[]` return types |
| Datasource quota exceeded | `429` during bulk re-index | Implement rate limiting with exponential backoff per Glean docs |

## Resources

- [Glean Developer Portal](https://developers.glean.com/)
- [Indexing API](https://developers.glean.com/api-info/indexing/getting-started/overview)
- [Search API](https://developers.glean.com/api/client-api/search/overview)
- [Glean Changelog](https://developers.glean.com/changelog)

## Next Steps

For CI pipeline integration, see `glean-ci-integration`.
