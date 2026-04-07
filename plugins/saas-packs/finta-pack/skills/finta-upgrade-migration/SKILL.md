---
name: finta-upgrade-migration
description: |
  Handle Finta platform updates and data migration.
  Trigger with phrases like "finta upgrade", "finta migration".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, fundraising-crm, investor-management, finta]
compatible-with: claude-code
---

# Finta Upgrade & Migration

## Overview

Finta is a fundraising CRM built for founders managing investor pipelines, deal rooms, and investor updates. The API exposes endpoints for funding rounds, investor contacts, and deal room documents. Tracking API changes matters because Finta evolves its data model around fundraising workflows — field renames in round stages, investor contact schema updates, and deal room permission changes can break integrations that sync pipeline data to external analytics or reporting tools.

## Version Detection

```typescript
const FINTA_BASE = "https://api.trustfinta.com/v1";

async function detectFintaApiVersion(apiKey: string): Promise<void> {
  const res = await fetch(`${FINTA_BASE}/rounds`, {
    headers: { Authorization: `Bearer ${apiKey}`, "Content-Type": "application/json" },
  });
  const data = await res.json();
  const apiVersion = res.headers.get("x-finta-version") ?? "unknown";
  console.log(`Finta API version: ${apiVersion}`);

  // Check for deprecated fields in round objects
  const knownFields = ["id", "name", "stage", "target_amount", "raised_amount", "investors", "created_at"];
  if (data.rounds?.[0]) {
    const actual = Object.keys(data.rounds[0]);
    const deprecated = knownFields.filter((f) => !actual.includes(f));
    const added = actual.filter((f) => !knownFields.includes(f));
    if (deprecated.length) console.warn(`Removed fields: ${deprecated.join(", ")}`);
    if (added.length) console.log(`New fields: ${added.join(", ")}`);
  }
}
```

## Migration Checklist

- [ ] Review Finta changelog for breaking changes to round or investor endpoints
- [ ] Audit codebase for hardcoded round stage values (e.g., `"pre-seed"`, `"series-a"`)
- [ ] Verify investor contact schema — check for `firm` vs. `organization` field rename
- [ ] Update deal room document upload endpoint if file size limits changed
- [ ] Test investor update email delivery via API (template format may change)
- [ ] Validate webhook payloads for round status change events
- [ ] Migrate CSV import mappings if column headers were renamed
- [ ] Check OAuth token expiry and refresh behavior for API key rotation
- [ ] Update pipeline stage enum values if Finta added custom stage support
- [ ] Run data export and re-import test to verify round-trip data integrity

## Schema Migration

```typescript
// Finta round schema evolved: flat stage string → structured stage object
interface OldRound {
  id: string;
  name: string;
  stage: string; // "pre-seed", "seed", "series-a"
  target_amount: number;
  raised_amount: number;
  investors: string[]; // investor IDs
}

interface NewRound {
  id: string;
  name: string;
  stage: { key: string; label: string; order: number }; // structured stage
  target: { amount: number; currency: string };
  raised: { amount: number; currency: string };
  investors: Array<{ id: string; committed_amount: number }>;
  updated_at: string;
}

function migrateRound(old: OldRound): NewRound {
  const stageMap: Record<string, { label: string; order: number }> = {
    "pre-seed": { label: "Pre-Seed", order: 1 },
    seed: { label: "Seed", order: 2 },
    "series-a": { label: "Series A", order: 3 },
  };
  return {
    id: old.id,
    name: old.name,
    stage: { key: old.stage, ...stageMap[old.stage] ?? { label: old.stage, order: 0 } },
    target: { amount: old.target_amount, currency: "USD" },
    raised: { amount: old.raised_amount, currency: "USD" },
    investors: old.investors.map((id) => ({ id, committed_amount: 0 })),
    updated_at: new Date().toISOString(),
  };
}
```

## Rollback Strategy

```typescript
class FintaClient {
  constructor(private apiKey: string, private version: "v1" | "legacy" = "v1") {}

  private get baseUrl(): string {
    return `https://api.trustfinta.com/${this.version}`;
  }

  async getRounds(): Promise<any> {
    try {
      const res = await fetch(`${this.baseUrl}/rounds`, {
        headers: { Authorization: `Bearer ${this.apiKey}` },
      });
      if (!res.ok) throw new Error(`Finta ${res.status}`);
      return await res.json();
    } catch (err) {
      if (this.version !== "legacy") {
        console.warn("Falling back to legacy Finta API");
        this.version = "legacy";
        return this.getRounds();
      }
      throw err;
    }
  }
}
```

## Error Handling

| Migration Issue | Symptom | Fix |
|----------------|---------|-----|
| Stage enum changed | `400 Bad Request` on round creation with old stage value | Fetch current stage options from `/rounds/stages` endpoint |
| Investor schema mismatch | `investors` returns objects instead of string IDs | Update parser to handle both `string[]` and `{id, committed_amount}[]` |
| Deal room permissions | `403 Forbidden` on document upload | Re-check deal room access scopes after API key rotation |
| CSV import column mismatch | Import fails silently with 0 records created | Re-map columns using updated Finta field names from `/schema` endpoint |
| Webhook signature invalid | Webhook verification fails after API update | Update HMAC secret from Finta dashboard settings |

## Resources

- [Finta Changelog](https://www.trustfinta.com/change-log)
- [Finta API Documentation](https://www.trustfinta.com/developers)

## Next Steps

For CI pipeline integration, see `finta-ci-integration`.
