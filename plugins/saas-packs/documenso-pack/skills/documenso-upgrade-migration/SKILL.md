---
name: documenso-upgrade-migration
description: |
  Manage Documenso API version upgrades and SDK migrations.
  Use when upgrading from v1 to v2 API, updating SDK versions,
  or migrating between Documenso versions.
  Trigger with phrases like "documenso upgrade", "documenso v2 migration",
  "update documenso SDK", "documenso API version".
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, documenso, api, migration]

---
# Documenso Upgrade & Migration

## Current State
!`npm list @documenso/sdk-typescript 2>/dev/null || echo 'SDK not installed'`
!`npm list documenso-sdk-python 2>/dev/null || pip show documenso-sdk-python 2>/dev/null | head -3 || echo 'Python SDK not installed'`

## Overview

Guide for upgrading between Documenso API versions and SDK updates. Documenso has two API versions: **v1** (legacy, document-centric) and **v2** (recommended, envelope-based with multi-document support). The TypeScript and Python SDKs use the v2 API by default.

## Prerequisites

- Current Documenso integration working
- Test environment available
- Feature flag system (recommended for gradual rollout)

## API Version Comparison

| Feature | v1 (legacy) | v2 (recommended) |
|---------|-------------|-------------------|
| Base path | `/api/v1/` | `/api/v2/` |
| Document model | Documents | Envelopes (can contain multiple documents) |
| SDK support | REST only | TypeScript + Python SDK |
| Template API | `/templates/{id}/create-document` | Via envelope create |
| Authentication | `Authorization: Bearer` | `Authorization: Bearer` (same) |
| Status | Maintained, not deprecated | Actively developed |

## Instructions

### Step 1: Upgrade SDK to Latest

```bash
# Check current version
npm list @documenso/sdk-typescript

# Upgrade
npm install @documenso/sdk-typescript@latest

# Check for breaking changes
npm info @documenso/sdk-typescript changelog

# Python
pip install --upgrade documenso-sdk-python
```

### Step 2: v1 REST to v2 SDK Migration

```typescript
// BEFORE: v1 REST API
const BASE = "https://app.documenso.com/api/v1";
const headers = { Authorization: `Bearer ${process.env.DOCUMENSO_API_KEY}` };

// Create document
const res = await fetch(`${BASE}/documents`, {
  method: "POST",
  headers: { ...headers, "Content-Type": "application/json" },
  body: JSON.stringify({ title: "Contract" }),
});
const doc = await res.json();

// List documents
const listRes = await fetch(`${BASE}/documents?page=1&perPage=20`, { headers });
const { documents } = await listRes.json();

// AFTER: v2 SDK
import { Documenso } from "@documenso/sdk-typescript";
const client = new Documenso({ apiKey: process.env.DOCUMENSO_API_KEY! });

// Create document
const doc = await client.documents.createV0({ title: "Contract" });

// List documents
const { documents } = await client.documents.findV0({ page: 1, perPage: 20 });
```

### Step 3: Gradual Migration with Feature Flags

```typescript
// src/documenso/migration.ts
import { Documenso } from "@documenso/sdk-typescript";

const USE_V2 = process.env.DOCUMENSO_USE_V2 === "true";

export async function createDocument(title: string) {
  if (USE_V2) {
    const client = new Documenso({ apiKey: process.env.DOCUMENSO_API_KEY! });
    return client.documents.createV0({ title });
  }

  // Legacy v1
  const res = await fetch("https://app.documenso.com/api/v1/documents", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${process.env.DOCUMENSO_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ title }),
  });
  return res.json();
}

// Enable gradually:
// 1. DOCUMENSO_USE_V2=true in staging → test
// 2. DOCUMENSO_USE_V2=true for 10% of production traffic
// 3. Monitor error rates
// 4. Roll to 100%
// 5. Remove v1 code
```

### Step 4: Self-Hosted Version Upgrade

```bash
# Self-hosted Documenso upgrades are simple:
# 1. Pull new image
docker pull documenso/documenso:latest

# 2. Restart container (migrations run automatically on start)
docker compose -f docker-compose.prod.yml up -d documenso

# 3. Verify
docker logs documenso --tail 20 | grep "prisma migrate"
curl -s https://sign.yourcompany.com/api/health

# Rollback if needed:
docker compose -f docker-compose.prod.yml down documenso
docker pull documenso/documenso:previous-tag
docker compose -f docker-compose.prod.yml up -d documenso
```

### Step 5: Migration Testing

```typescript
// tests/migration/v1-v2-parity.test.ts
import { describe, it, expect } from "vitest";

describe("v1/v2 API Parity", () => {
  it("creates documents with same result shape", async () => {
    // Create via v1
    const v1Doc = await createDocumentV1("Parity Test");
    // Create via v2
    const v2Doc = await createDocumentV2("Parity Test");

    // Verify same essential fields
    expect(v1Doc.title).toBe(v2Doc.title);
    expect(typeof v1Doc.id).toBe("number");
    expect(typeof v2Doc.documentId).toBe("number");
  });

  it("lists documents consistently", async () => {
    const v1List = await listDocumentsV1();
    const v2List = await listDocumentsV2();

    // Same documents visible via both APIs
    expect(v1List.length).toBe(v2List.length);
  });
});
```

## Migration Checklist

- [ ] Current SDK version documented
- [ ] Changelog reviewed for breaking changes
- [ ] Feature branch created for migration
- [ ] v2 SDK installed alongside v1 code
- [ ] Feature flag for gradual rollout
- [ ] Parity tests passing (v1 and v2 produce same results)
- [ ] Staging fully tested on v2
- [ ] Production rolled out gradually
- [ ] v1 code removed after full rollout
- [ ] Self-hosted: container upgraded and migrations verified

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| ID format mismatch | v1 returns `id`, v2 returns `documentId` | Use adapter/mapping layer |
| Missing field | API change in new version | Update to new field names |
| Enum case sensitivity | v2 SDK uses uppercase enums | Use `"SIGNER"` not `"signer"` |
| Template API difference | v1 templates vs v2 envelopes | Check API version for template operations |

## Resources

- [Documenso API v2 (OpenAPI)](https://openapi.documenso.com/)
- [TypeScript SDK Releases](https://github.com/documenso/sdk-typescript/releases)
- [Python SDK](https://github.com/documenso/sdk-python)
- [Self-Hosting Upgrade](https://docs.documenso.com/developers/self-hosting)

## Next Steps

For CI/CD integration, see `documenso-ci-integration`.
