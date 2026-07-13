# Documenso Upgrade & Migration - Implementation Guide

## API Version Differences

### v1 vs v2 Comparison

| Feature | API v1 | API v2 |
|---------|--------|--------|
| Status | Deprecated | Current |
| SDK Support | Limited | Full TypeScript/Python/Go |
| Documents | `/api/v1/documents` | `/api/v2/documents` |
| Templates | `/api/v1/templates` | `/api/v2/templates` |
| Envelopes | N/A | `/api/v2/envelopes` (new) |
| ID Format | Numeric | Prefixed (doc_, tmpl_, etc.) |
| Batch Operations | No | Yes |
| File Streaming | No | Yes |

## Migration Steps

### Step 1: Update SDK

```bash
# Remove old SDK (if any custom v1 implementation)
npm uninstall your-documenso-v1-wrapper

# Install v2 SDK
npm install @documenso/sdk-typescript

# For Python
pip install --upgrade documenso_sdk
```

### Step 2: Update Import Statements

```typescript
// Before (v1 - hypothetical)
import { DocumensoClient } from "documenso-v1";

// After (v2)
import { Documenso } from "@documenso/sdk-typescript";
```

### Step 3: Update Client Initialization

```typescript
// Before (v1)
const client = new DocumensoClient({
  apiKey: process.env.DOCUMENSO_API_KEY,
  baseUrl: "https://app.documenso.com/api/v1",
});

// After (v2)
const client = new Documenso({
  apiKey: process.env.DOCUMENSO_API_KEY ?? "",
  serverURL: "https://app.documenso.com/api/v2/",
});
```

### Step 4: Update Document Operations

```typescript
// Before (v1)
const document = await client.documents.create({
  title: "My Document",
  file: fileBuffer,
});
const docId = document.id;  // Numeric: 12345

// After (v2)
// Note: createV0 is used during beta, will become create
const document = await client.documents.createV0({
  title: "My Document",
  file: pdfBlob,
});
const docId = document.documentId;  // Prefixed: doc_abc123
```

### Step 5: Update Recipient Operations

```typescript
// Before (v1)
await client.documents.addRecipient(docId, {
  email: "signer@example.com",
  name: "John Doe",
  role: "signer",
});

// After (v2)
await client.documentsRecipients.createV0({
  documentId: docId,
  email: "signer@example.com",
  name: "John Doe",
  role: "SIGNER",  // Note: uppercase enum
});
```

### Step 6: Update Field Operations

```typescript
// Before (v1)
await client.documents.addField(docId, recipientId, {
  type: "signature",
  page: 1,
  x: 100,
  y: 600,
  width: 200,
  height: 60,
});

// After (v2)
await client.documentsFields.createV0({
  documentId: docId,
  recipientId: recipientId,
  type: "SIGNATURE",  // Note: uppercase enum
  page: 1,
  positionX: 100,     // Note: renamed from x/y
  positionY: 600,
  width: 200,
  height: 60,
});
```

### Step 7: Update Template Usage

```typescript
// Before (v1)
const doc = await client.templates.createDocument(templateId, {
  recipients: [{ email: "signer@example.com", name: "John" }],
});

// After (v2)
const envelope = await client.envelopes.useV0({
  templateId: templateId,
  recipients: [
    {
      email: "signer@example.com",
      name: "John",
      signerIndex: 0,
    },
  ],
});
```

### Step 8: Update Webhook Handlers

```typescript
// Before (v1)
interface V1WebhookPayload {
  type: string;
  document: {
    id: number;
    title: string;
    status: string;
  };
}

// After (v2)
interface V2WebhookPayload {
  event: string;  // Note: renamed from type
  payload: {
    id: string;   // Note: string prefixed ID
    title: string;
    status: string;
    recipients: Array<{
      email: string;
      signingStatus: string;
    }>;
  };
  createdAt: string;
  webhookEndpoint: string;
}

// Update handler
app.post("/webhooks/documenso", (req, res) => {
  const { event, payload } = req.body as V2WebhookPayload;

  switch (event) {
    case "document.completed":  // v2 event name
      handleDocumentCompleted(payload);
      break;
    case "document.signed":
      handleDocumentSigned(payload);
      break;
  }

  res.json({ received: true });
});
```

## Gradual Migration Strategy

### Step 1: Feature Flag Setup

```typescript
import { getDocumenso } from "./documenso-v2";
import { getLegacyClient } from "./documenso-v1";

async function getClient() {
  const useV2 = await featureFlags.isEnabled("documenso_v2");

  if (useV2) {
    return { client: getDocumenso(), version: "v2" };
  } else {
    return { client: getLegacyClient(), version: "v1" };
  }
}
```

### Step 2: Adapter Pattern

```typescript
// Create unified interface
interface DocumentService {
  createDocument(title: string, file: Blob): Promise<{ id: string }>;
  addRecipient(docId: string, email: string, name: string): Promise<void>;
  sendDocument(docId: string): Promise<void>;
}

// v1 adapter
class V1DocumentService implements DocumentService {
  async createDocument(title: string, file: Blob) {
    const doc = await v1Client.documents.create({ title, file });
    return { id: String(doc.id) };  // Convert numeric to string
  }
  // ... other methods
}

// v2 adapter
class V2DocumentService implements DocumentService {
  async createDocument(title: string, file: Blob) {
    const doc = await v2Client.documents.createV0({ title, file });
    return { id: doc.documentId! };
  }
  // ... other methods
}

// Factory
function getDocumentService(): DocumentService {
  return featureFlags.isEnabled("documenso_v2")
    ? new V2DocumentService()
    : new V1DocumentService();
}
```

### Step 3: Migration Rollout

```
Week 1: Deploy v2 code with feature flag OFF
Week 2: Enable v2 for internal users (5%)
Week 3: Enable v2 for beta users (20%)
Week 4: Enable v2 for all users (100%)
Week 5: Remove v1 code
```

## ID Migration

If you store document IDs in your database:

```typescript
// Migration script
async function migrateDocumentIds() {
  // v2 IDs have prefix, v1 IDs are numeric
  const documents = await db.documents.findAll({
    where: { documensoId: { notLike: 'doc_%' } }
  });

  for (const doc of documents) {
    // Fetch document from v2 API to get new ID
    // Note: You may need Documenso support for ID mapping
    console.log(`Migrate: ${doc.documensoId} -> doc_xxx`);
  }
}
```

## Testing Migration

```typescript
// Run both versions and compare
async function testMigration(testData: TestDocument) {
  const v1Result = await v1Service.createDocument(testData);
  const v2Result = await v2Service.createDocument(testData);

  // Compare results
  assert(v2Result.status === v1Result.status);
  assert(v2Result.recipients.length === v1Result.recipients.length);

  console.log("Migration test passed");
}
```

## Rollback Plan

```bash
# If v2 fails, rollback feature flag
featureFlags.disable("documenso_v2")

# Or deploy previous version
kubectl rollout undo deployment/signing-service
```
