# Documenso Migration Deep Dive - Implementation Guide

## Migration Types

| Migration Type | Complexity | Duration | Risk |
|---------------|------------|----------|------|
| Fresh start | Low | Days | Low |
| DocuSign migration | Medium | Weeks | Medium |
| HelloSign migration | Medium | Weeks | Medium |
| Adobe Sign migration | High | Months | High |
| Self-hosted migration | Medium | Weeks | Medium |

## Migration Strategy: Strangler Fig Pattern

```
Phase 1: Parallel Systems
┌─────────────────────────────────────────────────────────┐
│ Your Application                                         │
│  ┌─────────────┐         ┌─────────────┐               │
│  │   Legacy    │  100%   │  Documenso  │   0%         │
│  │  (DocuSign) │ ◀────── │   (New)     │              │
│  └─────────────┘         └─────────────┘               │
└─────────────────────────────────────────────────────────┘

Phase 2: Traffic Shifting
┌─────────────────────────────────────────────────────────┐
│ Your Application                                         │
│  ┌─────────────┐         ┌─────────────┐               │
│  │   Legacy    │  50%    │  Documenso  │   50%        │
│  │  (DocuSign) │ ◀─────▶ │   (New)     │              │
│  └─────────────┘         └─────────────┘               │
└─────────────────────────────────────────────────────────┘

Phase 3: Complete Migration
┌─────────────────────────────────────────────────────────┐
│ Your Application                                         │
│  ┌─────────────┐         ┌─────────────┐               │
│  │   Legacy    │   0%    │  Documenso  │  100%        │
│  │  (Retired)  │ ──────▶ │   (Active)  │              │
│  └─────────────┘         └─────────────┘               │
└─────────────────────────────────────────────────────────┘
```

## Pre-Migration Assessment

### Step 1: Document Current State

```typescript
// scripts/analyze-current-system.ts
interface MigrationAssessment {
  documentsTotal: number;
  documentsActive: number;
  templatesTotal: number;
  integrationPoints: string[];
  customizations: string[];
  dependencies: string[];
  estimatedMigrationHours: number;
}

async function assessCurrentSystem(): Promise<MigrationAssessment> {
  // Analyze existing integration
  const codebaseAnalysis = await analyzeCodebase();

  // Count documents and templates
  const documentStats = await getCurrentDocumentStats();

  // Identify integration points
  const integrations = await findIntegrationPoints();

  return {
    documentsTotal: documentStats.total,
    documentsActive: documentStats.active,
    templatesTotal: documentStats.templates,
    integrationPoints: integrations,
    customizations: codebaseAnalysis.customizations,
    dependencies: codebaseAnalysis.dependencies,
    estimatedMigrationHours: calculateEstimate(codebaseAnalysis),
  };
}

async function analyzeCodebase() {
  // Find all files using signing service
  // grep -r "docusign\|hellosign\|adobe.sign" src/

  return {
    customizations: [
      "Custom email templates",
      "Webhook processing",
      "PDF preprocessing",
    ],
    dependencies: ["@docusign/esign", "docusign-esign"],
  };
}
```

### Step 2: Feature Mapping

```typescript
// Map existing features to Documenso equivalents
interface FeatureMapping {
  existingFeature: string;
  documensoEquivalent: string;
  migrationNotes: string;
  complexity: "low" | "medium" | "high";
}

const FEATURE_MAPPING: FeatureMapping[] = [
  {
    existingFeature: "DocuSign envelope",
    documensoEquivalent: "Documenso document/envelope",
    migrationNotes: "Direct mapping, similar concept",
    complexity: "low",
  },
  {
    existingFeature: "DocuSign template",
    documensoEquivalent: "Documenso template",
    migrationNotes: "Recreate templates, export/import not supported",
    complexity: "medium",
  },
  {
    existingFeature: "PowerForms",
    documensoEquivalent: "Direct templates",
    migrationNotes: "Use Documenso direct template links",
    complexity: "low",
  },
  {
    existingFeature: "Bulk send",
    documensoEquivalent: "Batch API calls",
    migrationNotes: "Implement batch processing with queue",
    complexity: "medium",
  },
  {
    existingFeature: "Connect (webhooks)",
    documensoEquivalent: "Documenso webhooks",
    migrationNotes: "Similar events, different payload structure",
    complexity: "medium",
  },
  {
    existingFeature: "Embedded signing",
    documensoEquivalent: "Embed components",
    migrationNotes: "Use @documenso/embed-react or similar",
    complexity: "low",
  },
];
```

## Implementation Plan

### Phase 1: Setup (Week 1-2)

```typescript
// Step 1: Install Documenso SDK alongside existing
// package.json
{
  "dependencies": {
    // Keep existing
    "docusign-esign": "^6.0.0",
    // Add Documenso
    "@documenso/sdk-typescript": "^0.3.0"
  }
}

// Step 2: Create unified interface
// src/signing/interface.ts
export interface SigningService {
  createDocument(input: CreateDocumentInput): Promise<DocumentResult>;
  addRecipient(docId: string, recipient: RecipientInput): Promise<string>;
  addField(docId: string, field: FieldInput): Promise<string>;
  sendDocument(docId: string): Promise<void>;
  getDocumentStatus(docId: string): Promise<DocumentStatus>;
  downloadDocument(docId: string): Promise<Buffer>;
}

// Step 3: Implement adapters
// src/signing/adapters/docusign.ts
export class DocuSignAdapter implements SigningService {
  // Existing implementation
}

// src/signing/adapters/documenso.ts
export class DocumensoAdapter implements SigningService {
  // New implementation
}
```

### Phase 2: Adapter Implementation (Week 3-4)

```typescript
// src/signing/adapters/documenso.ts
import { Documenso } from "@documenso/sdk-typescript";
import { SigningService, CreateDocumentInput } from "../interface";

export class DocumensoAdapter implements SigningService {
  private client: Documenso;

  constructor(apiKey: string, baseUrl?: string) {
    this.client = new Documenso({
      apiKey,
      serverURL: baseUrl,
    });
  }

  async createDocument(input: CreateDocumentInput): Promise<DocumentResult> {
    const doc = await this.client.documents.createV0({
      title: input.title,
      file: input.file,
    });

    return {
      id: doc.documentId!,
      status: "DRAFT",
      provider: "documenso",
    };
  }

  async addRecipient(
    docId: string,
    recipient: RecipientInput
  ): Promise<string> {
    const result = await this.client.documentsRecipients.createV0({
      documentId: docId,
      email: recipient.email,
      name: recipient.name,
      role: this.mapRole(recipient.role),
    });

    return result.recipientId!;
  }

  async addField(docId: string, field: FieldInput): Promise<string> {
    const result = await this.client.documentsFields.createV0({
      documentId: docId,
      recipientId: field.recipientId,
      type: this.mapFieldType(field.type),
      page: field.page,
      positionX: field.x,
      positionY: field.y,
      width: field.width,
      height: field.height,
    });

    return result.fieldId!;
  }

  async sendDocument(docId: string): Promise<void> {
    await this.client.documents.sendV0({ documentId: docId });
  }

  async getDocumentStatus(docId: string): Promise<DocumentStatus> {
    const doc = await this.client.documents.getV0({ documentId: docId });

    return {
      id: doc.id!,
      status: this.mapStatus(doc.status!),
      recipients: doc.recipients?.map((r) => ({
        email: r.email!,
        status: this.mapRecipientStatus(r.signingStatus!),
      })) ?? [],
    };
  }

  async downloadDocument(docId: string): Promise<Buffer> {
    const result = await this.client.documents.downloadV0({
      documentId: docId,
    });
    return Buffer.from(result as ArrayBuffer);
  }

  private mapRole(role: string): string {
    const mapping: Record<string, string> = {
      signer: "SIGNER",
      cc: "CC",
      viewer: "VIEWER",
      approver: "APPROVER",
    };
    return mapping[role.toLowerCase()] ?? "SIGNER";
  }

  private mapFieldType(type: string): string {
    const mapping: Record<string, string> = {
      signHere: "SIGNATURE",
      initialHere: "INITIALS",
      dateSigned: "DATE",
      fullName: "NAME",
      email: "EMAIL",
      text: "TEXT",
      checkbox: "CHECKBOX",
    };
    return mapping[type] ?? "TEXT";
  }

  private mapStatus(status: string): string {
    const mapping: Record<string, string> = {
      DRAFT: "draft",
      PENDING: "sent",
      COMPLETED: "completed",
      CANCELLED: "voided",
      REJECTED: "declined",
    };
    return mapping[status] ?? status.toLowerCase();
  }

  private mapRecipientStatus(status: string): string {
    const mapping: Record<string, string> = {
      NOT_SIGNED: "pending",
      SIGNED: "completed",
      REJECTED: "declined",
    };
    return mapping[status] ?? "pending";
  }
}
```

### Phase 3: Service Factory with Feature Flags (Week 5)

```typescript
// src/signing/factory.ts
import { SigningService } from "./interface";
import { DocuSignAdapter } from "./adapters/docusign";
import { DocumensoAdapter } from "./adapters/documenso";

interface FeatureFlags {
  isEnabled(flag: string): Promise<boolean>;
  getPercentage(flag: string): Promise<number>;
}

export class SigningServiceFactory {
  constructor(
    private featureFlags: FeatureFlags,
    private config: {
      docusign: { apiKey: string; accountId: string };
      documenso: { apiKey: string; baseUrl?: string };
    }
  ) {}

  async getService(context?: { userId?: string }): Promise<SigningService> {
    // Check if fully migrated
    const documensoEnabled = await this.featureFlags.isEnabled("documenso_full");
    if (documensoEnabled) {
      return new DocumensoAdapter(
        this.config.documenso.apiKey,
        this.config.documenso.baseUrl
      );
    }

    // Check gradual rollout percentage
    const percentage = await this.featureFlags.getPercentage("documenso_rollout");
    if (Math.random() * 100 < percentage) {
      return new DocumensoAdapter(
        this.config.documenso.apiKey,
        this.config.documenso.baseUrl
      );
    }

    // Default to legacy
    return new DocuSignAdapter(
      this.config.docusign.apiKey,
      this.config.docusign.accountId
    );
  }
}
```

### Phase 4: Data Migration (Week 6-7)

```typescript
// scripts/migrate-templates.ts
/**
 * Templates cannot be directly exported/imported.
 * This script documents existing templates for manual recreation.
 */

interface TemplateMigrationPlan {
  legacyTemplateId: string;
  name: string;
  description: string;
  recipientRoles: string[];
  fields: FieldDefinition[];
  recreated: boolean;
  documensoTemplateId?: string;
}

async function generateTemplateMigrationPlan(): Promise<TemplateMigrationPlan[]> {
  const legacyTemplates = await getLegacyTemplates();
  const plans: TemplateMigrationPlan[] = [];

  for (const template of legacyTemplates) {
    plans.push({
      legacyTemplateId: template.id,
      name: template.name,
      description: template.description,
      recipientRoles: template.recipients.map((r) => r.roleName),
      fields: template.fields.map((f) => ({
        type: f.type,
        page: f.pageNumber,
        x: f.xPosition,
        y: f.yPosition,
        width: f.width,
        height: f.height,
        recipientRole: f.recipientRole,
      })),
      recreated: false,
    });
  }

  // Save plan for tracking
  await fs.writeFile(
    "migration/template-plan.json",
    JSON.stringify(plans, null, 2)
  );

  return plans;
}

// For completed documents, create reference mapping
interface DocumentMapping {
  legacyId: string;
  documensoId?: string;
  title: string;
  status: string;
  completedAt?: string;
  signedDocumentUrl?: string;
}

async function createDocumentMapping(): Promise<void> {
  // Historical documents stay in legacy system
  // New documents go to Documenso
  // Create mapping table for reference

  await db.execute(`
    CREATE TABLE IF NOT EXISTS document_mapping (
      id SERIAL PRIMARY KEY,
      legacy_id VARCHAR(255),
      documenso_id VARCHAR(255),
      title VARCHAR(500),
      status VARCHAR(50),
      completed_at TIMESTAMP,
      created_at TIMESTAMP DEFAULT NOW()
    )
  `);
}
```

### Phase 5: Webhook Migration (Week 8)

```typescript
// src/webhooks/unified-handler.ts
import express from "express";

const router = express.Router();

// New Documenso webhook endpoint
router.post("/webhooks/documenso", (req, res) => {
  const { event, payload } = req.body;

  // Normalize to common event format
  const normalizedEvent = normalizeDocumensoEvent(event, payload);
  processSigningEvent(normalizedEvent);

  res.json({ received: true });
});

// Keep legacy webhook endpoint during migration
router.post("/webhooks/docusign", (req, res) => {
  const { event, data } = req.body;

  // Normalize to common event format
  const normalizedEvent = normalizeDocuSignEvent(event, data);
  processSigningEvent(normalizedEvent);

  res.json({ status: "ok" });
});

// Common event processing
interface NormalizedSigningEvent {
  eventType: "created" | "sent" | "signed" | "completed" | "declined";
  documentId: string;
  provider: "documenso" | "docusign";
  signerEmail?: string;
  timestamp: Date;
}

async function processSigningEvent(event: NormalizedSigningEvent): Promise<void> {
  console.log(`Processing ${event.provider} event: ${event.eventType}`);

  switch (event.eventType) {
    case "completed":
      await handleDocumentCompleted(event);
      break;
    case "declined":
      await handleDocumentDeclined(event);
      break;
    // ... other handlers
  }
}
```

### Phase 6: Rollout & Monitoring (Week 9-10)

```typescript
// Gradual rollout schedule
const ROLLOUT_SCHEDULE = [
  { day: 1, percentage: 5, description: "Internal users" },
  { day: 3, percentage: 10, description: "Early adopters" },
  { day: 7, percentage: 25, description: "Quarter traffic" },
  { day: 14, percentage: 50, description: "Half traffic" },
  { day: 21, percentage: 75, description: "Most traffic" },
  { day: 28, percentage: 100, description: "Full migration" },
];

// Monitoring during rollout
interface MigrationMetrics {
  documentsCreated: { legacy: number; documenso: number };
  errorRate: { legacy: number; documenso: number };
  latencyP95: { legacy: number; documenso: number };
  completionRate: { legacy: number; documenso: number };
}

async function checkMigrationHealth(): Promise<{
  healthy: boolean;
  metrics: MigrationMetrics;
}> {
  const metrics = await collectMetrics();

  // Alert if Documenso error rate is significantly higher
  const errorDiff = metrics.errorRate.documenso - metrics.errorRate.legacy;
  const healthy = errorDiff < 0.02; // 2% tolerance

  return { healthy, metrics };
}
```

## Rollback Procedure

```bash
#!/bin/bash
# scripts/rollback-migration.sh

echo "Rolling back Documenso migration..."

# Disable Documenso via feature flag
curl -X POST $FEATURE_FLAG_API/flags \
  -d '{"flag": "documenso_rollout", "value": 0}'

# Verify rollback
sleep 10
curl -s https://your-app.com/health | jq '.signing.provider'

echo "Rollback complete. All traffic now using legacy provider."
```

## Congratulations!
You have completed the Documenso Skill Pack. Review other skills as needed for ongoing operations.
