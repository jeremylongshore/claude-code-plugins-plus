---
name: documenso-multi-env-setup
description: |
  Configure Documenso across multiple environments (dev, staging, production).
  Use when setting up environment-specific configurations, managing API keys,
  or implementing environment promotion workflows.
  Trigger with phrases like "documenso environments", "documenso staging",
  "documenso dev setup", "multi-environment documenso".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, documenso, api, workflow]

---
# Documenso Multi-Environment Setup

## Overview

Configure Documenso across development, staging, and production with environment isolation, secret management, and promotion workflows. Documenso cloud offers a staging environment at `stg-app.documenso.com`; self-hosted users run separate instances.

## Prerequisites

- Documenso accounts or instances for each environment
- Secret management solution (Vault, AWS Secrets Manager, or `.env` files)
- Completed `documenso-install-auth` setup

## Environment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Development                                                 │
│  API: stg-app.documenso.com (or localhost:3000 self-hosted) │
│  Key: DOCUMENSO_API_KEY=api_dev_xxx                         │
│  Webhooks: ngrok tunnel                                      │
├─────────────────────────────────────────────────────────────┤
│  Staging                                                     │
│  API: stg-app.documenso.com                                 │
│  Key: DOCUMENSO_API_KEY=api_stg_xxx                         │
│  Webhooks: staging.yourapp.com/webhooks/documenso           │
├─────────────────────────────────────────────────────────────┤
│  Production                                                  │
│  API: app.documenso.com (or sign.yourcompany.com)           │
│  Key: DOCUMENSO_API_KEY=api_prod_xxx                        │
│  Webhooks: api.yourapp.com/webhooks/documenso               │
└─────────────────────────────────────────────────────────────┘
```

## Instructions

### Step 1: Environment Configuration Files

```bash
# .env.development
DOCUMENSO_API_KEY=api_dev_xxxxxxxxxxxx
DOCUMENSO_BASE_URL=https://stg-app.documenso.com/api/v2
DOCUMENSO_WEBHOOK_SECRET=whsec_dev_xxxxxxxxxxxx
LOG_LEVEL=debug
NODE_ENV=development

# .env.staging
DOCUMENSO_API_KEY=api_stg_xxxxxxxxxxxx
DOCUMENSO_BASE_URL=https://stg-app.documenso.com/api/v2
DOCUMENSO_WEBHOOK_SECRET=whsec_stg_xxxxxxxxxxxx
LOG_LEVEL=info
NODE_ENV=staging

# .env.production
DOCUMENSO_API_KEY=api_prod_xxxxxxxxxxxx
DOCUMENSO_BASE_URL=https://app.documenso.com/api/v2
DOCUMENSO_WEBHOOK_SECRET=whsec_prod_xxxxxxxxxxxx
LOG_LEVEL=warn
NODE_ENV=production
```

### Step 2: Environment-Aware Client Factory

```typescript
// src/documenso/factory.ts
import { Documenso } from "@documenso/sdk-typescript";

interface EnvConfig {
  apiKey: string;
  baseUrl: string;
  webhookSecret: string;
}

function getConfig(): EnvConfig {
  const apiKey = process.env.DOCUMENSO_API_KEY;
  if (!apiKey) throw new Error("DOCUMENSO_API_KEY required");

  return {
    apiKey,
    baseUrl: process.env.DOCUMENSO_BASE_URL ?? "https://app.documenso.com/api/v2",
    webhookSecret: process.env.DOCUMENSO_WEBHOOK_SECRET ?? "",
  };
}

let client: Documenso | null = null;

export function getClient(): Documenso {
  if (!client) {
    const config = getConfig();
    client = new Documenso({
      apiKey: config.apiKey,
      serverURL: config.baseUrl,
    });
  }
  return client;
}

export function getWebhookSecret(): string {
  return getConfig().webhookSecret;
}

// Reset for testing
export function resetClient(): void {
  client = null;
}
```

### Step 3: Environment Guards

```typescript
// src/guards.ts
function requireProduction() {
  if (process.env.NODE_ENV !== "production") {
    throw new Error("This operation requires production environment");
  }
}

function blockProduction(operation: string) {
  if (process.env.NODE_ENV === "production") {
    throw new Error(`${operation} is blocked in production`);
  }
}

// Usage
async function deleteAllDrafts(client: Documenso) {
  blockProduction("deleteAllDrafts"); // Safety guard
  // ... only runs in dev/staging
}

async function sendBulkContracts(client: Documenso) {
  requireProduction(); // Only send real contracts in prod
  // ...
}
```

### Step 4: Mock Client for Development

```typescript
// src/documenso/mock.ts
import { vi } from "vitest";

export function createMockClient() {
  let docCounter = 0;
  return {
    documents: {
      createV0: vi.fn().mockImplementation(async ({ title }) => ({
        documentId: ++docCounter,
        title,
        status: "DRAFT",
      })),
      setFileV0: vi.fn().mockResolvedValue(undefined),
      findV0: vi.fn().mockResolvedValue({ documents: [] }),
      getV0: vi.fn().mockResolvedValue({ status: "DRAFT", recipients: [] }),
      sendV0: vi.fn().mockResolvedValue(undefined),
      deleteV0: vi.fn().mockResolvedValue(undefined),
    },
    documentsRecipients: {
      createV0: vi.fn().mockResolvedValue({ recipientId: 100 }),
    },
    documentsFields: {
      createV0: vi.fn().mockResolvedValue({ fieldId: 200 }),
    },
  };
}
```

### Step 5: Template Promotion Between Environments

```typescript
// scripts/promote-template.ts
// Templates can't be copied via API — recreate them per environment
// Keep template configuration in code for consistency

interface TemplateConfig {
  title: string;
  recipients: Array<{ role: string; placeholder: string }>;
  fields: Array<{
    recipientIndex: number;
    type: string;
    pageNumber: number;
    pageX: number;
    pageY: number;
    pageWidth: number;
    pageHeight: number;
  }>;
}

// Template definitions versioned in git
const SERVICE_AGREEMENT: TemplateConfig = {
  title: "Service Agreement Template v2",
  recipients: [
    { role: "SIGNER", placeholder: "Client" },
    { role: "APPROVER", placeholder: "Legal" },
  ],
  fields: [
    { recipientIndex: 0, type: "SIGNATURE", pageNumber: 3, pageX: 10, pageY: 80, pageWidth: 30, pageHeight: 5 },
    { recipientIndex: 0, type: "DATE", pageNumber: 3, pageX: 60, pageY: 80, pageWidth: 20, pageHeight: 3 },
    { recipientIndex: 1, type: "SIGNATURE", pageNumber: 3, pageX: 10, pageY: 90, pageWidth: 30, pageHeight: 5 },
  ],
};

// Apply to any environment by running: ENV=staging tsx scripts/promote-template.ts
```

## Environment Checklist

| Check | Dev | Staging | Production |
|-------|-----|---------|------------|
| Separate API key | Yes | Yes | Yes |
| Debug logging | On | On | Off |
| Webhook endpoint | ngrok | staging URL | production URL |
| Secret manager | .env file | .env file | Vault/AWS SM |
| Mock mode available | Yes | No | No |
| Cleanup scripts enabled | Yes | Yes | No |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong environment data | Missing `NODE_ENV` | Set explicitly in each environment |
| Key mismatch | Using dev key in prod | Verify env var names per environment |
| Webhook not received | Wrong URL configured | Update webhook URL in each Documenso environment |
| Mock not working | Wrong client injected | Check factory returns mock in test env |

## Resources

- [12-Factor App Config](https://12factor.net/config)
- [Documenso Staging](https://stg-app.documenso.com)
- [Secret Management Best Practices](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)

## Next Steps

For monitoring setup, see `documenso-observability`.
