---
name: documenso-core-workflow-a
description: |
  Implement Documenso document creation and recipient management workflows.
  Use when creating documents, managing recipients, adding signature fields,
  or building signing workflows with Documenso.
  Trigger with phrases like "documenso document", "create document",
  "add recipient", "documenso signer", "signature field".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, documenso, workflow]

---
# Documenso Core Workflow A: Document Creation & Recipients

## Overview

Complete workflow for creating documents, managing recipients with different roles, positioning fields, and controlling signing order. Covers both the SDK and v1 REST API for document-centric operations.

## Prerequisites

- Completed `documenso-install-auth` setup
- Understanding of `documenso-sdk-patterns`
- PDF file ready for signing

## Instructions

### Step 1: Create a Document with the SDK

```typescript
import { Documenso } from "@documenso/sdk-typescript";
import { readFileSync } from "fs";

const client = new Documenso({ apiKey: process.env.DOCUMENSO_API_KEY! });

// Create document shell
const doc = await client.documents.createV0({
  title: "Service Agreement — Q1 2026",
});

// Upload PDF
const pdf = readFileSync("./contracts/service-agreement.pdf");
await client.documents.setFileV0(doc.documentId, {
  file: new Blob([pdf], { type: "application/pdf" }),
});
```

### Step 2: Recipient Roles

Documenso supports these recipient roles:

| Role | Behavior |
|------|----------|
| `SIGNER` | Must complete all assigned fields to finish |
| `VIEWER` | Receives a copy but takes no action |
| `APPROVER` | Must approve before signers can proceed |
| `CC` | Receives a completed copy after all signatures |

```typescript
// Add multiple recipients with roles
const signer = await client.documentsRecipients.createV0(doc.documentId, {
  email: "ceo@acme.com",
  name: "Alice CEO",
  role: "SIGNER",
});

const approver = await client.documentsRecipients.createV0(doc.documentId, {
  email: "legal@acme.com",
  name: "Legal Team",
  role: "APPROVER",
});

const cc = await client.documentsRecipients.createV0(doc.documentId, {
  email: "records@acme.com",
  name: "Records",
  role: "CC",
});
```

### Step 3: Signing Order

Control the sequence in which recipients act. Lower numbers go first.

```typescript
// Sequential signing: legal approves, then CEO signs
await client.documentsRecipients.createV0(doc.documentId, {
  email: "legal@acme.com",
  name: "Legal",
  role: "APPROVER",
  signingOrder: 1, // Goes first
});

await client.documentsRecipients.createV0(doc.documentId, {
  email: "ceo@acme.com",
  name: "CEO",
  role: "SIGNER",
  signingOrder: 2, // Goes after legal approves
});
```

### Step 4: Add Fields to Document

Field coordinates use **percentage-based positioning** (0-100 for both X and Y axes). The origin is the top-left corner of the page.

```typescript
// Signature field — bottom of page 1
await client.documentsFields.createV0(doc.documentId, {
  recipientId: signer.recipientId,
  type: "SIGNATURE",
  pageNumber: 1,
  pageX: 10,      // 10% from left
  pageY: 85,      // 85% from top
  pageWidth: 30,  // 30% of page width
  pageHeight: 5,  // 5% of page height
});

// Date field — next to signature
await client.documentsFields.createV0(doc.documentId, {
  recipientId: signer.recipientId,
  type: "DATE",
  pageNumber: 1,
  pageX: 60,
  pageY: 85,
  pageWidth: 20,
  pageHeight: 3,
});

// Name field — auto-filled from recipient
await client.documentsFields.createV0(doc.documentId, {
  recipientId: signer.recipientId,
  type: "NAME",
  pageNumber: 1,
  pageX: 10,
  pageY: 78,
  pageWidth: 30,
  pageHeight: 3,
});

// Text field — custom input (e.g., title/position)
await client.documentsFields.createV0(doc.documentId, {
  recipientId: signer.recipientId,
  type: "TEXT",
  pageNumber: 1,
  pageX: 60,
  pageY: 78,
  pageWidth: 30,
  pageHeight: 3,
});
```

### Step 5: Multi-Page Document with Multiple Signers

```typescript
async function createMultiSignerContract(
  pdfPath: string,
  signers: Array<{ email: string; name: string; signPage: number }>
) {
  const client = new Documenso({ apiKey: process.env.DOCUMENSO_API_KEY! });
  const doc = await client.documents.createV0({ title: "Multi-Party Agreement" });
  const pdf = readFileSync(pdfPath);
  await client.documents.setFileV0(doc.documentId, {
    file: new Blob([pdf], { type: "application/pdf" }),
  });

  for (let i = 0; i < signers.length; i++) {
    const s = signers[i];
    const recip = await client.documentsRecipients.createV0(doc.documentId, {
      email: s.email,
      name: s.name,
      role: "SIGNER",
      signingOrder: i + 1,
    });

    // Each signer gets signature + date on their assigned page
    await client.documentsFields.createV0(doc.documentId, {
      recipientId: recip.recipientId,
      type: "SIGNATURE",
      pageNumber: s.signPage,
      pageX: 10, pageY: 80, pageWidth: 30, pageHeight: 5,
    });
    await client.documentsFields.createV0(doc.documentId, {
      recipientId: recip.recipientId,
      type: "DATE",
      pageNumber: s.signPage,
      pageX: 60, pageY: 80, pageWidth: 20, pageHeight: 3,
    });
  }

  await client.documents.sendV0(doc.documentId);
  return doc.documentId;
}
```

### Step 6: Document Metadata and Settings

```typescript
// v1 REST API: create document with metadata
const res = await fetch("https://app.documenso.com/api/v1/documents", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${process.env.DOCUMENSO_API_KEY}`,
  },
  body: (() => {
    const form = new FormData();
    form.append("title", "NDA — Confidential");
    form.append("file", new Blob([pdf], { type: "application/pdf" }));
    return form;
  })(),
});
const document = await res.json();
```

### Step 7: Query and Filter Documents

```typescript
// List documents with pagination
const { documents } = await client.documents.findV0({
  page: 1,
  perPage: 20,
  orderByColumn: "createdAt",
  orderByDirection: "desc",
});

// Get single document with all details
const detail = await client.documents.getV0(documentId);
console.log(`Status: ${detail.status}`);   // DRAFT | PENDING | COMPLETED
console.log(`Recipients: ${detail.recipients.length}`);
console.log(`Fields: ${detail.fields.length}`);
```

## Document Status Flow

```
DRAFT ──send()──→ PENDING ──all sign──→ COMPLETED
                      │
                      ├──reject()──→ REJECTED
                      └──cancel()──→ CANCELLED
```

Only `DRAFT` documents can be modified (add recipients, fields, change PDF).

## Error Handling

| Error | HTTP | Cause | Solution |
|-------|------|-------|----------|
| Document not found | 404 | Invalid document ID | Verify ID with `findV0()` |
| Recipient exists | 400 | Duplicate email on same doc | Update existing with `updateV0()` |
| Invalid field position | 400 | pageX/pageY > 100 or < 0 | Use percentage values 0-100 |
| Cannot modify sent doc | 400 | Document status is PENDING | Create new document or cancel first |
| File too large | 413 | PDF exceeds plan limit | Compress PDF (plan limits vary) |

## Resources

- [Documents API (SDK)](https://github.com/documenso/sdk-typescript/blob/main/docs/sdks/documents/README.md)
- [Recipients API (SDK)](https://github.com/documenso/sdk-typescript/blob/main/docs/sdks/documentsrecipients/README.md)
- [Fields API (SDK)](https://github.com/documenso/sdk-typescript/blob/main/docs/sdks/documentsfields/README.md)
- [Field Types](https://docs.documenso.com/users/documents/fields)

## Next Steps

For template-based workflows and direct signing links, see `documenso-core-workflow-b`.
