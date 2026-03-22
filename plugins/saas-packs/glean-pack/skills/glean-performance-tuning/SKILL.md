---
name: glean-performance-tuning
description: |
  Optimize Glean search relevance and indexing throughput with batch sizing,
  datasource configuration, and content quality improvements.
  Trigger: "glean performance", "glean search quality", "glean indexing speed".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, enterprise-search, glean]
compatible-with: claude-code
---

# Glean Performance Tuning

## Overview

Optimize Glean for better search results and faster indexing: tune content quality, batch sizes, and datasource configuration.

## Search Relevance

| Factor | Impact | Action |
|--------|--------|--------|
| Document titles | High | Use descriptive, unique titles |
| Body content | High | Include full text, not just metadata |
| Author info | Medium | Set email for people ranking |
| Updated date | Medium | Keep timestamps current |
| URL structure | Low | Use readable, hierarchical URLs |

## Indexing Throughput

```typescript
// Optimal batch configuration
const BATCH_SIZE = 100;        // Max per API call
const CONCURRENT_BATCHES = 3;  // Parallel uploads
const DELAY_BETWEEN_MS = 500;  // Avoid rate limits

async function indexWithThroughput(docs: GleanDocument[]) {
  const batches = chunk(docs, BATCH_SIZE);
  const queue = new PQueue({ concurrency: CONCURRENT_BATCHES, interval: DELAY_BETWEEN_MS });

  await Promise.all(batches.map((batch, i) =>
    queue.add(() => glean.indexDocuments('my_ds', batch))
  ));
}
```

## Incremental vs Bulk Strategy

| Strategy | When | API Endpoint |
|----------|------|-------------|
| Incremental (`indexdocuments`) | Real-time updates, < 100 docs | `/index/v1/indexdocuments` |
| Bulk (`bulkindexdocuments`) | Daily full refresh, > 1000 docs | `/index/v1/bulkindexdocuments` |

## Resources

- [Glean Developer Portal](https://developers.glean.com/)
