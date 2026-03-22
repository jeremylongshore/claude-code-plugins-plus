---
name: documenso-core-workflow-b
description: |
  Implement Documenso template-based workflows and direct signing links.
  Use when creating reusable templates, generating documents from templates,
  or implementing direct signing experiences.
  Trigger with phrases like "documenso template", "signing link",
  "direct template", "reusable document", "template workflow".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, documenso, workflow]

---
# Documenso Core Workflow B: Templates & Direct Signing

## Overview

Create reusable templates, generate documents from templates with prefilled fields, and implement direct signing links for public/anonymous signers. Templates define the PDF, fields, and recipient roles once — then stamp out documents on demand.

## Prerequisites

- Completed `documenso-core-workflow-a`
- At least one PDF uploaded to Documenso as a template
- Understanding of recipient roles and field types

## Instructions

### Step 1: Create a Template via Dashboard

Templates are created in the Documenso UI:

1. Navigate to **Templates** in the sidebar.
2. Click **Create Template** and upload a PDF.
3. Add **placeholder recipients** (e.g., "Signer 1", "Approver") — these become roles that get filled when creating documents from the template.
4. Place fields on the PDF and assign them to placeholder recipients.
5. Save the template and note the **template ID** from the URL.

### Step 2: Create Document from Template (v1 REST API)

```typescript
// The v1 API has a dedicated template endpoint
const templateId = 42; // From the dashboard URL

const res = await fetch(
  `https://app.documenso.com/api/v1/templates/${templateId}/create-document`,
  {
    method: "POST",
    headers: {
      Authorization: `Bearer ${process.env.DOCUMENSO_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      title: "Service Agreement — Acme Corp",
      recipients: [
        {
          email: "ceo@acme.com",
          name: "Alice CEO",
          role: "SIGNER",
        },
      ],
      // Optionally prefill fields by their IDs
      prefillFields: [
        { id: "field_abc123", value: "2026-03-22" },
        { id: "field_def456", value: "Acme Corporation" },
      ],
    }),
  }
);

const document = await res.json();
console.log(`Created document ${document.documentId} from template ${templateId}`);
```

### Step 3: Template Workflow Patterns

```typescript
// Pattern: Batch document generation from template
async function generateContracts(
  templateId: number,
  clients: Array<{ email: string; name: string; company: string }>
) {
  const results = [];

  for (const client of clients) {
    const res = await fetch(
      `https://app.documenso.com/api/v1/templates/${templateId}/create-document`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${process.env.DOCUMENSO_API_KEY}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          title: `Service Agreement — ${client.company}`,
          recipients: [
            { email: client.email, name: client.name, role: "SIGNER" },
          ],
        }),
      }
    );

    const doc = await res.json();

    // Send immediately after creation
    await fetch(
      `https://app.documenso.com/api/v1/documents/${doc.documentId}/send`,
      {
        method: "POST",
        headers: { Authorization: `Bearer ${process.env.DOCUMENSO_API_KEY}` },
      }
    );

    results.push({ documentId: doc.documentId, client: client.email });
  }

  return results;
}
```

### Step 4: Direct Signing Links

Direct links let anyone sign without receiving an email — perfect for public forms, walk-in signers, or embedded flows.

**Setup in Dashboard:**
1. Open a template.
2. Click **Direct Link** in template settings.
3. Choose which recipient role the direct link signer fills.
4. Copy the generated URL.

**Direct Link URL format:**

```
https://app.documenso.com/sign/direct/{token}
```

**Embedding a Direct Link in an iframe:**

```html
<iframe
  src="https://app.documenso.com/sign/direct/abc123token"
  width="100%"
  height="800"
  frameborder="0"
  allow="clipboard-write"
></iframe>
```

### Step 5: Embedded Signing with React

```bash
npm install @documenso/embed-react
```

```tsx
// DirectSigningPage.tsx
import { EmbedDirectTemplate } from "@documenso/embed-react";

export function DirectSigningPage() {
  return (
    <EmbedDirectTemplate
      token="your-direct-link-token"
      host="https://app.documenso.com"
      // Pre-fill recipient data
      name="Jane Doe"
      email="jane@example.com"
      // Lock pre-filled fields so signer can't change them
      lockName={true}
      lockEmail={true}
      // Callbacks
      onDocumentReady={() => console.log("Document loaded")}
      onDocumentCompleted={() => console.log("Signing complete!")}
      onDocumentError={(err) => console.error("Error:", err)}
    />
  );
}
```

### Step 6: Embedded Authoring (Document Editor)

Let users create and edit documents directly in your app:

```tsx
import { EmbedCreateDocument } from "@documenso/embed-react";

export function CreateDocumentPage() {
  return (
    <EmbedCreateDocument
      presignToken="presign-token-from-api"
      host="https://app.documenso.com"
      onDocumentCreated={(doc) => {
        console.log(`Document ${doc.documentId} created`);
      }}
    />
  );
}
```

Presign tokens are obtained from the API and expire after 1 hour by default.

### Step 7: v2 Envelope API (Multi-Document)

The v2 API uses "envelopes" that can contain multiple documents:

```typescript
// Create envelope with multipart/form-data
const form = new FormData();
form.append("payload.title", "Multi-Doc Envelope");
form.append("payload.type", "DOCUMENT"); // or "TEMPLATE"
form.append("files", pdfBlob1, "contract.pdf");
form.append("files", pdfBlob2, "appendix.pdf");

const envelope = await fetch("https://app.documenso.com/api/v2/envelope/create", {
  method: "POST",
  headers: { Authorization: `Bearer ${process.env.DOCUMENSO_API_KEY}` },
  body: form,
});

const { envelopeId } = await envelope.json();

// Distribute (send) the envelope
await fetch("https://app.documenso.com/api/v2/envelope/distribute", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${process.env.DOCUMENSO_API_KEY}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ envelopeId }),
});
```

## Template vs Direct Document Comparison

| Feature | Document (ad-hoc) | Template | Direct Link |
|---------|-------------------|----------|-------------|
| PDF upload | Every time | Once | Once (via template) |
| Field placement | Every time | Once | Once (via template) |
| Recipient known upfront | Yes | Yes | No |
| Public/anonymous signing | No | No | Yes |
| Batch generation | Manual | API call per client | N/A |
| Embedding | SignDocument | DirectTemplate | iframe/embed |

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Template not found (404) | Invalid template ID or deleted | Verify ID in dashboard URL |
| Recipient mismatch | Wrong number vs template roles | Match template's placeholder roles |
| Field not found for prefill | Invalid `prefillFields[].id` | GET template first, inspect field IDs |
| Direct link disabled | Feature not enabled on template | Enable in template settings |
| Presign token expired | Token older than 1 hour | Request a new presign token |

## Resources

- [Templates User Guide](https://docs.documenso.com/users/templates)
- [Direct Link Signing](https://docs.documenso.com/users/direct-links)
- [Embedding Documentation](https://docs.documenso.com/developers/embedding)
- [React Embed SDK](https://docs.documenso.com/developers/embedding/react)
- [v2 Envelope API](https://openapi.documenso.com/)

## Next Steps

For error handling patterns, see `documenso-common-errors`.
