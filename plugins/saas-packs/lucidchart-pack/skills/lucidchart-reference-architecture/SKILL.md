---
name: lucidchart-reference-architecture
description: |
  Reference Architecture for Lucidchart.
  Trigger: "lucidchart reference architecture".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, lucidchart, diagramming]
compatible-with: claude-code
---

# Lucidchart Reference Architecture

## Overview
Design a version-controlled integration layer for the Lucidchart diagramming platform. Document versioning is the primary driver, so every shape mutation is tracked for diff, rollback, and branch operations while an async export pipeline renders diagrams without blocking collaboration.

## Instructions
1. Provision the prerequisites below and register a Lucidchart OAuth2 application.
2. Deploy the document sync service to reconcile local snapshots with Lucidchart state.
3. Start the collaboration event consumer to capture shape deltas in real time.
4. Configure the export worker pool with deduplication via Redis SETNX.
5. Tune the sync interval and version retention policy for your document volume.

## Prerequisites
- Node.js 18+, TypeScript 5, PostgreSQL 15, Redis 7, RabbitMQ or SQS
- Lucidchart OAuth2 credentials with `document:read`, `document:write`, `export` scopes

## Architecture Diagram
```
Client --> API Gateway --> DocumentSyncService --> Lucidchart API
                                  |
                   +--------------+--------------+
                   v              v              v
             Version DB    Collab Event     Export Worker
            (snapshots)     Consumer       (PNG/SVG/PDF)
```

## Service Layer
```typescript
class DocumentSyncService {
  constructor(
    private api: LucidchartApiClient,
    private versions: VersionStore,
    private events: EventPublisher
  ) {}

  async syncDocument(docId: string): Promise<DocumentSnapshot> {
    const remote = await this.api.getDocument(docId);
    const local = await this.versions.getLatest(docId);
    if (!local || remote.revision > local.revision) {
      const snapshot = await this.versions.save(docId, remote);
      await this.events.publish('document.synced', { docId, revision: remote.revision });
      return snapshot;
    }
    return local;
  }

  async exportDiagram(docId: string, format: ExportFormat): Promise<string> {
    await this.events.publish('export.requested', { docId, format });
    return this.api.requestExport(docId, format);
  }
}
```

## Caching Strategy
```typescript
class DocumentCache {
  constructor(private redis: RedisClient) {}

  async getMetadata(docId: string): Promise<DocumentMeta | null> {
    const raw = await this.redis.get(`doc:meta:${docId}`);
    return raw ? JSON.parse(raw) : null;
  }

  async setMetadata(docId: string, meta: DocumentMeta): Promise<void> {
    await this.redis.setEx(`doc:meta:${docId}`, 120, JSON.stringify(meta));
  }

  async deduplicateExport(docId: string, format: string): Promise<boolean> {
    const key = `export:lock:${docId}:${format}`;
    return (await this.redis.setNX(key, '1')) === true;
  }
}
// TTLs: doc metadata 2 min, shape data not cached (version store is truth)
```

## Event Pipeline
```typescript
class CollabEventConsumer {
  constructor(private queue: MessageQueue, private versions: VersionStore) {}

  async start(): Promise<void> {
    await this.queue.subscribe('collab.shape_changed', async (evt: ShapeEvent) => {
      await this.versions.recordDelta(evt.docId, evt.revision, evt.delta);
    });
    await this.queue.subscribe('collab.user_joined', async (evt: PresenceEvent) => {
      await this.versions.recordCollaborator(evt.docId, evt.userId);
    });
  }
}

class ExportWorker {
  async processExport(job: ExportJob): Promise<void> {
    const url = await this.api.pollExportStatus(job.exportId);
    const buffer = await this.api.downloadExport(url);
    await this.storage.upload(`exports/${job.docId}/${job.format}`, buffer);
  }
}
```

## Data Model
```typescript
interface DocumentSnapshot {
  docId: string; revision: number; title: string;
  pages: Page[]; collaborators: string[]; capturedAt: Date;
}
interface Page {
  pageId: string; title: string;
  shapes: Shape[]; connectors: Connector[];
}
interface Shape {
  id: string; type: string; text: string;
  position: { x: number; y: number };
  size: { width: number; height: number };
}
interface ExportJob {
  exportId: string; docId: string;
  format: 'png' | 'svg' | 'pdf'; requestedAt: Date;
}
```

## Output
Running this architecture produces a versioned document store with full revision history, a real-time collaboration delta stream, and on-demand diagram exports to PNG, SVG, or PDF with deduplication.

## Scaling Considerations
- Partition the version store by document ID to isolate write-heavy diagrams
- Export workers are stateless; scale horizontally based on queue depth
- Deduplicate concurrent export requests for the same document/format via Redis SETNX
- Distribute sync jobs across OAuth tokens to respect per-user rate limits

## Error Handling
| Component | Failure Mode | Recovery |
|-----------|-------------|----------|
| Lucidchart API | 429 rate limit | Exponential backoff, pause sync for that token |
| Version Store | Write conflict | Retry with latest revision, merge divergent deltas |
| Export Worker | Render timeout | Re-queue lower priority, notify after 3 failures |
| Collab Consumer | Out-of-order events | Buffer and reorder by revision before applying |
| Redis | Cache eviction | Rebuild metadata from version store on next read |

## Examples
```bash
# Sync a document and capture its current revision
curl http://localhost:3000/api/documents/abc123/sync
# Request a PNG export of a specific diagram
curl -X POST http://localhost:3000/api/documents/abc123/export?format=png
```

## Resources
- [Lucidchart API Reference](https://developer.lucid.co/reference/overview)

## Next Steps
See `lucidchart-deploy-integration`.
