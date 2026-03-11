# Documenso Common Errors - Implementation Guide

## Error Reference Table

| Status | Error | Common Cause | Quick Fix |
|--------|-------|--------------|-----------|
| 400 | Bad Request | Invalid parameters | Check request body format |
| 401 | Unauthorized | Invalid/missing API key | Verify DOCUMENSO_API_KEY |
| 403 | Forbidden | Insufficient permissions | Use team API key |
| 404 | Not Found | Resource doesn't exist | Verify ID is correct |
| 409 | Conflict | Duplicate resource | Handle existing resource |
| 422 | Unprocessable | Validation failed | Check field values |
| 429 | Rate Limited | Too many requests | Implement backoff |
| 500 | Server Error | Documenso issue | Retry with backoff |

## Detailed Error Scenarios

### Error: 401 Unauthorized

**Symptoms:**
```
SDKError: Unauthorized
Status: 401
```

**Causes and Solutions:**

```typescript
// Cause 1: Missing API key
// Solution: Set environment variable
export DOCUMENSO_API_KEY="your-api-key"

// Cause 2: Invalid API key format
// Wrong: API key with extra whitespace
const apiKey = " dcs_abc123 ";  // Bad
const apiKey = "dcs_abc123";     // Good

// Cause 3: Expired or revoked key
// Solution: Generate new key in Documenso dashboard

// Cause 4: Wrong environment
// Solution: Use correct key for environment
const client = new Documenso({
  apiKey: process.env.DOCUMENSO_API_KEY,
  serverURL: process.env.DOCUMENSO_BASE_URL,  // Match key to URL
});
```

### Error: 403 Forbidden

**Symptoms:**
```
SDKError: Forbidden
Status: 403
```

**Causes and Solutions:**

```typescript
// Cause 1: Personal API key used for team resources
// Solution: Use team API key for team documents
// Get team API key from: Team Settings > API Tokens

// Cause 2: Accessing another user's resource
// Solution: Verify you own the document
const doc = await client.documents.getV0({ documentId });
// Check doc.userId matches your user

// Cause 3: Document in terminal state
// Solution: Cannot modify completed/cancelled documents
if (doc.status === "COMPLETED" || doc.status === "CANCELLED") {
  console.log("Cannot modify document in terminal state");
  // Create new document instead
}
```

### Error: 404 Not Found

**Symptoms:**
```
SDKError: Not Found
Status: 404
```

**Causes and Solutions:**

```typescript
// Cause 1: Wrong document ID
// Solution: Verify ID format and existence
async function safeGetDocument(documentId: string) {
  try {
    return await client.documents.getV0({ documentId });
  } catch (error: any) {
    if (error.statusCode === 404) {
      console.log(`Document ${documentId} not found`);
      return null;
    }
    throw error;
  }
}

// Cause 2: Document deleted
// Solution: Check if document was deleted

// Cause 3: Using v1 ID with v2 API (or vice versa)
// Solution: IDs have different formats between versions
// v1: numeric IDs like "12345"
// v2: prefixed IDs like "doc_abc123"
```

### Error: 409 Conflict

**Symptoms:**
```
SDKError: Conflict
Status: 409
```

**Causes and Solutions:**

```typescript
// Cause 1: Duplicate recipient email
// Solution: Update existing or skip
async function addOrUpdateRecipient(
  documentId: string,
  email: string,
  name: string
) {
  try {
    return await client.documentsRecipients.createV0({
      documentId,
      email,
      name,
      role: "SIGNER",
    });
  } catch (error: any) {
    if (error.statusCode === 409) {
      // Recipient exists - find and update
      const doc = await client.documents.getV0({ documentId });
      const existing = doc.recipients?.find(r => r.email === email);
      if (existing) {
        return await client.documentsRecipients.updateV0({
          documentId,
          recipientId: existing.id!,
          name,  // Update name
        });
      }
    }
    throw error;
  }
}

// Cause 2: Template with same name
// Solution: Use unique name or update existing
```

### Error: 422 Unprocessable Entity

**Symptoms:**
```
SDKError: Unprocessable Entity
Status: 422
```

**Causes and Solutions:**

```typescript
// Cause 1: Invalid field position (off-page)
// Solution: Check page dimensions
const fieldConfig = {
  page: 1,
  positionX: 100,  // Must be 0 < x < pageWidth
  positionY: 600,  // Must be 0 < y < pageHeight
  width: 200,      // x + width must be < pageWidth
  height: 60,      // y + height must be < pageHeight
};

// Letter size: 612 x 792 points
// A4 size: 595 x 842 points

// Cause 2: Invalid email format
// Solution: Validate before sending
function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

// Cause 3: Missing required fields
// Solution: Check all required parameters
const recipient = await client.documentsRecipients.createV0({
  documentId,      // Required
  email,           // Required
  name,            // Required
  role: "SIGNER",  // Required
});

// Cause 4: Invalid file type
// Solution: Only PDF files are supported
```

### Error: 429 Rate Limited

**Symptoms:**
```
SDKError: Too Many Requests
Status: 429
```

**Solution:**

```typescript
// Implement exponential backoff
async function withBackoff<T>(
  operation: () => Promise<T>,
  maxRetries = 5
): Promise<T> {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error: any) {
      if (error.statusCode !== 429 || attempt === maxRetries - 1) {
        throw error;
      }

      // Check Retry-After header if available
      const retryAfter = error.headers?.["retry-after"];
      const delay = retryAfter
        ? parseInt(retryAfter) * 1000
        : Math.pow(2, attempt) * 1000;

      console.log(`Rate limited. Waiting ${delay}ms...`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error("Max retries exceeded");
}

// Use queue for bulk operations
import PQueue from "p-queue";

const queue = new PQueue({
  concurrency: 2,
  interval: 1000,
  intervalCap: 5,
});

async function queuedCreate(data: any) {
  return queue.add(() => client.documents.createV0(data));
}
```

### Error: 500 Internal Server Error

**Symptoms:**
```
SDKError: Internal Server Error
Status: 500
```

**Solution:**

```typescript
// Retry with exponential backoff (server errors are usually transient)
async function retryServerErrors<T>(
  operation: () => Promise<T>
): Promise<T> {
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      return await operation();
    } catch (error: any) {
      if (error.statusCode < 500 || attempt === 2) {
        throw error;
      }

      const delay = Math.pow(2, attempt) * 1000;
      console.log(`Server error. Retrying in ${delay}ms...`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error("Max retries exceeded");
}

// If persistent, check Documenso status
// https://status.documenso.com
```

## File Upload Errors

```typescript
// Error: File too large
// Solution: Check file size before upload
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

async function uploadWithSizeCheck(pdfPath: string) {
  const stats = await fs.promises.stat(pdfPath);
  if (stats.size > MAX_FILE_SIZE) {
    throw new Error(`File exceeds ${MAX_FILE_SIZE / 1024 / 1024}MB limit`);
  }
  return openAsBlob(pdfPath);
}

// Error: Invalid file type
// Solution: Verify PDF format
import { fileTypeFromFile } from "file-type";

async function verifyPdf(filePath: string) {
  const type = await fileTypeFromFile(filePath);
  if (type?.mime !== "application/pdf") {
    throw new Error("Only PDF files are supported");
  }
}
```

## Webhook Errors

```typescript
// Error: Webhook not receiving events
// Checklist:
// 1. Webhook URL is HTTPS
// 2. Endpoint returns 200 within 30 seconds
// 3. Correct events are subscribed
// 4. Secret is correctly configured

// Error: Signature verification failing
function verifyWebhookSignature(
  payload: string,
  receivedSecret: string
): boolean {
  const expectedSecret = process.env.DOCUMENSO_WEBHOOK_SECRET;
  // Documenso sends secret in X-Documenso-Secret header
  return receivedSecret === expectedSecret;
}
```

## Debugging Checklist

1. **Check API Key:**
   ```bash
   echo $DOCUMENSO_API_KEY | head -c 10
   # Should show: dcs_xxx...
   ```

2. **Verify Endpoint:**
   ```bash
   curl -H "Authorization: Bearer $DOCUMENSO_API_KEY" \
     https://app.documenso.com/api/v2/documents
   ```

3. **Enable Debug Logging:**
   ```typescript
   const client = new Documenso({
     apiKey: process.env.DOCUMENSO_API_KEY,
     debugLogger: console,
   });
   ```

4. **Check Document Status:**
   ```typescript
   const doc = await client.documents.getV0({ documentId });
   console.log(`Status: ${doc.status}`);
   console.log(`Recipients: ${doc.recipients?.length}`);
   ```
