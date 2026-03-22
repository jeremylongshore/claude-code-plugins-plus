---
name: documenso-data-handling
description: |
  Handle document data, signatures, and PII in Documenso integrations.
  Use when managing document lifecycle, handling signed PDFs,
  or implementing data retention policies.
  Trigger with phrases like "documenso data", "signed document",
  "document retention", "documenso PII", "download signed pdf".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, documenso, documenso-data]

---
# Documenso Data Handling

## Overview

Best practices for handling documents, signatures, and PII in Documenso integrations. Covers downloading signed PDFs, data retention, GDPR compliance, and secure storage. Note: Documenso cloud stores documents in PostgreSQL by default; self-hosted gives you full control.

## Prerequisites

- Understanding of data protection regulations (GDPR, CCPA)
- Secure storage infrastructure (S3, GCS, or local encrypted storage)
- Completed `documenso-install-auth` setup

## Document Lifecycle

```
DRAFT ──send()──→ PENDING ──all sign──→ COMPLETED
                      │
                      ├──reject()──→ REJECTED
                      └──cancel()──→ CANCELLED

Data handling implications:
- DRAFT: mutable, can delete freely
- PENDING: immutable document, but status changes
- COMPLETED: signed PDF available for download, archive
- REJECTED/CANCELLED: cleanup candidate
```

## Instructions

### Step 1: Download Signed Documents

```typescript
import { Documenso } from "@documenso/sdk-typescript";
import { writeFile } from "node:fs/promises";

const client = new Documenso({ apiKey: process.env.DOCUMENSO_API_KEY! });

async function downloadSignedPdf(documentId: number, outputPath: string) {
  // Verify document is completed
  const doc = await client.documents.getV0(documentId);
  if (doc.status !== "COMPLETED") {
    throw new Error(`Document ${documentId} is ${doc.status}, not COMPLETED`);
  }

  // Download via v1 REST API (SDK may not expose download directly)
  const res = await fetch(
    `https://app.documenso.com/api/v1/documents/${documentId}/download`,
    { headers: { Authorization: `Bearer ${process.env.DOCUMENSO_API_KEY}` } }
  );
  if (!res.ok) throw new Error(`Download failed: ${res.status}`);

  const buffer = Buffer.from(await res.arrayBuffer());
  await writeFile(outputPath, buffer);
  console.log(`Saved signed PDF: ${outputPath} (${buffer.length} bytes)`);
}
```

### Step 2: PII Handling

```typescript
// Identify PII in Documenso data
interface RecipientPII {
  email: string;    // PII — must be protected
  name: string;     // PII — must be protected
  role: string;     // Not PII
  signingStatus: string; // Not PII
}

// Sanitize before logging
function sanitizeForLogging(payload: any): any {
  const sanitized = { ...payload };
  if (sanitized.recipients) {
    sanitized.recipients = sanitized.recipients.map((r: any) => ({
      ...r,
      email: r.email.replace(/^(.{2}).*(@.*)$/, "$1***$2"),
      name: "[REDACTED]",
    }));
  }
  return sanitized;
}

// Usage: safe to log
console.log("Webhook received:", JSON.stringify(sanitizeForLogging(payload)));
// Output: { email: "ja***@example.com", name: "[REDACTED]" }
```

### Step 3: Data Retention Policy

```typescript
// src/retention/documenso-cleanup.ts
import { Documenso } from "@documenso/sdk-typescript";

interface RetentionPolicy {
  draftMaxAgeDays: number;      // Delete abandoned drafts
  completedArchiveDays: number; // Archive completed docs
  retainCompletedDays: number;  // Keep completed in Documenso
}

const POLICY: RetentionPolicy = {
  draftMaxAgeDays: 30,
  completedArchiveDays: 7,    // Archive to S3 within 7 days
  retainCompletedDays: 365,   // Keep in Documenso for 1 year
};

async function enforceRetention(client: Documenso) {
  const { documents } = await client.documents.findV0({ page: 1, perPage: 100 });
  const now = Date.now();

  for (const doc of documents) {
    const ageDays = (now - new Date(doc.createdAt).getTime()) / (1000 * 60 * 60 * 24);

    // Delete old drafts
    if (doc.status === "DRAFT" && ageDays > POLICY.draftMaxAgeDays) {
      await client.documents.deleteV0(doc.id);
      console.log(`Deleted abandoned draft: ${doc.title} (${ageDays.toFixed(0)} days old)`);
    }

    // Archive completed documents
    if (doc.status === "COMPLETED" && ageDays > POLICY.completedArchiveDays) {
      await archiveToS3(doc.id, doc.title);
      console.log(`Archived: ${doc.title}`);
    }
  }
}
```

### Step 4: GDPR Data Subject Requests

```typescript
// Handle GDPR access and erasure requests
async function handleDataSubjectRequest(
  client: Documenso,
  type: "access" | "erasure",
  subjectEmail: string
) {
  const { documents } = await client.documents.findV0({ page: 1, perPage: 100 });

  // Find all documents involving this person
  const subjectDocs = documents.filter((doc: any) =>
    doc.recipients?.some((r: any) => r.email === subjectEmail)
  );

  if (type === "access") {
    // Return all data associated with this person
    return {
      documentsCount: subjectDocs.length,
      documents: subjectDocs.map((d: any) => ({
        title: d.title,
        status: d.status,
        createdAt: d.createdAt,
        role: d.recipients.find((r: any) => r.email === subjectEmail)?.role,
      })),
    };
  }

  if (type === "erasure") {
    // Delete/anonymize where legally permissible
    // Note: completed, signed documents may need to be retained for legal compliance
    const deletable = subjectDocs.filter((d: any) => d.status === "DRAFT");
    for (const doc of deletable) {
      await client.documents.deleteV0(doc.id);
    }
    return {
      deleted: deletable.length,
      retained: subjectDocs.length - deletable.length,
      retainedReason: "Completed documents retained for legal compliance",
    };
  }
}
```

### Step 5: Secure Storage for Downloaded PDFs

```typescript
import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";
import crypto from "crypto";

const s3 = new S3Client({ region: "us-east-1" });

async function archiveToS3(documentId: number, title: string) {
  // Download signed PDF
  const res = await fetch(
    `https://app.documenso.com/api/v1/documents/${documentId}/download`,
    { headers: { Authorization: `Bearer ${process.env.DOCUMENSO_API_KEY}` } }
  );
  const buffer = Buffer.from(await res.arrayBuffer());

  // Upload with server-side encryption
  const key = `signed-documents/${documentId}-${Date.now()}.pdf`;
  await s3.send(new PutObjectCommand({
    Bucket: process.env.ARCHIVE_BUCKET!,
    Key: key,
    Body: buffer,
    ContentType: "application/pdf",
    ServerSideEncryption: "aws:kms",
    Metadata: {
      documentId: String(documentId),
      title,
      archivedAt: new Date().toISOString(),
      checksum: crypto.createHash("sha256").update(buffer).digest("hex"),
    },
  }));

  console.log(`Archived to s3://${process.env.ARCHIVE_BUCKET}/${key}`);
}
```

## Data Classification

| Data Type | Classification | Retention | Handling |
|-----------|---------------|-----------|----------|
| Signed PDF | Legal record | Per regulation (often 7+ years) | Encrypted archive |
| Recipient email/name | PII | Duration of business relationship | Sanitize in logs |
| API keys | Secret | Active use only | Secret manager, never logged |
| Webhook payloads | Contains PII | 30 days max | Anonymize after processing |
| Audit trail | Compliance record | Per regulation | Immutable storage |

## Error Handling

| Data Issue | Cause | Solution |
|------------|-------|----------|
| Download failed | Document not COMPLETED | Check status before download |
| Storage permission denied | Wrong bucket policy | Verify IAM permissions |
| GDPR request incomplete | Pagination not handled | Iterate all pages of documents |
| Retention job failed | API error during deletion | Retry with backoff, log failures |

## Resources

- [GDPR Requirements](https://gdpr.eu/)
- [Documenso Self-Hosting](https://docs.documenso.com/developers/self-hosting)
- [AWS S3 Server-Side Encryption](https://docs.aws.amazon.com/AmazonS3/latest/userguide/serv-side-encryption.html)

## Next Steps

For enterprise RBAC, see `documenso-enterprise-rbac`.
