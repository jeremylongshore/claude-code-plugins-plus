---
name: documenso-migration-deep-dive
description: |
  Execute comprehensive Documenso migration strategies for platform switches.
  Use when migrating from other signing platforms, re-platforming to Documenso,
  or performing major infrastructure changes.
  Trigger with phrases like "migrate to documenso", "documenso migration",
  "switch to documenso", "documenso replatform", "replace docusign".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, documenso, migration]

---
# Documenso Migration Deep Dive

## Current State
!`npm list 2>/dev/null | head -10`

## Overview

Comprehensive guide for migrating to Documenso from other e-signature platforms (DocuSign, HelloSign, PandaDoc, Adobe Sign). Uses the Strangler Fig pattern for zero-downtime migration with feature flags and rollback support.

## Prerequisites

- Current signing platform documented (APIs, templates, webhooks)
- Documenso account configured (see `documenso-install-auth`)
- Feature flag infrastructure (LaunchDarkly, environment variables, etc.)
- Parallel run capability (both platforms active during migration)

## Migration Strategy: Strangler Fig Pattern

```
Phase 1: Parallel Systems (Week 1-2)
┌──────────┐     ┌─────────────┐
│ Your App │────▶│ Old Platform │  (100% traffic)
│          │     └─────────────┘
│          │────▶│  Documenso   │  (shadow: log only, don't send)
└──────────┘     └─────────────┘

Phase 2: Gradual Cutover (Week 3-4)
┌──────────┐     ┌─────────────┐
│ Your App │────▶│ Old Platform │  (50% traffic via feature flag)
│          │     └─────────────┘
│          │────▶│  Documenso   │  (50% traffic)
└──────────┘     └─────────────┘

Phase 3: Full Migration (Week 5+)
┌──────────┐     ┌─────────────┐
│ Your App │────▶│  Documenso   │  (100% traffic)
└──────────┘     └─────────────┘
                 Old platform decommissioned
```

## Instructions

### Step 1: Pre-Migration Assessment

```typescript
// scripts/assess-current-system.ts
// Inventory your current signing platform usage

interface MigrationAssessment {
  platform: string;
  activeTemplates: number;
  documentsPerMonth: number;
  webhookEndpoints: string[];
  recipientRoles: string[];
  fieldTypes: string[];
  integrations: string[];  // CRM, database, etc.
}

async function assessCurrentSystem(): Promise<MigrationAssessment> {
  // Example for DocuSign
  return {
    platform: "DocuSign",
    activeTemplates: 15,
    documentsPerMonth: 200,
    webhookEndpoints: [
      "https://api.yourapp.com/webhooks/docusign",
    ],
    recipientRoles: ["Signer", "CC", "In Person Signer"],
    fieldTypes: ["Signature", "Date", "Text", "Checkbox", "Initial"],
    integrations: ["Salesforce", "PostgreSQL"],
  };
}
```

### Step 2: Feature Mapping

| DocuSign | HelloSign | Documenso | Notes |
|----------|-----------|-----------|-------|
| Envelope | Signature Request | Document | Documenso v2 also has Envelopes |
| Template | Template | Template | Create via UI, use via API |
| Signer | Signer | SIGNER role | Same concept |
| CC | CC | CC role | Same concept |
| In Person | N/A | Direct Link | Use embedded signing |
| Tabs/Fields | Form Fields | Fields | SIGNATURE, TEXT, DATE, etc. |
| Connect (webhooks) | Callbacks | Webhooks | document.completed, etc. |
| PowerForms | N/A | Direct Links | Public signing URLs |

### Step 3: Template Migration

```typescript
// Templates can't be migrated via API — recreate in Documenso
// Keep template definitions in code for reproducibility

interface TemplateDef {
  name: string;
  description: string;
  recipientRoles: Array<{ role: string; placeholder: string }>;
  fields: Array<{
    recipientIndex: number;
    type: string;
    page: number;
    x: number;
    y: number;
    width: number;
    height: number;
  }>;
}

const TEMPLATES: TemplateDef[] = [
  {
    name: "NDA — Standard",
    description: "Non-disclosure agreement template",
    recipientRoles: [
      { role: "SIGNER", placeholder: "Counterparty" },
      { role: "CC", placeholder: "Legal Team" },
    ],
    fields: [
      { recipientIndex: 0, type: "SIGNATURE", page: 2, x: 10, y: 80, width: 30, height: 5 },
      { recipientIndex: 0, type: "DATE", page: 2, x: 60, y: 80, width: 20, height: 3 },
      { recipientIndex: 0, type: "NAME", page: 2, x: 10, y: 75, width: 30, height: 3 },
    ],
  },
  // ... more templates
];

// Instructions: create each template in the Documenso UI using these specs
// Then record the template IDs in your config
```

### Step 4: Webhook Migration

```typescript
// Map old platform events to Documenso events
const EVENT_MAPPING: Record<string, string> = {
  // DocuSign → Documenso
  "envelope-completed": "document.completed",
  "envelope-sent": "document.sent",
  "envelope-declined": "document.rejected",
  "envelope-voided": "document.cancelled",
  "recipient-completed": "document.signed",

  // HelloSign → Documenso
  "signature_request_all_signed": "document.completed",
  "signature_request_sent": "document.sent",
  "signature_request_declined": "document.rejected",
  "signature_request_signed": "document.signed",
};

// Unified handler that works with both platforms during migration
async function handleSigningEvent(source: "old" | "documenso", event: string, payload: any) {
  const normalizedEvent = source === "old"
    ? EVENT_MAPPING[event] ?? event
    : event;

  switch (normalizedEvent) {
    case "document.completed":
      await onDocumentCompleted(payload);
      break;
    case "document.rejected":
      await onDocumentRejected(payload);
      break;
  }
}
```

### Step 5: Dual-Write with Feature Flag

```typescript
// src/signing/router.ts
const USE_DOCUMENSO = process.env.USE_DOCUMENSO === "true";

async function sendForSigning(request: SigningRequest) {
  if (USE_DOCUMENSO) {
    return sendViaDocumenso(request);
  }
  return sendViaLegacy(request);
}

// During parallel phase: send via both, compare results
async function sendForSigningParallel(request: SigningRequest) {
  const legacyResult = await sendViaLegacy(request);

  // Shadow-send to Documenso (don't actually send to recipients)
  try {
    const doc = await documensoClient.documents.createV0({ title: request.title });
    // Don't call sendV0 — just verify creation works
    await documensoClient.documents.deleteV0(doc.documentId);
    console.log("Documenso shadow test: OK");
  } catch (err) {
    console.error("Documenso shadow test: FAIL", err);
  }

  return legacyResult;
}
```

### Step 6: Rollback Procedure

```bash
# If Documenso migration causes issues:

# 1. Disable feature flag
export USE_DOCUMENSO=false
# Or toggle in LaunchDarkly/feature flag service

# 2. Deploy the change
# All new signing requests go to old platform immediately

# 3. Handle in-flight Documenso documents
# Documents already sent via Documenso will complete there
# No action needed — they just use a different platform

# 4. Investigate and fix the issue
# Review logs, fix the integration, re-enable gradually
```

## Migration Timeline

| Week | Phase | Action | Risk |
|------|-------|--------|------|
| 1 | Assessment | Inventory templates, webhooks, integrations | Low |
| 2 | Setup | Configure Documenso, recreate templates | Low |
| 3 | Shadow | Run parallel, compare results (no live traffic) | Low |
| 4 | Pilot | 10% of new documents via Documenso | Medium |
| 5 | Expand | 50% of new documents via Documenso | Medium |
| 6 | Cutover | 100% via Documenso, old platform read-only | Medium |
| 8 | Decommission | Remove old platform code and webhooks | Low |

## Error Handling

| Migration Issue | Cause | Solution |
|----------------|-------|----------|
| Field position different | Different coordinate systems | Map percentage-based (Documenso) from pixel-based (old) |
| Webhook format change | Different payload structure | Use event normalizer/adapter |
| Template missing | Not recreated in Documenso | Create from template definitions |
| High error rate during cutover | Integration bug | Pause rollout, rollback, investigate |

## Resources

- [Strangler Fig Pattern](https://martinfowler.com/bliki/StranglerFigApplication.html)
- [Documenso Documentation](https://docs.documenso.com)
- [Documenso vs DocuSign](https://documenso.com/blog)
- [Feature Flags Best Practices](https://launchdarkly.com/blog/feature-flags-best-practices/)

## Next Steps

Review related skills for comprehensive coverage of your new Documenso integration.
