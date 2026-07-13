# Documenso Data Handling - Implementation Guide

## Document Lifecycle

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   DRAFT     │────▶│   PENDING   │────▶│  COMPLETED  │
│             │     │  (Signing)  │     │             │
└─────────────┘     └──────┬──────┘     └──────┬──────┘
                           │                    │
                           ▼                    │
                    ┌─────────────┐             │
                    │  REJECTED/  │             │
                    │  CANCELLED  │             │
                    └─────────────┘             │
                                               ▼
                                        ┌─────────────┐
                                        │  ARCHIVED   │
                                        │  (Storage)  │
                                        └─────────────┘
```

## Downloading Signed Documents

### Step 1: Download Completed Document

```typescript
import { getDocumensoClient } from "./documenso/client";
import fs from "fs/promises";

async function downloadSignedDocument(
  documentId: string,
  outputPath: string
): Promise<void> {
  const client = getDocumensoClient();

  // Verify document is completed
  const doc = await client.documents.getV0({ documentId });

  if (doc.status !== "COMPLETED") {
    throw new Error(`Document not completed. Status: ${doc.status}`);
  }

  // Download the signed PDF
  const pdfData = await client.documents.downloadV0({ documentId });

  // Save to file
  await fs.writeFile(outputPath, Buffer.from(pdfData as ArrayBuffer));

  console.log(`Signed document saved to: ${outputPath}`);
}
```

### Step 2: Secure Storage

```typescript
import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";
import crypto from "crypto";

const s3 = new S3Client({ region: process.env.AWS_REGION });

interface StorageResult {
  key: string;
  bucket: string;
  checksum: string;
}

async function storeSignedDocument(
  documentId: string,
  pdfData: Buffer,
  metadata: Record<string, string>
): Promise<StorageResult> {
  // Generate unique key with date partitioning
  const date = new Date();
  const key = `signed-documents/${date.getFullYear()}/${
    String(date.getMonth() + 1).padStart(2, "0")
  }/${documentId}.pdf`;

  // Calculate checksum for integrity verification
  const checksum = crypto.createHash("sha256").update(pdfData).digest("hex");

  // Upload with server-side encryption
  await s3.send(
    new PutObjectCommand({
      Bucket: process.env.DOCUMENTS_BUCKET!,
      Key: key,
      Body: pdfData,
      ContentType: "application/pdf",
      ServerSideEncryption: "aws:kms",
      SSEKMSKeyId: process.env.KMS_KEY_ID,
      Metadata: {
        ...metadata,
        checksum,
        uploadedAt: new Date().toISOString(),
      },
    })
  );

  return {
    key,
    bucket: process.env.DOCUMENTS_BUCKET!,
    checksum,
  };
}
```

## PII Handling

### Step 3: Recipient Data Management

```typescript
interface RecipientPII {
  email: string;
  name: string;
  documentIds: string[];
}

// Store PII reference mapping (not the actual PII)
interface PIIReference {
  recipientHash: string;  // Hashed identifier
  documentIds: string[];
  createdAt: Date;
  lastAccessedAt: Date;
}

function hashRecipientEmail(email: string): string {
  const salt = process.env.PII_SALT!;
  return crypto
    .createHmac("sha256", salt)
    .update(email.toLowerCase().trim())
    .digest("hex");
}

// Track document associations without storing raw PII
async function trackRecipientDocument(
  email: string,
  documentId: string
): Promise<void> {
  const recipientHash = hashRecipientEmail(email);

  await db.piiReferences.upsert({
    where: { recipientHash },
    create: {
      recipientHash,
      documentIds: [documentId],
      createdAt: new Date(),
      lastAccessedAt: new Date(),
    },
    update: {
      documentIds: { push: documentId },
      lastAccessedAt: new Date(),
    },
  });
}
```

### Step 4: Data Minimization

```typescript
// Only request necessary recipient information
async function addRecipientMinimal(
  documentId: string,
  email: string,
  name: string
): Promise<string> {
  const client = getDocumensoClient();

  // Don't store additional PII we don't need
  const recipient = await client.documentsRecipients.createV0({
    documentId,
    email,
    name,
    role: "SIGNER",
    // Don't add phone, address, or other unnecessary PII
  });

  return recipient.recipientId!;
}

// Sanitize document data before logging
function sanitizeForLogging(doc: any): any {
  return {
    id: doc.id,
    title: doc.title,
    status: doc.status,
    recipientCount: doc.recipients?.length ?? 0,
    // Explicitly exclude: recipients[].email, recipients[].name
  };
}
```

## Data Retention

### Step 5: Retention Policy Implementation

```typescript
interface RetentionPolicy {
  completedDocuments: number;  // Days to retain completed docs
  draftDocuments: number;      // Days to retain drafts
  cancelledDocuments: number;  // Days to retain cancelled
}

const RETENTION_POLICY: RetentionPolicy = {
  completedDocuments: 2555,  // 7 years for legal compliance
  draftDocuments: 30,        // 30 days for abandoned drafts
  cancelledDocuments: 90,    // 90 days for cancelled
};

async function enforceRetentionPolicy(): Promise<RetentionReport> {
  const report = {
    draftsDeleted: 0,
    cancelledDeleted: 0,
    archivedCompleted: 0,
  };

  const client = getDocumensoClient();
  const now = new Date();

  // Find old drafts
  const drafts = await findDocumentsByStatus("DRAFT");
  for (const draft of drafts) {
    const age = daysSince(new Date(draft.createdAt!));
    if (age > RETENTION_POLICY.draftDocuments) {
      await client.documents.deleteV0({ documentId: draft.id! });
      report.draftsDeleted++;
    }
  }

  // Find old cancelled documents
  const cancelled = await findDocumentsByStatus("CANCELLED");
  for (const doc of cancelled) {
    const age = daysSince(new Date(doc.updatedAt!));
    if (age > RETENTION_POLICY.cancelledDocuments) {
      await archiveAndDelete(doc.id!);
      report.cancelledDeleted++;
    }
  }

  return report;
}

function daysSince(date: Date): number {
  const now = new Date();
  return Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
}
```

### Step 6: Archive Before Delete

```typescript
interface ArchiveRecord {
  documentId: string;
  title: string;
  status: string;
  completedAt?: string;
  recipientEmails: string[];  // Hashed
  storageKey: string;
  archivedAt: string;
}

async function archiveAndDelete(documentId: string): Promise<void> {
  const client = getDocumensoClient();

  // Get document details
  const doc = await client.documents.getV0({ documentId });

  // Download PDF if completed
  let storageKey = "";
  if (doc.status === "COMPLETED") {
    const pdfData = await client.documents.downloadV0({ documentId });
    const result = await storeSignedDocument(
      documentId,
      Buffer.from(pdfData as ArrayBuffer),
      { title: doc.title!, status: doc.status }
    );
    storageKey = result.key;
  }

  // Create archive record
  const archiveRecord: ArchiveRecord = {
    documentId,
    title: doc.title!,
    status: doc.status!,
    completedAt: doc.completedAt,
    recipientEmails: doc.recipients?.map((r) =>
      hashRecipientEmail(r.email!)
    ) ?? [],
    storageKey,
    archivedAt: new Date().toISOString(),
  };

  // Save to archive database
  await db.documentArchive.create({ data: archiveRecord });

  // Delete from Documenso
  await client.documents.deleteV0({ documentId });

  console.log(`Archived and deleted document: ${documentId}`);
}
```

## GDPR Compliance

### Step 7: Data Subject Access Request (DSAR)

```typescript
interface DSARResponse {
  recipientHash: string;
  documents: Array<{
    documentId: string;
    title: string;
    status: string;
    signedAt?: string;
  }>;
  exportedAt: string;
}

async function handleDSAR(email: string): Promise<DSARResponse> {
  const recipientHash = hashRecipientEmail(email);
  const client = getDocumensoClient();

  // Find all documents associated with this email
  const documents: DSARResponse["documents"] = [];

  // Search through documents (pagination required for large datasets)
  let page = 1;
  let hasMore = true;

  while (hasMore) {
    const result = await client.documents.findV0({ page, perPage: 100 });

    for (const doc of result.documents ?? []) {
      const hasRecipient = doc.recipients?.some(
        (r) => r.email?.toLowerCase() === email.toLowerCase()
      );

      if (hasRecipient) {
        const recipient = doc.recipients?.find(
          (r) => r.email?.toLowerCase() === email.toLowerCase()
        );

        documents.push({
          documentId: doc.id!,
          title: doc.title!,
          status: doc.status!,
          signedAt: recipient?.signedAt,
        });
      }
    }

    hasMore = (result.documents?.length ?? 0) === 100;
    page++;
  }

  return {
    recipientHash,
    documents,
    exportedAt: new Date().toISOString(),
  };
}
```

### Step 8: Right to Erasure

```typescript
async function handleErasureRequest(email: string): Promise<ErasureReport> {
  const report = {
    documentsAffected: 0,
    cannotDelete: [] as string[],
    deleted: [] as string[],
  };

  const dsar = await handleDSAR(email);

  for (const doc of dsar.documents) {
    // Cannot delete completed documents due to legal requirements
    if (doc.status === "COMPLETED") {
      report.cannotDelete.push(doc.documentId);
      console.log(
        `Cannot delete ${doc.documentId}: Legal retention required`
      );
      continue;
    }

    // Can delete drafts and cancelled
    if (doc.status === "DRAFT" || doc.status === "CANCELLED") {
      const client = getDocumensoClient();
      await client.documents.deleteV0({ documentId: doc.documentId });
      report.deleted.push(doc.documentId);
    }

    report.documentsAffected++;
  }

  return report;
}
```

## Encryption at Rest

```typescript
import crypto from "crypto";

const ENCRYPTION_KEY = Buffer.from(process.env.ENCRYPTION_KEY!, "hex");

function encryptPII(plaintext: string): string {
  const iv = crypto.randomBytes(16);
  const cipher = crypto.createCipheriv("aes-256-gcm", ENCRYPTION_KEY, iv);

  let encrypted = cipher.update(plaintext, "utf8", "hex");
  encrypted += cipher.final("hex");

  const authTag = cipher.getAuthTag().toString("hex");

  return `${iv.toString("hex")}:${authTag}:${encrypted}`;
}

function decryptPII(ciphertext: string): string {
  const [ivHex, authTagHex, encrypted] = ciphertext.split(":");

  const iv = Buffer.from(ivHex, "hex");
  const authTag = Buffer.from(authTagHex, "hex");

  const decipher = crypto.createDecipheriv("aes-256-gcm", ENCRYPTION_KEY, iv);
  decipher.setAuthTag(authTag);

  let decrypted = decipher.update(encrypted, "hex", "utf8");
  decrypted += decipher.final("utf8");

  return decrypted;
}
```
