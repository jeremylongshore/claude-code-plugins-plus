---
name: juicebox-upgrade-migration
description: |
  Plan Juicebox SDK upgrades.
  Trigger: "upgrade juicebox", "juicebox migration".
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, recruiting, juicebox]
compatible-with: claude-code
---

# Juicebox Upgrade & Migration

## Overview

Juicebox is an AI-powered people search and analysis platform used for recruiting and market research. The API provides endpoints for dataset management, people searches, and AI-generated analyses. Tracking API versions is essential because Juicebox evolves its search query syntax, dataset schema, and analysis output format — upgrading without testing can break saved search filters, corrupt dataset imports, and change the structure of AI-generated candidate profiles that downstream systems consume.

## Version Detection

```typescript
const JUICEBOX_BASE = "https://api.juicebox.work/v1";

async function detectJuiceboxVersion(apiKey: string): Promise<void> {
  const res = await fetch(`${JUICEBOX_BASE}/datasets`, {
    headers: { Authorization: `Bearer ${apiKey}`, "Content-Type": "application/json" },
  });
  const version = res.headers.get("x-juicebox-api-version") ?? "v1";
  console.log(`Juicebox API version: ${version}`);

  // Check for deprecated search parameters
  const searchRes = await fetch(`${JUICEBOX_BASE}/search`, {
    method: "POST",
    headers: { Authorization: `Bearer ${apiKey}`, "Content-Type": "application/json" },
    body: JSON.stringify({ query: "test", limit: 1 }),
  });
  const deprecation = searchRes.headers.get("x-deprecated-params");
  if (deprecation) console.warn(`Deprecated search params: ${deprecation}`);
}
```

## Migration Checklist

- [ ] Review Juicebox changelog for API breaking changes
- [ ] Audit codebase for hardcoded dataset field names
- [ ] Verify search query syntax — filter operators may have changed
- [ ] Check analysis output format for new or renamed fields
- [ ] Update dataset import schema if column mapping changed
- [ ] Test people search result structure (profile fields, enrichment data)
- [ ] Validate pagination — cursor-based vs. offset may have changed
- [ ] Update SDK version in `package.json` and verify type compatibility
- [ ] Check webhook payloads for analysis completion events
- [ ] Run integration tests with sample dataset to verify search quality

## Schema Migration

```typescript
// Juicebox search results evolved: flat profile → enriched profile with sources
interface OldSearchResult {
  id: string;
  name: string;
  title: string;
  company: string;
  email?: string;
  linkedin_url?: string;
}

interface NewSearchResult {
  id: string;
  profile: {
    full_name: string;
    current_title: string;
    current_company: { name: string; domain: string };
    emails: Array<{ address: string; type: "work" | "personal"; verified: boolean }>;
    social: { linkedin?: string; twitter?: string };
  };
  match_score: number;
  enrichment_sources: string[];
}

function migrateSearchResult(old: OldSearchResult): NewSearchResult {
  return {
    id: old.id,
    profile: {
      full_name: old.name,
      current_title: old.title,
      current_company: { name: old.company, domain: "" },
      emails: old.email ? [{ address: old.email, type: "work", verified: false }] : [],
      social: { linkedin: old.linkedin_url },
    },
    match_score: 0,
    enrichment_sources: [],
  };
}
```

## Rollback Strategy

```typescript
class JuiceboxClient {
  private currentVersion: "v1" | "v2";

  constructor(private apiKey: string, version: "v1" | "v2" = "v2") {
    this.currentVersion = version;
  }

  async search(query: string, filters?: Record<string, any>): Promise<any> {
    try {
      const res = await fetch(`https://api.juicebox.work/${this.currentVersion}/search`, {
        method: "POST",
        headers: { Authorization: `Bearer ${this.apiKey}`, "Content-Type": "application/json" },
        body: JSON.stringify({ query, filters }),
      });
      if (!res.ok) throw new Error(`Juicebox search ${res.status}`);
      return await res.json();
    } catch (err) {
      if (this.currentVersion === "v2") {
        console.warn("Falling back to Juicebox API v1");
        this.currentVersion = "v1";
        return this.search(query, filters);
      }
      throw err;
    }
  }
}
```

## Error Handling

| Migration Issue | Symptom | Fix |
|----------------|---------|-----|
| Search filter syntax changed | `400 Bad Request` with `invalid filter operator` | Update filter syntax to new query DSL format |
| Dataset schema mismatch | Import succeeds but columns mapped incorrectly | Re-map dataset columns using `/datasets/schema` endpoint |
| Profile field restructured | Code crashes accessing `result.name` (now `result.profile.full_name`) | Update all property access paths to new nested structure |
| Analysis format changed | AI analysis output missing expected sections | Update parser for new structured analysis response |
| Rate limit reduced | `429 Too Many Requests` on previously working batch sizes | Reduce batch size and implement request queuing |

## Resources

- [Juicebox Changelog](https://docs.juicebox.work/changelog)
- [Juicebox API Documentation](https://docs.juicebox.work/api)

## Next Steps

For CI pipeline integration, see `juicebox-ci-integration`.
