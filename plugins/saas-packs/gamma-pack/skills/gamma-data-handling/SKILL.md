---
name: gamma-data-handling
description: |
  Handle data privacy, retention, and compliance for Gamma integrations.
  Use when implementing GDPR compliance, data retention policies,
  or managing user data within Gamma workflows.
  Trigger with phrases like "gamma data", "gamma privacy",
  "gamma GDPR", "gamma data retention", "gamma compliance".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, gamma, workflow, compliance]

---
# Gamma Data Handling

## Overview

Data handling, privacy controls, and compliance for Gamma API integrations. Gamma processes user-submitted content through AI to generate presentations -- understand what data flows where and how to handle PII, retention, and GDPR requirements.

## Prerequisites

- Understanding of data privacy regulations (GDPR, CCPA)
- Completed `gamma-install-auth` setup
- Data classification policies defined

## Data Flow Map

```
User Input (content, prompts)
     │
     ▼
┌──────────────┐
│  Your App    │  ← PII may be in content (names, company data)
│  (API key)   │
└──────┬───────┘
       │ POST /v1.0/generations
       ▼
┌──────────────┐
│  Gamma API   │  ← Content processed by AI
│  (gamma.app) │  ← Images generated
└──────┬───────┘
       │ gammaUrl + exportUrl
       ▼
┌──────────────┐
│  Generated   │  ← Presentation stored in Gamma workspace
│  Content     │  ← Export files (PDF/PPTX/PNG) temporary
└──────────────┘
```

## Data Classification

| Data Type | Classification | Where Stored | Retention |
|-----------|---------------|--------------|-----------|
| API key | Secret | Your env vars | Active use only |
| Content/prompts | May contain PII | Gamma servers (during generation) | Gamma's policy |
| Generated gammas | User data | Gamma workspace | User-controlled |
| Export files (PDF/PPTX) | User data | Temporary URLs | Download promptly, URLs expire |
| User prompts in logs | PII risk | Your infrastructure | Your policy (sanitize!) |
| Credit usage | Billing data | Gamma | Per Gamma ToS |

## Instructions

### Step 1: Sanitize Content Before Sending

```typescript
// src/gamma/sanitize.ts
// Remove PII from content before sending to Gamma if not needed

interface SanitizeOptions {
  removeEmails: boolean;
  removePhones: boolean;
  maskNames: boolean;
}

function sanitizeContent(content: string, opts: SanitizeOptions): string {
  let sanitized = content;

  if (opts.removeEmails) {
    sanitized = sanitized.replace(/[\w.-]+@[\w.-]+\.\w+/g, "[email]");
  }
  if (opts.removePhones) {
    sanitized = sanitized.replace(/\+?[\d\s()-]{10,}/g, "[phone]");
  }
  if (opts.maskNames) {
    // Only mask if you have a list of known names
    // Generic regex would be too aggressive
  }

  return sanitized;
}

// Usage: sanitize before generation
const safeContent = sanitizeContent(userContent, {
  removeEmails: true,
  removePhones: true,
  maskNames: false,
});

await gamma.generate({
  content: safeContent,
  outputFormat: "presentation",
});
```

### Step 2: Sanitize Logs

```typescript
// src/gamma/logging.ts
// Never log raw content or API keys

function logGeneration(request: any, result: any) {
  console.log(JSON.stringify({
    event: "gamma_generation",
    timestamp: new Date().toISOString(),
    generationId: result.generationId,
    outputFormat: request.outputFormat,
    contentLength: request.content?.length,
    // NEVER log: content (may have PII), apiKey
    status: result.status,
    creditsUsed: result.creditsUsed,
  }));
}
```

### Step 3: Export File Handling

```typescript
// src/gamma/exports.ts
// Export URLs are temporary — download and store securely

import { writeFile } from "node:fs/promises";
import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";

async function archiveExport(
  exportUrl: string,
  metadata: { generationId: string; userId: string }
) {
  // Download immediately — URLs expire
  const res = await fetch(exportUrl);
  if (!res.ok) throw new Error(`Export download failed: ${res.status}`);
  const buffer = Buffer.from(await res.arrayBuffer());

  // Store with encryption
  const s3 = new S3Client({ region: "us-east-1" });
  const key = `gamma-exports/${metadata.userId}/${metadata.generationId}.pdf`;

  await s3.send(new PutObjectCommand({
    Bucket: process.env.EXPORTS_BUCKET!,
    Key: key,
    Body: buffer,
    ContentType: "application/pdf",
    ServerSideEncryption: "aws:kms",
    Metadata: {
      generationId: metadata.generationId,
      archivedAt: new Date().toISOString(),
    },
  }));

  console.log(`Archived: s3://${process.env.EXPORTS_BUCKET}/${key}`);
}
```

### Step 4: Data Retention Policy

```typescript
// src/gamma/retention.ts
interface RetentionPolicy {
  exportMaxDays: number;     // Delete local export copies
  logRetentionDays: number;  // Anonymize generation logs
  promptRetentionDays: number; // Delete stored prompts
}

const POLICY: RetentionPolicy = {
  exportMaxDays: 90,       // Keep exports 90 days
  logRetentionDays: 30,    // Anonymize logs after 30 days
  promptRetentionDays: 7,  // Delete prompts after 7 days
};

async function enforceRetention() {
  const cutoff = new Date();

  // Delete old exports from S3
  cutoff.setDate(cutoff.getDate() - POLICY.exportMaxDays);
  await deleteOldExports(cutoff);

  // Anonymize old logs
  cutoff.setDate(cutoff.getDate() + POLICY.exportMaxDays - POLICY.logRetentionDays);
  await anonymizeLogs(cutoff);

  // Delete stored prompts
  cutoff.setDate(cutoff.getDate() + POLICY.logRetentionDays - POLICY.promptRetentionDays);
  await deletePrompts(cutoff);
}
```

### Step 5: GDPR Request Handling

```typescript
// Handle data subject access/erasure requests
async function handleGdprRequest(
  type: "access" | "erasure",
  userId: string
) {
  if (type === "access") {
    // Return all data we store about this user
    return {
      generations: await db.generations.findMany({ where: { userId } }),
      exports: await listS3Objects(`gamma-exports/${userId}/`),
      // Note: data stored IN Gamma's workspace is Gamma's responsibility
      // Direct user to gamma.app to access/delete their workspace data
    };
  }

  if (type === "erasure") {
    // Delete from our systems
    await db.generations.deleteMany({ where: { userId } });
    await deleteS3Prefix(`gamma-exports/${userId}/`);
    // Instruct user to delete Gamma workspace data at gamma.app
    return { deleted: true, note: "Delete Gamma workspace data at gamma.app" };
  }
}
```

## Compliance Checklist

- [ ] Content sanitized before sending to Gamma API (PII removed if not needed)
- [ ] API keys never logged
- [ ] Export URLs downloaded promptly and stored encrypted
- [ ] Retention policies defined and enforced
- [ ] GDPR access/erasure request process documented
- [ ] User consent obtained for AI processing of their content
- [ ] Gamma DPA signed (if required by your jurisdiction)
- [ ] Logs sanitized (no raw content or PII)

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Export URL expired | Downloaded too late | Download immediately on generation completion |
| PII in logs | Missing sanitization | Add log sanitization middleware |
| Retention job failed | Scheduler stopped | Monitor cron job health |
| GDPR request incomplete | Gamma workspace not addressed | Direct user to gamma.app for workspace data |

## Resources

- [Gamma Privacy Policy](https://gamma.app/privacy)
- [Gamma Terms of Service](https://gamma.app/tos)
- [GDPR Compliance Guide](https://gdpr.eu/)

## Next Steps

Proceed to `gamma-enterprise-rbac` for access control.
