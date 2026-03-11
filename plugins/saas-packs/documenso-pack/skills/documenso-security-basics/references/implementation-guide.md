# Documenso Security Basics - Implementation Guide

## Instructions

### Step 1: Secure API Key Management

```typescript
// NEVER do this:
const client = new Documenso({
  apiKey: "dcs_abc123...",  // Hardcoded - BAD!
});

// ALWAYS do this:
const client = new Documenso({
  apiKey: process.env.DOCUMENSO_API_KEY ?? "",
});

// Validate API key is present at startup
function validateEnvironment(): void {
  const required = ["DOCUMENSO_API_KEY"];
  const missing = required.filter((key) => !process.env[key]);

  if (missing.length > 0) {
    throw new Error(
      `Missing required environment variables: ${missing.join(", ")}`
    );
  }

  // Validate API key format
  const apiKey = process.env.DOCUMENSO_API_KEY!;
  if (!apiKey.startsWith("dcs_")) {
    console.warn("Warning: API key format unexpected (should start with dcs_)");
  }
}
```

### Step 2: API Key Rotation

```typescript
// Support multiple API keys for rotation
interface KeyRotationConfig {
  primaryKey: string;
  secondaryKey?: string;  // Fallback during rotation
}

async function getClientWithFallback(
  config: KeyRotationConfig
): Promise<Documenso> {
  // Try primary key first
  try {
    const client = new Documenso({ apiKey: config.primaryKey });
    await client.documents.findV0({ perPage: 1 });
    return client;
  } catch (error: any) {
    if (error.statusCode === 401 && config.secondaryKey) {
      console.warn("Primary key failed, trying secondary...");
      return new Documenso({ apiKey: config.secondaryKey });
    }
    throw error;
  }
}

// Rotation procedure:
// 1. Generate new key in Documenso dashboard
// 2. Set as DOCUMENSO_API_KEY_SECONDARY
// 3. Test secondary key works
// 4. Swap: SECONDARY -> PRIMARY
// 5. Revoke old primary key
// 6. Remove secondary env var
```

### Step 3: Webhook Security

```typescript
import express from "express";

const app = express();

// Parse raw body for signature verification
app.use("/webhooks/documenso", express.raw({ type: "application/json" }));

app.post("/webhooks/documenso", (req, res) => {
  // Verify webhook secret
  const receivedSecret = req.headers["x-documenso-secret"];
  const expectedSecret = process.env.DOCUMENSO_WEBHOOK_SECRET;

  if (!expectedSecret) {
    console.error("DOCUMENSO_WEBHOOK_SECRET not configured");
    return res.status(500).json({ error: "Webhook not configured" });
  }

  // Timing-safe comparison to prevent timing attacks
  if (!timingSafeEqual(receivedSecret as string, expectedSecret)) {
    console.warn("Invalid webhook secret received");
    return res.status(401).json({ error: "Invalid signature" });
  }

  // Parse and process
  try {
    const payload = JSON.parse(req.body.toString());
    handleWebhookEvent(payload);
    res.status(200).json({ received: true });
  } catch (error) {
    console.error("Webhook processing error:", error);
    res.status(400).json({ error: "Invalid payload" });
  }
});

function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;

  const bufA = Buffer.from(a);
  const bufB = Buffer.from(b);
  return require("crypto").timingSafeEqual(bufA, bufB);
}
```

### Step 4: Document Access Control

```typescript
// Track document ownership for access control
interface DocumentAccess {
  documentId: string;
  ownerId: string;
  authorizedEmails: string[];
}

class DocumentAccessControl {
  private accessMap = new Map<string, DocumentAccess>();

  async createDocument(
    userId: string,
    title: string,
    authorizedEmails: string[]
  ): Promise<string> {
    const doc = await client.documents.createV0({ title });
    const documentId = doc.documentId!;

    this.accessMap.set(documentId, {
      documentId,
      ownerId: userId,
      authorizedEmails,
    });

    return documentId;
  }

  canAccess(userId: string, documentId: string): boolean {
    const access = this.accessMap.get(documentId);
    if (!access) return false;
    return access.ownerId === userId;
  }

  canSign(email: string, documentId: string): boolean {
    const access = this.accessMap.get(documentId);
    if (!access) return false;
    return access.authorizedEmails.includes(email.toLowerCase());
  }
}
```

### Step 5: Signing URL Security

```typescript
// Signing URLs should be treated as sensitive
// They grant access to sign documents

// DON'T expose signing URLs in logs
function logDocument(doc: any): void {
  const safeDoc = { ...doc };
  if (safeDoc.recipients) {
    safeDoc.recipients = safeDoc.recipients.map((r: any) => ({
      ...r,
      signingUrl: "[REDACTED]",
      signingToken: "[REDACTED]",
    }));
  }
  console.log(JSON.stringify(safeDoc, null, 2));
}

// DON'T store signing URLs in insecure locations
// They should be sent directly to recipients via secure channel

// DO set appropriate expiry on embedded signing sessions
async function getSecureSigningSession(
  documentId: string,
  recipientEmail: string
): Promise<{ signingUrl: string; expiresAt: Date }> {
  const doc = await client.documents.getV0({ documentId });
  const recipient = doc.recipients?.find((r) => r.email === recipientEmail);

  if (!recipient?.signingUrl) {
    throw new Error("Signing URL not available");
  }

  return {
    signingUrl: recipient.signingUrl,
    expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000), // 24 hours
  };
}
```

### Step 6: Input Validation

```typescript
import { z } from "zod";

// Validate recipient input
const RecipientInputSchema = z.object({
  email: z
    .string()
    .email("Invalid email format")
    .transform((e) => e.toLowerCase().trim()),
  name: z
    .string()
    .min(1, "Name is required")
    .max(100, "Name too long")
    .transform((n) => n.trim()),
  role: z.enum(["SIGNER", "APPROVER", "VIEWER", "CC"]),
});

// Validate document title
const DocumentInputSchema = z.object({
  title: z
    .string()
    .min(1, "Title is required")
    .max(255, "Title too long")
    .refine(
      (t) => !/<script/i.test(t),
      "Title contains invalid characters"
    ),
});

// Validate file upload
async function validatePdfUpload(
  file: Buffer,
  maxSizeMb = 10
): Promise<boolean> {
  // Check file size
  const maxBytes = maxSizeMb * 1024 * 1024;
  if (file.length > maxBytes) {
    throw new Error(`File exceeds ${maxSizeMb}MB limit`);
  }

  // Verify PDF magic bytes
  const pdfMagic = Buffer.from([0x25, 0x50, 0x44, 0x46]); // %PDF
  if (!file.slice(0, 4).equals(pdfMagic)) {
    throw new Error("File is not a valid PDF");
  }

  return true;
}

// Use in handler
async function createDocumentHandler(input: unknown) {
  const validated = DocumentInputSchema.parse(input);
  return client.documents.createV0(validated);
}
```

### Step 7: Audit Logging

```typescript
interface AuditEntry {
  timestamp: Date;
  userId: string;
  action: string;
  resourceType: "document" | "template" | "recipient";
  resourceId: string;
  ipAddress?: string;
  userAgent?: string;
  success: boolean;
  error?: string;
}

class AuditLogger {
  private entries: AuditEntry[] = [];

  log(entry: Omit<AuditEntry, "timestamp">): void {
    const fullEntry: AuditEntry = {
      ...entry,
      timestamp: new Date(),
    };

    this.entries.push(fullEntry);

    // Log to console (in production, send to logging service)
    console.log(
      `[AUDIT] ${entry.action} ${entry.resourceType}:${entry.resourceId} ` +
      `by ${entry.userId} - ${entry.success ? "SUCCESS" : "FAILED"}`
    );

    // Alert on suspicious activity
    if (!entry.success && entry.action === "delete") {
      console.warn(`[SECURITY] Failed delete attempt by ${entry.userId}`);
    }
  }

  getRecentEntries(limit = 100): AuditEntry[] {
    return this.entries.slice(-limit);
  }
}

const auditLogger = new AuditLogger();

// Wrap operations with audit logging
async function auditedDeleteDocument(
  userId: string,
  documentId: string
): Promise<boolean> {
  try {
    await client.documents.deleteV0({ documentId });
    auditLogger.log({
      userId,
      action: "delete",
      resourceType: "document",
      resourceId: documentId,
      success: true,
    });
    return true;
  } catch (error: any) {
    auditLogger.log({
      userId,
      action: "delete",
      resourceType: "document",
      resourceId: documentId,
      success: false,
      error: error.message,
    });
    throw error;
  }
}
```

## Security Checklist

- [ ] API keys stored in environment variables only
- [ ] API keys never logged or exposed in responses
- [ ] Webhook endpoints validate X-Documenso-Secret
- [ ] Webhook secret stored securely
- [ ] Signing URLs treated as sensitive data
- [ ] Input validation on all user-provided data
- [ ] File uploads validated (type and size)
- [ ] Audit logging for sensitive operations
- [ ] Access control checks before operations
- [ ] Rate limiting to prevent abuse
