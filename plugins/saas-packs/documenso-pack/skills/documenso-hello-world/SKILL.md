---
name: documenso-hello-world
description: |
  Create a minimal working Documenso example.
  Use when starting a new Documenso integration, testing your setup,
  or learning basic document signing patterns.
  Trigger with phrases like "documenso hello world", "documenso example",
  "documenso quick start", "simple documenso code", "first document".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, documenso, testing]

---
# Documenso Hello World

## Overview

Minimal working example that creates a document, adds a recipient with a signature field, and sends it for signing — all in one script. Uses the Documenso TypeScript SDK (v2 API) with a Python equivalent.

## Prerequisites

- Completed `documenso-install-auth` setup
- Valid API key in `DOCUMENSO_API_KEY` environment variable
- A PDF file to upload (or generate a test one below)

## Instructions

### Step 1: Generate a Test PDF (Optional)

If you don't have a PDF handy:

```bash
npm install pdf-lib
```

```typescript
// generate-test-pdf.ts
import { PDFDocument, StandardFonts } from "pdf-lib";
import { writeFileSync } from "fs";

async function createTestPdf() {
  const pdf = PDFDocument.create();
  const page = (await pdf).addPage([612, 792]); // US Letter
  const font = await (await pdf).embedFont(StandardFonts.Helvetica);
  page.drawText("Please sign below:", { x: 50, y: 700, size: 16, font });
  const bytes = await (await pdf).save();
  writeFileSync("test-contract.pdf", bytes);
  console.log("Created test-contract.pdf");
}
createTestPdf();
```

### Step 2: Complete Signing Workflow (TypeScript)

```typescript
// documenso-hello.ts
import { Documenso } from "@documenso/sdk-typescript";
import { readFileSync } from "fs";

async function main() {
  const client = new Documenso({
    apiKey: process.env.DOCUMENSO_API_KEY!,
  });

  // 1. Create a document
  const doc = await client.documents.createV0({
    title: "Hello World Contract",
  });
  console.log(`Document created: ID ${doc.documentId}`);

  // 2. Upload the PDF
  const pdfBuffer = readFileSync("test-contract.pdf");
  await client.documents.setFileV0(doc.documentId, {
    file: new Blob([pdfBuffer], { type: "application/pdf" }),
  });

  // 3. Add a recipient (signer)
  const recipient = await client.documentsRecipients.createV0(doc.documentId, {
    email: "signer@example.com",
    name: "Jane Doe",
    role: "SIGNER",
  });
  console.log(`Recipient added: ${recipient.recipientId}`);

  // 4. Add a signature field at specific coordinates
  await client.documentsFields.createV0(doc.documentId, {
    recipientId: recipient.recipientId,
    type: "SIGNATURE",
    pageNumber: 1,
    pageX: 50,    // X position (left offset, percentage-based 0-100)
    pageY: 80,    // Y position (top offset, percentage-based 0-100)
    pageWidth: 30, // Width as percentage of page
    pageHeight: 5, // Height as percentage of page
  });

  // 5. Send for signing
  await client.documents.sendV0(doc.documentId);
  console.log("Document sent for signing!");
}

main().catch(console.error);
```

Run: `npx tsx documenso-hello.ts`

### Step 3: Python Equivalent

```python
# documenso_hello.py
import os
from documenso_sdk_python import Documenso

client = Documenso(api_key=os.environ["DOCUMENSO_API_KEY"])

# Create document
doc = client.documents.create_v0(title="Hello World Contract")
print(f"Document created: ID {doc.document_id}")

# Upload PDF
with open("test-contract.pdf", "rb") as f:
    client.documents.set_file_v0(doc.document_id, file=f.read())

# Add recipient
recipient = client.documents_recipients.create_v0(
    doc.document_id,
    email="signer@example.com",
    name="Jane Doe",
    role="SIGNER",
)

# Add signature field
client.documents_fields.create_v0(
    doc.document_id,
    recipient_id=recipient.recipient_id,
    type="SIGNATURE",
    page_number=1,
    page_x=50,
    page_y=80,
    page_width=30,
    page_height=5,
)

# Send for signing
client.documents.send_v0(doc.document_id)
print("Document sent for signing!")
```

### Step 4: REST API Equivalent (curl)

```bash
# Create document
DOC=$(curl -s -X POST "https://app.documenso.com/api/v1/documents" \
  -H "Authorization: Bearer $DOCUMENSO_API_KEY" \
  -F "title=Hello World Contract" \
  -F "file=@test-contract.pdf" | jq -r '.id')

# Add recipient
RECIP=$(curl -s -X POST "https://app.documenso.com/api/v1/documents/$DOC/recipients" \
  -H "Authorization: Bearer $DOCUMENSO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email":"signer@example.com","name":"Jane Doe","role":"SIGNER"}' \
  | jq -r '.id')

# Send
curl -s -X POST "https://app.documenso.com/api/v1/documents/$DOC/send" \
  -H "Authorization: Bearer $DOCUMENSO_API_KEY"
```

## Field Types Reference

| Type | Description | Common Use |
|------|-------------|------------|
| `SIGNATURE` | Electronic signature capture | Contract signing |
| `FREE_SIGNATURE` | Hand-drawn / upload signature | Notarized documents |
| `INITIALS` | Initials field | Page-by-page acknowledgment |
| `NAME` | Auto-filled full name | Identity confirmation |
| `EMAIL` | Auto-filled email address | Contact verification |
| `DATE` | Date picker / auto-date | Timestamp of signing |
| `TEXT` | Free text input | Custom fields (title, address) |
| `NUMBER` | Numeric input | Amounts, quantities |
| `CHECKBOX` | Boolean check | Terms acceptance |
| `DROPDOWN` | Select from options | Role selection |
| `RADIO` | Radio button group | Single-choice options |

## Document Lifecycle

```
DRAFT → (send) → PENDING → (all sign) → COMPLETED
                          → (reject)  → REJECTED
       → (cancel) →                     CANCELLED
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid or missing API key | Verify `DOCUMENSO_API_KEY` is set |
| `File too large` | PDF exceeds upload limit | Compress PDF or check plan limits |
| `Invalid field position` | pageX/pageY out of range | Use 0-100 range (percentage-based) |
| `Recipient exists` | Duplicate email on document | Update existing recipient instead |
| `Cannot send DRAFT` | Missing required fields | Add at least one recipient + field |

## Resources

- [Documenso Getting Started](https://docs.documenso.com/developers)
- [TypeScript SDK Docs](https://github.com/documenso/sdk-typescript)
- [API Reference (OpenAPI)](https://openapi.documenso.com/)
- [Field Types Documentation](https://docs.documenso.com/users/documents/fields)

## Next Steps

Proceed to `documenso-local-dev-loop` for development workflow setup or `documenso-core-workflow-a` for production document management.
