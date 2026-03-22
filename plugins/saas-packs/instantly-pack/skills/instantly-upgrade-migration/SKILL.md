---
name: instantly-upgrade-migration
description: |
  Migrate Instantly.ai integrations from API v1 to v2.
  Use when upgrading from deprecated v1 endpoints, updating authentication,
  or migrating endpoint paths and request formats.
  Trigger with phrases like "instantly v1 to v2", "instantly api migration",
  "instantly upgrade", "instantly deprecated", "migrate instantly api".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, instantly, migration, upgrade]

---
# Instantly Upgrade Migration: API v1 to v2

## Overview
Migrate from Instantly API v1 (deprecated January 2026) to API v2. Key changes: Bearer token auth replaces query-string API keys, REST-standard endpoints replace legacy paths, scoped API keys replace single global key, and cursor-based pagination replaces offset pagination. Existing v1 integrations via Zapier/Make continue working, but new integrations must use v2.

## Prerequisites
- Existing Instantly API v1 integration
- Access to Instantly dashboard to generate v2 API keys
- Understanding of Bearer token authentication

## Migration Map

### Authentication Change
```typescript
// v1: API key as query parameter
// DEPRECATED — do not use
const v1Url = `https://api.instantly.ai/api/v1/campaign/list?api_key=${API_KEY}`;

// v2: Bearer token in Authorization header
const v2Response = await fetch("https://api.instantly.ai/api/v2/campaigns", {
  headers: { Authorization: `Bearer ${API_KEY}` },
});
```

### Endpoint Migration Table
| Operation | v1 Endpoint | v2 Endpoint | Method Change |
|-----------|------------|------------|---------------|
| List campaigns | `GET /api/v1/campaign/list` | `GET /api/v2/campaigns` | Same |
| Get campaign | `GET /api/v1/campaign/get` | `GET /api/v2/campaigns/{id}` | Query -> Path param |
| Create campaign | `POST /api/v1/campaign/create` | `POST /api/v2/campaigns` | REST standard |
| Launch campaign | `POST /api/v1/campaign/launch` | `POST /api/v2/campaigns/{id}/activate` | New path |
| Pause campaign | `POST /api/v1/campaign/pause` | `POST /api/v2/campaigns/{id}/pause` | New path |
| Add leads | `POST /api/v1/lead/add` | `POST /api/v2/leads` | Simplified |
| List leads | `GET /api/v1/lead/list` | `POST /api/v2/leads/list` | GET -> POST |
| Delete leads | `POST /api/v1/lead/delete` | `DELETE /api/v2/leads/{id}` | REST standard |
| Get analytics | `GET /api/v1/analytics/campaign` | `GET /api/v2/campaigns/analytics` | New path |
| List accounts | `GET /api/v1/account/list` | `GET /api/v2/accounts` | Simplified |

### Request Body Changes
```typescript
// v1: Campaign creation
const v1Body = {
  api_key: "your-key",
  name: "Campaign Name",
  // Flat structure
};

// v2: Campaign creation — structured schedule and sequences
const v2Body = {
  name: "Campaign Name",
  campaign_schedule: {
    start_date: "2026-04-01",
    schedules: [{
      name: "Business Hours",
      timing: { from: "09:00", to: "17:00" },
      days: { "1": true, "2": true, "3": true, "4": true, "5": true, "0": false, "6": false },
      timezone: "America/New_York",
    }],
  },
  sequences: [{
    steps: [{
      type: "email",
      delay: 0,
      variants: [{ subject: "Hello {{firstName}}", body: "Hi {{firstName}}..." }],
    }],
  }],
};
```

### Lead Operation Changes
```typescript
// v1: Add leads to campaign
const v1AddLeads = {
  api_key: "your-key",
  campaign_id: "campaign-uuid",
  leads: [
    { email: "user@example.com", first_name: "Jane" },
  ],
};

// v2: Add leads individually (POST /api/v2/leads)
const v2AddLead = {
  campaign: "campaign-uuid",          // "campaign_id" -> "campaign"
  email: "user@example.com",
  first_name: "Jane",
  skip_if_in_workspace: true,         // New: deduplication control
  verify_leads_on_import: true,       // New: auto-verification
  custom_variables: { role: "CTO" },  // New: custom fields
};

// v2: Bulk operations use POST /api/v2/leads/move for batch moves
```

## Instructions

### Step 1: Audit Existing v1 Calls
```bash
set -euo pipefail
# Find all v1 API calls in your codebase
grep -rn "api/v1/" src/ --include="*.ts" --include="*.js" --include="*.py" || echo "No v1 calls found"
grep -rn "api_key=" src/ --include="*.ts" --include="*.js" --include="*.py" || echo "No query-string keys found"
```

### Step 2: Create Migration Adapter
```typescript
// src/instantly-migration.ts
// Drop-in adapter that maps v1 calls to v2 endpoints

export class InstantlyV1ToV2Adapter {
  private apiKey: string;
  private baseUrl = "https://api.instantly.ai/api/v2";

  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${this.apiKey}`,
        ...options.headers,
      },
    });
    if (!res.ok) throw new Error(`Instantly ${res.status}: ${await res.text()}`);
    return res.json() as Promise<T>;
  }

  // v1: campaign/list -> v2: GET /campaigns
  async listCampaigns() {
    return this.request("/campaigns?limit=100");
  }

  // v1: campaign/get?campaign_id=X -> v2: GET /campaigns/{id}
  async getCampaign(campaignId: string) {
    return this.request(`/campaigns/${campaignId}`);
  }

  // v1: campaign/launch -> v2: POST /campaigns/{id}/activate
  async launchCampaign(campaignId: string) {
    return this.request(`/campaigns/${campaignId}/activate`, { method: "POST" });
  }

  // v1: campaign/pause -> v2: POST /campaigns/{id}/pause
  async pauseCampaign(campaignId: string) {
    return this.request(`/campaigns/${campaignId}/pause`, { method: "POST" });
  }

  // v1: lead/add (bulk) -> v2: POST /leads (one at a time)
  async addLeads(campaignId: string, leads: Array<{ email: string; first_name?: string }>) {
    const results = [];
    for (const lead of leads) {
      const result = await this.request("/leads", {
        method: "POST",
        body: JSON.stringify({
          campaign: campaignId,
          email: lead.email,
          first_name: lead.first_name,
          skip_if_in_workspace: true,
        }),
      });
      results.push(result);
    }
    return results;
  }

  // v1: analytics/campaign -> v2: GET /campaigns/analytics
  async getCampaignAnalytics(campaignId: string) {
    return this.request(`/campaigns/analytics?id=${campaignId}`);
  }
}
```

### Step 3: Pagination Migration
```typescript
// v1: Offset-based (skip/limit)
// const v1 = await fetch(`/api/v1/lead/list?api_key=${key}&campaign_id=${id}&skip=100&limit=50`);

// v2: Cursor-based (starting_after)
async function* paginateV2<T extends { id: string }>(
  path: string,
  pageSize = 100
): AsyncGenerator<T[]> {
  let startingAfter: string | undefined;
  while (true) {
    const qs = new URLSearchParams({ limit: String(pageSize) });
    if (startingAfter) qs.set("starting_after", startingAfter);
    const page = await instantly<T[]>(`${path}?${qs}`);
    if (page.length === 0) break;
    yield page;
    startingAfter = page[page.length - 1].id;
    if (page.length < pageSize) break;
  }
}
```

### Step 4: New v2 Features to Adopt
```typescript
// These features are v2-only — no v1 equivalent

// Scoped API keys
// POST /api/v2/api-keys — create keys with specific scopes
await instantly("/api-keys", {
  method: "POST",
  body: JSON.stringify({ name: "analytics-only", scopes: ["campaigns:read"] }),
});

// Subsequences (conditional follow-ups)
// POST /api/v2/subsequences
await instantly("/subsequences", {
  method: "POST",
  body: JSON.stringify({
    parent_campaign: campaignId,
    name: "Re-engage interested leads",
    conditions: { crm_status: [1] }, // triggered when lead is "Interested"
  }),
});

// Inbox placement testing
// POST /api/v2/inbox-placement-tests
await instantly("/inbox-placement-tests", {
  method: "POST",
  body: JSON.stringify({
    name: "Pre-launch deliverability test",
    email_subject: "Test Subject",
    email_body: "Test body content",
    type: 1,
  }),
});

// Block list management (bulk)
// POST /api/v2/block-lists-entries/bulk-create
await instantly("/block-lists-entries/bulk-create", {
  method: "POST",
  body: JSON.stringify({
    entries: ["competitor.com", "internal.com"],
  }),
});
```

## Migration Checklist
- [ ] Generate v2 API key with appropriate scopes
- [ ] Replace `api_key` query params with `Authorization: Bearer` header
- [ ] Update all endpoint paths per migration table above
- [ ] Convert offset pagination to cursor-based pagination
- [ ] Update request bodies (e.g., `campaign_id` -> `campaign`)
- [ ] Add error handling for new HTTP status codes (422, 429)
- [ ] Test all migrated endpoints against v2 mock server
- [ ] Remove old v1 API key from environment

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `401` on v2 | Using v1 key format | Generate new v2 Bearer token |
| `404` on v2 path | Using v1 endpoint path | Check migration table above |
| `422` on lead add | New validation rules in v2 | Add required fields per v2 schema |
| Missing pagination data | Using `skip` instead of `starting_after` | Convert to cursor pagination |

## Resources
- [API v1 to v2 Migration Guide](https://developer.instantly.ai/api-v1-docs)
- [API v2 Documentation](https://developer.instantly.ai/)
- [API v2 Schemas](https://developer.instantly.ai/api/v2/schemas)

## Next Steps
For CI/CD integration, see `instantly-ci-integration`.
