# Documenso Core Workflow A: Document Creation & Recipients - Implementation Guide

## Instructions

### Step 1: Create Document with PDF Upload

```typescript
import { Documenso } from "@documenso/sdk-typescript";
import { openAsBlob } from "node:fs";

const documenso = new Documenso({
  apiKey: process.env.DOCUMENSO_API_KEY ?? "",
});

async function createDocument(
  title: string,
  pdfPath: string
): Promise<string> {
  const pdfBlob = await openAsBlob(pdfPath);

  const document = await documenso.documents.createV0({
    title,
    file: pdfBlob,
  });

  console.log(`Created document: ${document.documentId}`);
  return document.documentId!;
}
```

### Step 2: Add Multiple Recipients with Signing Order

```typescript
interface RecipientInput {
  email: string;
  name: string;
  role: "SIGNER" | "VIEWER" | "APPROVER" | "CC";
  signingOrder?: number;
}

async function addRecipients(
  documentId: string,
  recipients: RecipientInput[]
): Promise<Map<string, string>> {
  const recipientMap = new Map<string, string>(); // email -> recipientId

  for (const recipient of recipients) {
    const result = await documenso.documentsRecipients.createV0({
      documentId,
      email: recipient.email,
      name: recipient.name,
      role: recipient.role,
      signingOrder: recipient.signingOrder,
    });

    recipientMap.set(recipient.email, result.recipientId!);
    console.log(`Added ${recipient.role}: ${recipient.email}`);
  }

  return recipientMap;
}

// Example: Sequential signing order
const recipients: RecipientInput[] = [
  { email: "employee@company.com", name: "John Employee", role: "SIGNER", signingOrder: 1 },
  { email: "manager@company.com", name: "Jane Manager", role: "APPROVER", signingOrder: 2 },
  { email: "hr@company.com", name: "HR Department", role: "CC", signingOrder: 3 },
];
```

### Step 3: Add Signature Fields

```typescript
interface FieldInput {
  recipientId: string;
  type: "SIGNATURE" | "INITIALS" | "NAME" | "EMAIL" | "DATE" | "TEXT" | "CHECKBOX";
  page: number;
  x: number;
  y: number;
  width?: number;
  height?: number;
  required?: boolean;
  placeholder?: string;
}

async function addFields(
  documentId: string,
  fields: FieldInput[]
): Promise<string[]> {
  const fieldIds: string[] = [];

  for (const field of fields) {
    const result = await documenso.documentsFields.createV0({
      documentId,
      recipientId: field.recipientId,
      type: field.type,
      page: field.page,
      positionX: field.x,
      positionY: field.y,
      width: field.width ?? getDefaultWidth(field.type),
      height: field.height ?? getDefaultHeight(field.type),
    });

    fieldIds.push(result.fieldId!);
    console.log(`Added ${field.type} field on page ${field.page}`);
  }

  return fieldIds;
}

function getDefaultWidth(type: string): number {
  const widths: Record<string, number> = {
    SIGNATURE: 200,
    INITIALS: 80,
    NAME: 180,
    EMAIL: 200,
    DATE: 120,
    TEXT: 200,
    CHECKBOX: 24,
  };
  return widths[type] ?? 150;
}

function getDefaultHeight(type: string): number {
  const heights: Record<string, number> = {
    SIGNATURE: 60,
    INITIALS: 40,
    NAME: 30,
    EMAIL: 30,
    DATE: 30,
    TEXT: 30,
    CHECKBOX: 24,
  };
  return heights[type] ?? 30;
}
```

### Step 4: Complete Document Creation Workflow

```typescript
interface CreateSigningDocumentInput {
  title: string;
  pdfPath: string;
  recipients: Array<{
    email: string;
    name: string;
    role: "SIGNER" | "VIEWER" | "APPROVER" | "CC";
    signingOrder?: number;
    fields: Array<{
      type: "SIGNATURE" | "INITIALS" | "NAME" | "EMAIL" | "DATE" | "TEXT";
      page: number;
      x: number;
      y: number;
    }>;
  }>;
  sendImmediately?: boolean;
}

async function createSigningDocument(
  input: CreateSigningDocumentInput
): Promise<{ documentId: string; signingUrls: Map<string, string> }> {
  // Step 1: Create document with PDF
  const pdfBlob = await openAsBlob(input.pdfPath);
  const document = await documenso.documents.createV0({
    title: input.title,
    file: pdfBlob,
  });
  const documentId = document.documentId!;

  // Step 2: Add recipients and collect their IDs
  const recipientIds = new Map<string, string>();

  for (const recipient of input.recipients) {
    const result = await documenso.documentsRecipients.createV0({
      documentId,
      email: recipient.email,
      name: recipient.name,
      role: recipient.role,
      signingOrder: recipient.signingOrder,
    });
    recipientIds.set(recipient.email, result.recipientId!);
  }

  // Step 3: Add fields for each recipient
  for (const recipient of input.recipients) {
    const recipientId = recipientIds.get(recipient.email)!;

    for (const field of recipient.fields) {
      await documenso.documentsFields.createV0({
        documentId,
        recipientId,
        type: field.type,
        page: field.page,
        positionX: field.x,
        positionY: field.y,
        width: getDefaultWidth(field.type),
        height: getDefaultHeight(field.type),
      });
    }
  }

  // Step 4: Send document if requested
  if (input.sendImmediately) {
    await documenso.documents.sendV0({ documentId });
    console.log("Document sent to all recipients!");
  }

  // Step 5: Get signing URLs
  const signingUrls = new Map<string, string>();
  const doc = await documenso.documents.getV0({ documentId });

  for (const recipient of doc.recipients ?? []) {
    if (recipient.signingUrl) {
      signingUrls.set(recipient.email!, recipient.signingUrl);
    }
  }

  return { documentId, signingUrls };
}

// Example usage
const result = await createSigningDocument({
  title: "Employment Contract",
  pdfPath: "./contracts/employment.pdf",
  recipients: [
    {
      email: "newhire@company.com",
      name: "New Employee",
      role: "SIGNER",
      signingOrder: 1,
      fields: [
        { type: "SIGNATURE", page: 3, x: 100, y: 600 },
        { type: "DATE", page: 3, x: 350, y: 600 },
        { type: "INITIALS", page: 1, x: 500, y: 750 },
        { type: "INITIALS", page: 2, x: 500, y: 750 },
      ],
    },
    {
      email: "hr@company.com",
      name: "HR Manager",
      role: "APPROVER",
      signingOrder: 2,
      fields: [
        { type: "SIGNATURE", page: 3, x: 100, y: 700 },
        { type: "DATE", page: 3, x: 350, y: 700 },
      ],
    },
  ],
  sendImmediately: true,
});

console.log(`Document ID: ${result.documentId}`);
```

### Step 5: Update Recipients

```typescript
async function updateRecipient(
  documentId: string,
  recipientId: string,
  updates: { email?: string; name?: string }
): Promise<void> {
  await documenso.documentsRecipients.updateV0({
    documentId,
    recipientId,
    ...updates,
  });
  console.log(`Updated recipient ${recipientId}`);
}

// Example: Correct email typo
await updateRecipient(documentId, recipientId, {
  email: "correct.email@company.com",
});
```

### Step 6: Remove Recipients

```typescript
async function removeRecipient(
  documentId: string,
  recipientId: string
): Promise<void> {
  await documenso.documentsRecipients.deleteV0({
    documentId,
    recipientId,
  });
  console.log(`Removed recipient ${recipientId}`);
}
```

## Recipient Roles

| Role | Description | Signs Document |
|------|-------------|----------------|
| SIGNER | Primary signer | Yes |
| APPROVER | Must approve before completion | Yes |
| VIEWER | Can view but not sign | No |
| CC | Receives copy when complete | No |

## Field Positioning Tips

- PDF coordinates start from bottom-left (0, 0)
- Standard letter size: 612 x 792 points
- Standard A4 size: 595 x 842 points
- Leave 50+ points margin from edges
- Signature fields: typically 200x60 points
- Text fields: typically 200x30 points
