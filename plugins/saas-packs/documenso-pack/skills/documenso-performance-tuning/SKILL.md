---
name: documenso-performance-tuning
description: |
  Optimize Documenso integration performance with caching, batching, and efficient patterns.
  Use when improving response times, reducing API calls,
  or optimizing bulk document operations.
  Trigger with phrases like "documenso performance", "optimize documenso",
  "documenso caching", "documenso batch operations".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, documenso, api, performance]

---
# Documenso Performance Tuning

## Overview

Optimize Documenso integrations for speed and efficiency. Key strategies: reduce API round-trips with templates, cache document metadata, batch operations with concurrency control, and use async processing for bulk signing workflows.

## Prerequisites

- Working Documenso integration
- Redis or in-memory cache (recommended)
- Completed `documenso-sdk-patterns` setup

## Instructions

### Step 1: Reduce API Calls with Templates

The biggest performance win: templates reduce a multi-step document creation (create + upload + add recipients + add fields + send = 5+ calls) to just 2 calls (create from template + send).

```typescript
// WITHOUT templates: 5+ API calls per document
async function createDocumentManual(signer: { email: string; name: string }) {
  const doc = await client.documents.createV0({ title: "Contract" });              // 1
  await client.documents.setFileV0(doc.documentId, { file: pdfBlob });             // 2
  const recip = await client.documentsRecipients.createV0(doc.documentId, {        // 3
    email: signer.email, name: signer.name, role: "SIGNER",
  });
  await client.documentsFields.createV0(doc.documentId, {                          // 4
    recipientId: recip.recipientId, type: "SIGNATURE",
    pageNumber: 1, pageX: 10, pageY: 80, pageWidth: 30, pageHeight: 5,
  });
  await client.documents.sendV0(doc.documentId);                                   // 5
}

// WITH templates: 2 API calls per document
async function createDocumentFromTemplate(templateId: number, signer: { email: string; name: string }) {
  const res = await fetch(                                                          // 1
    `${BASE}/templates/${templateId}/create-document`,
    {
      method: "POST",
      headers: { Authorization: `Bearer ${API_KEY}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        title: `Contract — ${signer.name}`,
        recipients: [{ email: signer.email, name: signer.name, role: "SIGNER" }],
      }),
    }
  );
  const doc = await res.json();
  await fetch(`${BASE}/documents/${doc.documentId}/send`, {                         // 2
    method: "POST",
    headers: { Authorization: `Bearer ${API_KEY}` },
  });
}
```

### Step 2: Cache Document Metadata

```typescript
// src/cache/documenso-cache.ts
import NodeCache from "node-cache";

const cache = new NodeCache({ stdTTL: 300, checkperiod: 60 }); // 5 min TTL

export async function getCachedDocument(client: Documenso, documentId: number) {
  const key = `doc:${documentId}`;
  const cached = cache.get(key);
  if (cached) return cached;

  const doc = await client.documents.getV0(documentId);
  // Only cache completed documents (immutable)
  if (doc.status === "COMPLETED") {
    cache.set(key, doc, 3600); // 1 hour for completed
  } else {
    cache.set(key, doc, 30); // 30 seconds for in-progress
  }
  return doc;
}

// Invalidate on webhook events
export function invalidateDocument(documentId: number) {
  cache.del(`doc:${documentId}`);
}
```

### Step 3: Batch Operations with Concurrency Control

```typescript
// src/batch/documenso-batch.ts
import PQueue from "p-queue";

const queue = new PQueue({
  concurrency: 5,       // Max 5 concurrent API calls
  interval: 1000,       // Per second window
  intervalCap: 10,      // Max 10 per second
});

export async function batchCreateDocuments(
  client: Documenso,
  templateId: number,
  signers: Array<{ email: string; name: string; company: string }>
): Promise<Array<{ email: string; documentId?: number; error?: string }>> {
  const results = await Promise.allSettled(
    signers.map((signer) =>
      queue.add(async () => {
        const res = await fetch(
          `https://app.documenso.com/api/v1/templates/${templateId}/create-document`,
          {
            method: "POST",
            headers: {
              Authorization: `Bearer ${process.env.DOCUMENSO_API_KEY}`,
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              title: `Agreement — ${signer.company}`,
              recipients: [{ email: signer.email, name: signer.name, role: "SIGNER" }],
            }),
          }
        );
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const doc = await res.json();

        // Send immediately
        await fetch(
          `https://app.documenso.com/api/v1/documents/${doc.documentId}/send`,
          {
            method: "POST",
            headers: { Authorization: `Bearer ${process.env.DOCUMENSO_API_KEY}` },
          }
        );

        return { email: signer.email, documentId: doc.documentId };
      })
    )
  );

  return results.map((r, i) => {
    if (r.status === "fulfilled") return r.value as any;
    return { email: signers[i].email, error: (r.reason as Error).message };
  });
}
```

### Step 4: Async Processing with Background Jobs

```typescript
// src/jobs/signing-queue.ts
import Bull from "bull";

const signingQueue = new Bull("documenso-signing", process.env.REDIS_URL!);

// Producer: queue signing requests
export async function queueSigningRequest(data: {
  templateId: number;
  signerEmail: string;
  signerName: string;
}) {
  const job = await signingQueue.add(data, {
    attempts: 3,
    backoff: { type: "exponential", delay: 5000 },
  });
  return job.id;
}

// Consumer: process in background
signingQueue.process(5, async (job) => {
  const { templateId, signerEmail, signerName } = job.data;
  // Create and send document...
  return { status: "sent" };
});

signingQueue.on("completed", (job, result) => {
  console.log(`Job ${job.id} completed: ${JSON.stringify(result)}`);
});

signingQueue.on("failed", (job, err) => {
  console.error(`Job ${job.id} failed: ${err.message}`);
});
```

### Step 5: Efficient Pagination

```typescript
// Paginate through all documents without loading everything into memory
async function* iterateDocuments(client: Documenso, perPage = 50) {
  let page = 1;
  while (true) {
    const { documents } = await client.documents.findV0({
      page,
      perPage,
      orderByColumn: "createdAt",
      orderByDirection: "desc",
    });

    for (const doc of documents) {
      yield doc;
    }

    if (documents.length < perPage) break; // Last page
    page++;
  }
}

// Usage: process all documents without memory issues
for await (const doc of iterateDocuments(client)) {
  if (doc.status === "COMPLETED") {
    await archiveDocument(doc.id);
  }
}
```

## Performance Targets

| Operation | Target | If Exceeded |
|-----------|--------|-------------|
| Single document create | < 500ms | Check network latency |
| Template create + send | < 1s | Normal for template workflow |
| Batch of 100 documents | < 30s | Use concurrency 5-10 |
| Document list (page) | < 300ms | Add caching layer |
| Webhook processing | < 100ms | Process async, respond 200 immediately |

## Error Handling

| Performance Issue | Cause | Solution |
|------------------|-------|----------|
| Slow responses | No connection reuse | Use singleton client pattern |
| Rate limit errors | Too many concurrent calls | Use `p-queue` with concurrency cap |
| Memory issues | Loading all documents | Use async generator pagination |
| Queue backlog | Slow processing | Increase worker concurrency |

## Resources

- [p-queue Documentation](https://github.com/sindresorhus/p-queue)
- [Bull Queue](https://github.com/OptimalBits/bull)
- [node-cache](https://github.com/node-cache/node-cache)

## Next Steps

For cost optimization, see `documenso-cost-tuning`.
