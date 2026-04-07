---
name: glean-reference-architecture
description: |
  Enterprise architecture: Source Systems -> Connectors (Cloud Run/Lambda, event-driven or scheduled) -> Glean Indexing API -> Glean Search Index -> Client API (Search + Chat) -> Your Apps (Slack bot, portal, internal tools).
  Trigger: "glean reference architecture", "reference-architecture".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, enterprise-search, glean]
compatible-with: claude-code
---

# Glean Reference Architecture

## Overview

Enterprise search integration architecture for connecting internal knowledge systems to Glean's indexing and search platform. Designed for organizations needing unified search across Confluence, Google Drive, Notion, Slack, Jira, and custom internal tools. Key design drivers: connector reliability for continuous indexing, permission synchronization to enforce source-system ACLs, incremental vs bulk indexing tradeoffs, and low-latency search aggregation across heterogeneous document types.

## Architecture Diagram
```
Source Systems ──→ Connector Framework ──→ Queue (SQS) ──→ Glean Indexing API
(Confluence, Drive,    (Cloud Run)              ↓            /indexing/documents
 Notion, Slack, Jira)       ↓              Permission Sync  /indexing/permissions
                      Schedule (cron) ──→  Bulk Reindexer   /indexing/datasources
                            ↓
                      Glean Search Index ──→ Client API ──→ Your Apps
                                              /search       (Slack bot, portal)
                                              /chat         (internal tools)
```

## Service Layer
```typescript
class ConnectorService {
  constructor(private glean: GleanIndexingClient, private cache: CacheLayer) {}

  async indexDocument(doc: SourceDocument): Promise<void> {
    const gleanDoc = this.transformToGleanFormat(doc);
    await this.glean.indexDocument(doc.datasource, gleanDoc);
    await this.syncPermissions(doc.id, doc.acl);
  }

  async bulkReindex(datasource: string, since?: string): Promise<IndexReport> {
    const docs = await this.fetchAllDocuments(datasource, since);
    const batches = this.chunk(docs, 100);  // Glean recommends batches of 100
    let indexed = 0;
    for (const batch of batches) {
      await this.glean.bulkIndex(datasource, batch);
      indexed += batch.length;
    }
    return { datasource, totalIndexed: indexed, timestamp: new Date().toISOString() };
  }
}
```

## Caching Strategy
```typescript
const CACHE_CONFIG = {
  searchResults:  { ttl: 30,   prefix: 'search' },   // 30s — freshness critical for search
  permissions:    { ttl: 300,  prefix: 'perm' },      // 5 min — ACL changes are infrequent
  datasources:    { ttl: 3600, prefix: 'ds' },        // 1 hr — datasource config rarely changes
  connectorState: { ttl: 60,   prefix: 'conn' },      // 1 min — sync cursor freshness
  documentMeta:   { ttl: 120,  prefix: 'docmeta' },   // 2 min — title/author for search previews
};
// Webhook-driven invalidation: source system change events flush document cache immediately
```

## Event Pipeline
```typescript
class IndexingPipeline {
  private queue = new Bull('glean-indexing', { redis: process.env.REDIS_URL });

  async onSourceChange(event: SourceChangeEvent): Promise<void> {
    await this.queue.add(event.type, event, { attempts: 5, backoff: { type: 'exponential', delay: 3000 } });
  }

  async processDocumentChange(event: DocumentChangeEvent): Promise<void> {
    if (event.action === 'deleted') await this.glean.deleteDocument(event.datasource, event.docId);
    else await this.connector.indexDocument(await this.fetchDoc(event.datasource, event.docId));
  }

  async processPermissionChange(event: PermissionChangeEvent): Promise<void> {
    await this.glean.syncPermissions(event.datasource, event.docId, event.newAcl);
  }
}
```

## Data Model
```typescript
interface SourceDocument  { id: string; datasource: string; title: string; body: string; url: string; author: string; updatedAt: string; acl: Permission[]; }
interface Permission      { type: 'user' | 'group' | 'domain'; value: string; access: 'read' | 'write'; }
interface ConnectorState  { datasource: string; lastSyncCursor: string; lastFullReindex: string; documentCount: number; status: 'healthy' | 'degraded' | 'failed'; }
interface IndexReport     { datasource: string; totalIndexed: number; failures: string[]; timestamp: string; }
```

## Scaling Considerations
- Deploy one connector instance per datasource to isolate failures and rate limits
- Schedule bulk reindexing during off-peak hours — Glean indexing API has per-datasource throughput limits
- Use incremental sync (change cursors) for high-frequency sources (Slack, Jira) to minimize API calls
- Permission sync is the bottleneck — batch ACL updates and run as a separate queue consumer
- Monitor connector health per datasource; alert on sync lag > 15 minutes for critical sources

## Error Handling
| Component | Failure Mode | Recovery |
|-----------|-------------|----------|
| Connector sync | Source API rate limit | Per-datasource backoff, degrade to hourly bulk sync |
| Document indexing | Glean 429 throughput limit | Queue retry with jitter, batch size reduction |
| Permission sync | ACL mismatch between source and Glean | Reconciliation job flags discrepancies for admin review |
| Bulk reindex | Timeout on large datasource | Checkpoint cursor, resume from last successful batch |
| Search aggregation | Stale index for one datasource | Degrade gracefully — return results from healthy sources, flag staleness |

## Resources
- [Glean Developer Portal](https://developers.glean.com/)
- [Indexing API](https://developers.glean.com/api-info/indexing/getting-started/overview)
- [Search API](https://developers.glean.com/api/client-api/search/overview)

## Next Steps
See `glean-deploy-integration`.
