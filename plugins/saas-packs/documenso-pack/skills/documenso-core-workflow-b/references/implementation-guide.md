# Documenso Core Workflow B: Templates & Direct Signing - Implementation Guide

## Instructions

### Step 1: Create a Template

```typescript
import { Documenso } from "@documenso/sdk-typescript";
import { openAsBlob } from "node:fs";

const documenso = new Documenso({
  apiKey: process.env.DOCUMENSO_API_KEY ?? "",
});

interface CreateTemplateInput {
  title: string;
  pdfPath: string;
  recipientRoles: Array<{
    name: string;  // e.g., "Employee", "Manager"
    role: "SIGNER" | "APPROVER" | "VIEWER" | "CC";
    signingOrder?: number;
  }>;
}

async function createTemplate(
  input: CreateTemplateInput
): Promise<string> {
  const pdfBlob = await openAsBlob(input.pdfPath);

  // Create the template
  const template = await documenso.templates.createV0({
    title: input.title,
    file: pdfBlob,
  });

  const templateId = template.templateId!;
  console.log(`Created template: ${templateId}`);

  // Add recipient placeholders
  for (const role of input.recipientRoles) {
    await documenso.templatesRecipients.createV0({
      templateId,
      name: role.name,
      role: role.role,
      signingOrder: role.signingOrder,
    });
    console.log(`Added role: ${role.name}`);
  }

  return templateId;
}

// Example: Create NDA template
const templateId = await createTemplate({
  title: "Non-Disclosure Agreement",
  pdfPath: "./templates/nda.pdf",
  recipientRoles: [
    { name: "Disclosing Party", role: "SIGNER", signingOrder: 1 },
    { name: "Receiving Party", role: "SIGNER", signingOrder: 2 },
  ],
});
```

### Step 2: Add Template Fields

```typescript
interface TemplateFieldInput {
  recipientIndex: number;  // Index of recipient in the roles array
  type: "SIGNATURE" | "INITIALS" | "NAME" | "EMAIL" | "DATE" | "TEXT";
  page: number;
  x: number;
  y: number;
  width?: number;
  height?: number;
}

async function addTemplateFields(
  templateId: string,
  fields: TemplateFieldInput[]
): Promise<void> {
  // Get template recipients to map indices to IDs
  const template = await documenso.templates.getV0({ templateId });
  const recipientIds = template.recipients?.map(r => r.id!) ?? [];

  for (const field of fields) {
    const recipientId = recipientIds[field.recipientIndex];
    if (!recipientId) {
      console.error(`No recipient at index ${field.recipientIndex}`);
      continue;
    }

    await documenso.templatesFields.createV0({
      templateId,
      recipientId,
      type: field.type,
      page: field.page,
      positionX: field.x,
      positionY: field.y,
      width: field.width ?? 200,
      height: field.height ?? 60,
    });
    console.log(`Added ${field.type} field for recipient ${field.recipientIndex}`);
  }
}

// Example: Add fields to NDA template
await addTemplateFields(templateId, [
  // Disclosing Party fields (index 0)
  { recipientIndex: 0, type: "SIGNATURE", page: 2, x: 100, y: 400 },
  { recipientIndex: 0, type: "NAME", page: 2, x: 100, y: 350 },
  { recipientIndex: 0, type: "DATE", page: 2, x: 350, y: 400 },
  // Receiving Party fields (index 1)
  { recipientIndex: 1, type: "SIGNATURE", page: 2, x: 100, y: 200 },
  { recipientIndex: 1, type: "NAME", page: 2, x: 100, y: 150 },
  { recipientIndex: 1, type: "DATE", page: 2, x: 350, y: 200 },
]);
```

### Step 3: Generate Document from Template

```typescript
interface UseTemplateInput {
  templateId: string;
  title?: string;
  recipients: Array<{
    email: string;
    name: string;
  }>;
  sendImmediately?: boolean;
}

async function createFromTemplate(
  input: UseTemplateInput
): Promise<{ documentId: string }> {
  // Use the template to create a new document
  const result = await documenso.envelopes.useV0({
    templateId: input.templateId,
    title: input.title,
    recipients: input.recipients.map((r, index) => ({
      email: r.email,
      name: r.name,
      signerIndex: index,
    })),
  });

  const documentId = result.envelopeId!;
  console.log(`Created document from template: ${documentId}`);

  // Send if requested
  if (input.sendImmediately) {
    await documenso.envelopes.distributeV0({
      envelopeId: documentId,
    });
    console.log("Document sent to recipients");
  }

  return { documentId };
}

// Example: Create NDA from template
const document = await createFromTemplate({
  templateId,
  title: "NDA - Acme Corp Partnership",
  recipients: [
    { email: "legal@yourcompany.com", name: "Your Company Legal" },
    { email: "partner@acme.com", name: "Acme Corp Representative" },
  ],
  sendImmediately: true,
});
```

### Step 4: Direct Template Links

Direct templates allow signers to access and sign documents without pre-registration.

```typescript
async function createDirectTemplateLink(
  templateId: string
): Promise<{ directLink: string }> {
  // Get template direct link settings
  const template = await documenso.templates.getV0({ templateId });

  // The direct link is available when template is published
  const directLink = template.directLink;

  if (!directLink) {
    console.log("Template direct link not enabled. Enable in dashboard.");
    throw new Error("Direct link not available");
  }

  return { directLink };
}

// Example usage with direct link
// Users can access: https://app.documenso.com/d/{directLinkToken}
```

### Step 5: Embedding Signing Experience

```typescript
// Get signing token for embedding
async function getSigningToken(
  documentId: string,
  recipientEmail: string
): Promise<{ signingToken: string; signingUrl: string }> {
  // Get document with recipients
  const doc = await documenso.documents.getV0({ documentId });

  const recipient = doc.recipients?.find(r => r.email === recipientEmail);
  if (!recipient) {
    throw new Error(`Recipient ${recipientEmail} not found`);
  }

  // The signing token can be used for embedding
  return {
    signingToken: recipient.signingToken!,
    signingUrl: recipient.signingUrl!,
  };
}

// For React embedding, use @documenso/embed-react
// npm install @documenso/embed-react

// React component example:
/*
import { EmbedDirectTemplate } from '@documenso/embed-react';

function SigningComponent({ signingToken }) {
  return (
    <EmbedDirectTemplate
      token={signingToken}
      host="https://app.documenso.com"
      onDocumentReady={() => console.log('Ready')}
      onDocumentCompleted={() => console.log('Completed')}
      onDocumentError={(error) => console.error(error)}
    />
  );
}
*/
```

### Step 6: Pre-fill Template Fields

```typescript
interface PrefillInput {
  templateId: string;
  recipients: Array<{
    email: string;
    name: string;
    prefillFields?: Array<{
      fieldId: string;
      value: string;
    }>;
  }>;
}

async function createWithPrefill(
  input: PrefillInput
): Promise<{ documentId: string }> {
  const result = await documenso.envelopes.useV0({
    templateId: input.templateId,
    recipients: input.recipients.map((r, index) => ({
      email: r.email,
      name: r.name,
      signerIndex: index,
      prefillFields: r.prefillFields,
    })),
  });

  return { documentId: result.envelopeId! };
}

// Example: Pre-fill contract details
await createWithPrefill({
  templateId,
  recipients: [
    {
      email: "client@example.com",
      name: "Client Name",
      prefillFields: [
        { fieldId: "company_name_field", value: "Acme Corporation" },
        { fieldId: "contract_amount_field", value: "$50,000" },
      ],
    },
  ],
});
```

### Step 7: Duplicate and Modify Templates

```typescript
async function duplicateTemplate(
  templateId: string,
  newTitle: string
): Promise<string> {
  const duplicate = await documenso.templates.duplicateV0({
    templateId,
    title: newTitle,
  });

  console.log(`Duplicated template: ${duplicate.templateId}`);
  return duplicate.templateId!;
}

// Example: Create region-specific variants
const usTemplateId = await duplicateTemplate(templateId, "NDA - US Version");
const euTemplateId = await duplicateTemplate(templateId, "NDA - EU Version");
```

## Template Workflow Patterns

### Pattern 1: Sales Contract Flow
```typescript
// 1. Create template once
const salesContractTemplate = await createTemplate({
  title: "Sales Agreement",
  pdfPath: "./templates/sales-agreement.pdf",
  recipientRoles: [
    { name: "Sales Rep", role: "SIGNER", signingOrder: 1 },
    { name: "Customer", role: "SIGNER", signingOrder: 2 },
    { name: "Legal Review", role: "APPROVER", signingOrder: 3 },
  ],
});

// 2. Use for each deal
async function createSalesContract(deal: DealInfo) {
  return createFromTemplate({
    templateId: salesContractTemplate,
    title: `Sales Agreement - ${deal.customerName}`,
    recipients: [
      { email: deal.salesRepEmail, name: deal.salesRepName },
      { email: deal.customerEmail, name: deal.customerName },
      { email: "legal@company.com", name: "Legal Team" },
    ],
    sendImmediately: true,
  });
}
```

### Pattern 2: Self-Service Signing
```typescript
// Customer visits your site, fills form, and signs
async function selfServiceSigning(customerInfo: CustomerInfo) {
  // Create document from template with customer info pre-filled
  const doc = await createWithPrefill({
    templateId: selfServiceTemplateId,
    recipients: [
      {
        email: customerInfo.email,
        name: customerInfo.name,
        prefillFields: [
          { fieldId: "customer_name", value: customerInfo.name },
          { fieldId: "customer_address", value: customerInfo.address },
        ],
      },
    ],
  });

  // Get signing URL for immediate redirect
  const { signingUrl } = await getSigningToken(
    doc.documentId,
    customerInfo.email
  );

  return { signingUrl };
}
```
