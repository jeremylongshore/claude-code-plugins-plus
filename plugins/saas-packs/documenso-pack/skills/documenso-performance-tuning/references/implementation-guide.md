# Documenso Performance Tuning - Implementation Guide

## Caching Strategies

### Step 1: Document Metadata Cache

```typescript
import Redis from "ioredis";

const redis = new Redis(process.env.REDIS_URL);
const CACHE_TTL = 300; // 5 minutes

interface CachedDocument {
  id: string;
  title: string;
  status: string;
  recipientCount: number;
  cachedAt: string;
}

async function getDocumentCached(
  documentId: string
): Promise<CachedDocument | null> {
  // Try cache first
  const cacheKey = `doc:${documentId}`;
  const cached = await redis.get(cacheKey);

  if (cached) {
    return JSON.parse(cached);
  }

  // Fetch from API
  const client = getDocumensoClient();
  const doc = await client.documents.getV0({ documentId });

  // Cache the result
  const cacheData: CachedDocument = {
    id: doc.id!,
    title: doc.title!,
    status: doc.status!,
    recipientCount: doc.recipients?.length ?? 0,
    cachedAt: new Date().toISOString(),
  };

  await redis.setex(cacheKey, CACHE_TTL, JSON.stringify(cacheData));

  return cacheData;
}

// Invalidate cache on webhook events
async function invalidateDocumentCache(documentId: string): Promise<void> {
  await redis.del(`doc:${documentId}`);
}
```

### Step 2: Template Cache

```typescript
// Templates change rarely - longer TTL
const TEMPLATE_CACHE_TTL = 3600; // 1 hour

async function getTemplateCached(templateId: string) {
  const cacheKey = `tmpl:${templateId}`;
  const cached = await redis.get(cacheKey);

  if (cached) {
    return JSON.parse(cached);
  }

  const client = getDocumensoClient();
  const template = await client.templates.getV0({ templateId });

  await redis.setex(cacheKey, TEMPLATE_CACHE_TTL, JSON.stringify(template));

  return template;
}

// Bulk cache templates on startup
async function warmTemplateCache(templateIds: string[]): Promise<void> {
  const client = getDocumensoClient();

  console.log(`Warming cache for ${templateIds.length} templates...`);

  for (const templateId of templateIds) {
    try {
      await getTemplateCached(templateId);
    } catch (error) {
      console.warn(`Failed to cache template ${templateId}`);
    }
  }
}
```

## Batch Operations

### Step 3: Batch Document Creation

```typescript
import PQueue from "p-queue";

interface DocumentInput {
  title: string;
  templateId: string;
  recipients: Array<{ email: string; name: string }>;
}

async function batchCreateDocuments(
  inputs: DocumentInput[]
): Promise<Map<string, string>> {
  const results = new Map<string, string>(); // title -> documentId

  // Queue with rate limiting
  const queue = new PQueue({
    concurrency: 3,
    interval: 1000,
    intervalCap: 5,
  });

  // Process in batches
  const promises = inputs.map((input) =>
    queue.add(async () => {
      const envelope = await client.envelopes.useV0({
        templateId: input.templateId,
        title: input.title,
        recipients: input.recipients.map((r, i) => ({
          email: r.email,
          name: r.name,
          signerIndex: i,
        })),
      });

      results.set(input.title, envelope.envelopeId!);
      return envelope;
    })
  );

  await Promise.all(promises);

  return results;
}
```

### Step 4: Batch Recipient Updates

```typescript
// Use bulk API when available
async function addRecipientsBatch(
  documentId: string,
  recipients: Array<{ email: string; name: string; role: string }>
): Promise<string[]> {
  // Use createManyV0 for batch creation
  const result = await client.documentsRecipients.createManyV0({
    documentId,
    recipients: recipients.map((r) => ({
      email: r.email,
      name: r.name,
      role: r.role as any,
    })),
  });

  return result.recipientIds ?? [];
}
```

## Connection Pooling

### Step 5: HTTP Client Optimization

```typescript
import { Documenso } from "@documenso/sdk-typescript";

// Reuse client instance (connection pooling is handled internally)
let clientInstance: Documenso | null = null;

export function getDocumensoClient(): Documenso {
  if (!clientInstance) {
    clientInstance = new Documenso({
      apiKey: process.env.DOCUMENSO_API_KEY ?? "",
      // SDK handles connection pooling internally
      timeoutMs: 30000,
      retryConfig: {
        strategy: "backoff",
        backoff: {
          initialInterval: 500,
          maxInterval: 30000,
          exponent: 1.5,
          maxElapsedTime: 120000,
        },
        retryConnectionErrors: true,
      },
    });
  }
  return clientInstance;
}
```

## Response Size Optimization

### Step 6: Pagination for Large Lists

```typescript
// Efficient pagination
async function* iterateDocuments(
  pageSize = 100
): AsyncGenerator<DocumentInfo[]> {
  let page = 1;
  let hasMore = true;

  while (hasMore) {
    const result = await client.documents.findV0({
      page,
      perPage: pageSize,
    });

    const docs = result.documents ?? [];

    if (docs.length > 0) {
      yield docs;
    }

    hasMore = docs.length === pageSize;
    page++;
  }
}

// Usage
async function processAllDocuments() {
  for await (const batch of iterateDocuments(100)) {
    console.log(`Processing ${batch.length} documents...`);
    await processBatch(batch);
  }
}
```

### Step 7: Field Selection (When Available)

```typescript
// Request only needed fields to reduce payload size
// Note: Check SDK for field selection support
async function getDocumentStatus(documentId: string) {
  const doc = await client.documents.getV0({ documentId });

  // Extract only what's needed
  return {
    id: doc.id,
    status: doc.status,
    completedAt: doc.completedAt,
  };
}
```

## Async Processing

### Step 8: Background Job Queue

```typescript
import Bull from "bull";

const documentQueue = new Bull("document-processing", {
  redis: process.env.REDIS_URL,
});

// Add job instead of processing synchronously
async function createDocumentAsync(input: DocumentInput): Promise<string> {
  const job = await documentQueue.add("create-document", input, {
    attempts: 3,
    backoff: { type: "exponential", delay: 1000 },
  });

  return job.id.toString();
}

// Process jobs in background
documentQueue.process("create-document", async (job) => {
  const { title, templateId, recipients } = job.data;

  const envelope = await client.envelopes.useV0({
    templateId,
    title,
    recipients: recipients.map((r: any, i: number) => ({
      email: r.email,
      name: r.name,
      signerIndex: i,
    })),
  });

  return { documentId: envelope.envelopeId };
});
```

## Performance Monitoring

### Step 9: Request Timing

```typescript
class PerformanceMonitor {
  private timings: number[] = [];

  async track<T>(operation: () => Promise<T>): Promise<T> {
    const start = Date.now();
    try {
      return await operation();
    } finally {
      const duration = Date.now() - start;
      this.timings.push(duration);

      // Keep last 1000 timings
      if (this.timings.length > 1000) {
        this.timings = this.timings.slice(-1000);
      }
    }
  }

  getMetrics() {
    const sorted = [...this.timings].sort((a, b) => a - b);
    return {
      count: this.timings.length,
      p50: sorted[Math.floor(sorted.length * 0.5)] ?? 0,
      p95: sorted[Math.floor(sorted.length * 0.95)] ?? 0,
      p99: sorted[Math.floor(sorted.length * 0.99)] ?? 0,
      avg:
        this.timings.reduce((a, b) => a + b, 0) / this.timings.length || 0,
    };
  }
}

const perfMonitor = new PerformanceMonitor();

// Wrap API calls
async function getDocumentTimed(documentId: string) {
  return perfMonitor.track(() =>
    client.documents.getV0({ documentId })
  );
}
```

## Performance Checklist

- [ ] Caching implemented for frequently accessed data
- [ ] Batch operations used where available
- [ ] Connection pooling via singleton client
- [ ] Pagination for large result sets
- [ ] Background processing for non-blocking operations
- [ ] Request timing and monitoring in place
- [ ] Rate limiting prevents API throttling
- [ ] Cache invalidation on webhook events
