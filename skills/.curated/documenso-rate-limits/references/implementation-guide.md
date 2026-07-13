# Documenso Rate Limits - Implementation Guide

## Documenso Fair Use Policy

Documenso implements fair use rate limiting. While specific limits are not publicly documented, follow these guidelines:

| Recommendation | Limit | Notes |
|----------------|-------|-------|
| Requests per second | 5-10 | Stay well under burst |
| Requests per minute | 100-200 | Sustained rate |
| Bulk operations | Use batching | Batch create recipients/fields |
| File uploads | 1 at a time | Sequential uploads |
| Polling | 5-10 second intervals | Don't poll aggressively |

## Instructions

### Step 1: Implement Exponential Backoff with Jitter

```typescript
interface BackoffConfig {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
  jitterMs: number;
}

const DEFAULT_BACKOFF: BackoffConfig = {
  maxRetries: 5,
  baseDelayMs: 1000,
  maxDelayMs: 32000,
  jitterMs: 500,
};

async function withExponentialBackoff<T>(
  operation: () => Promise<T>,
  config: Partial<BackoffConfig> = {}
): Promise<T> {
  const { maxRetries, baseDelayMs, maxDelayMs, jitterMs } = {
    ...DEFAULT_BACKOFF,
    ...config,
  };

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error: any) {
      if (attempt === maxRetries) throw error;

      const status = error.statusCode ?? error.status;

      // Only retry on rate limit (429) or server errors (5xx)
      if (status !== 429 && (status < 500 || status >= 600)) {
        throw error;
      }

      // Check for Retry-After header
      const retryAfter = error.headers?.["retry-after"];
      let delay: number;

      if (retryAfter) {
        delay = parseInt(retryAfter) * 1000;
      } else {
        // Exponential backoff with jitter
        const exponentialDelay = baseDelayMs * Math.pow(2, attempt);
        const jitter = Math.random() * jitterMs;
        delay = Math.min(exponentialDelay + jitter, maxDelayMs);
      }

      console.log(
        `Rate limited (attempt ${attempt + 1}/${maxRetries}). ` +
        `Waiting ${delay.toFixed(0)}ms...`
      );
      await new Promise((r) => setTimeout(r, delay));
    }
  }
  throw new Error("Unreachable");
}
```

### Step 2: Request Queue for Controlled Throughput

```typescript
import PQueue from "p-queue";

// Configure queue for Documenso's fair use limits
const documensoQueue = new PQueue({
  concurrency: 3,          // Max 3 concurrent requests
  interval: 1000,          // Per second
  intervalCap: 5,          // Max 5 requests per second
});

// Wrapper for queued requests
async function queuedDocumensoRequest<T>(
  operation: () => Promise<T>
): Promise<T> {
  return documensoQueue.add(() => withExponentialBackoff(operation));
}

// Usage example
const results = await Promise.all(
  documents.map((doc) =>
    queuedDocumensoRequest(() =>
      client.documents.createV0({ title: doc.title })
    )
  )
);
```

### Step 3: Batch Operations

```typescript
// Batch multiple recipients into single requests where possible
async function addRecipientsInBatch(
  documentId: string,
  recipients: Array<{ email: string; name: string; role: string }>
): Promise<string[]> {
  // Use createManyV0 for batch creation
  const result = await queuedDocumensoRequest(() =>
    client.documentsRecipients.createManyV0({
      documentId,
      recipients: recipients.map((r) => ({
        email: r.email,
        name: r.name,
        role: r.role as any,
      })),
    })
  );

  return result.recipientIds ?? [];
}

// Batch fields similarly
async function addFieldsInBatch(
  documentId: string,
  fields: Array<{
    recipientId: string;
    type: string;
    page: number;
    x: number;
    y: number;
  }>
): Promise<void> {
  await queuedDocumensoRequest(() =>
    client.documentsFields.createManyV0({
      documentId,
      fields: fields.map((f) => ({
        recipientId: f.recipientId,
        type: f.type as any,
        page: f.page,
        positionX: f.x,
        positionY: f.y,
        width: 200,
        height: 60,
      })),
    })
  );
}
```

### Step 4: Rate Limit Monitor

```typescript
class RateLimitMonitor {
  private requestCount = 0;
  private windowStart = Date.now();
  private readonly windowMs = 60000; // 1 minute window
  private readonly maxRequests = 100; // Target max per minute

  async canMakeRequest(): Promise<boolean> {
    const now = Date.now();

    // Reset window if expired
    if (now - this.windowStart > this.windowMs) {
      this.requestCount = 0;
      this.windowStart = now;
    }

    // Check if under limit
    if (this.requestCount >= this.maxRequests) {
      const waitTime = this.windowMs - (now - this.windowStart);
      console.log(`Rate limit reached. Wait ${waitTime}ms`);
      return false;
    }

    this.requestCount++;
    return true;
  }

  getStats(): { count: number; remaining: number; resetIn: number } {
    const now = Date.now();
    return {
      count: this.requestCount,
      remaining: Math.max(0, this.maxRequests - this.requestCount),
      resetIn: Math.max(0, this.windowMs - (now - this.windowStart)),
    };
  }
}

const rateLimitMonitor = new RateLimitMonitor();

// Use with requests
async function monitoredRequest<T>(operation: () => Promise<T>): Promise<T> {
  while (!(await rateLimitMonitor.canMakeRequest())) {
    await new Promise((r) => setTimeout(r, 1000));
  }
  return operation();
}
```

### Step 5: Idempotent Requests

```typescript
import crypto from "crypto";

// Generate deterministic idempotency key from request params
function generateIdempotencyKey(
  operation: string,
  params: Record<string, any>
): string {
  const data = JSON.stringify({ operation, params });
  return crypto.createHash("sha256").update(data).digest("hex");
}

// Track processed requests to prevent duplicates
const processedRequests = new Map<string, any>();

async function idempotentRequest<T>(
  key: string,
  operation: () => Promise<T>
): Promise<T> {
  // Check cache first
  if (processedRequests.has(key)) {
    console.log(`Using cached result for ${key.substring(0, 8)}...`);
    return processedRequests.get(key);
  }

  // Execute and cache
  const result = await operation();
  processedRequests.set(key, result);

  // Clean old entries (keep last 1000)
  if (processedRequests.size > 1000) {
    const firstKey = processedRequests.keys().next().value;
    processedRequests.delete(firstKey);
  }

  return result;
}

// Usage
async function createDocumentIdempotent(title: string) {
  const key = generateIdempotencyKey("createDocument", { title });
  return idempotentRequest(key, () =>
    client.documents.createV0({ title })
  );
}
```

### Step 6: Bulk Document Processing with Rate Control

```typescript
interface BulkProcessConfig {
  documents: Array<{ title: string; pdfPath: string }>;
  batchSize: number;
  delayBetweenBatches: number;
}

async function bulkCreateDocuments(
  config: BulkProcessConfig
): Promise<Map<string, string>> {
  const results = new Map<string, string>();
  const batches: Array<typeof config.documents> = [];

  // Split into batches
  for (let i = 0; i < config.documents.length; i += config.batchSize) {
    batches.push(config.documents.slice(i, i + config.batchSize));
  }

  console.log(`Processing ${config.documents.length} documents in ${batches.length} batches`);

  for (let i = 0; i < batches.length; i++) {
    const batch = batches[i];
    console.log(`\nBatch ${i + 1}/${batches.length}`);

    // Process batch concurrently (respecting queue limits)
    const batchResults = await Promise.all(
      batch.map(async (doc) => {
        try {
          const result = await queuedDocumensoRequest(async () => {
            const pdfBlob = await openAsBlob(doc.pdfPath);
            return client.documents.createV0({
              title: doc.title,
              file: pdfBlob,
            });
          });
          return { title: doc.title, id: result.documentId!, error: null };
        } catch (error: any) {
          return { title: doc.title, id: null, error: error.message };
        }
      })
    );

    // Record results
    for (const result of batchResults) {
      if (result.id) {
        results.set(result.title, result.id);
        console.log(`  Created: ${result.title}`);
      } else {
        console.error(`  Failed: ${result.title} - ${result.error}`);
      }
    }

    // Delay between batches (except for last)
    if (i < batches.length - 1) {
      console.log(`Waiting ${config.delayBetweenBatches}ms before next batch...`);
      await new Promise((r) => setTimeout(r, config.delayBetweenBatches));
    }
  }

  return results;
}

// Example usage
const results = await bulkCreateDocuments({
  documents: [...],  // Your documents
  batchSize: 10,
  delayBetweenBatches: 5000,  // 5 seconds between batches
});
```
