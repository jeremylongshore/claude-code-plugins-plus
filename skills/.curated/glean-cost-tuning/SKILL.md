---
name: glean-cost-tuning
description: 'Optimize Glean costs by managing indexed content volume, datasource
  efficiency,

  and connector resource usage.

  Trigger: "glean costs", "glean optimization", "reduce glean indexing".

  '
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- enterprise-search
- glean
compatibility: Designed for Claude Code
---
# Glean Cost Tuning

## Overview

Glean pricing scales with indexed content volume and per-seat user count, making document indexing volume and search query frequency the primary cost drivers. Enterprise deployments typically connect dozens of datasources, each pushing thousands of documents into the index. Without active content governance, stale drafts, archived pages, and near-empty documents inflate the index by 30-50%, driving up costs with zero search value. Pruning irrelevant content and using incremental indexing are the highest-leverage optimizations.

## Cost Breakdown

| Component | Cost Driver | Optimization |
|-----------|------------|--------------|
| Document indexing | Volume of indexed content across all sources | Filter drafts, templates, and archived content pre-index |
| User seats | Per-seat licensing | Audit active users quarterly; deprovision inactive accounts |
| Search queries | Query volume across the organization | Cache frequent queries; use search analytics to identify redundant patterns |
| Datasource connectors | Number of active connectors to maintain | Consolidate overlapping sources; remove unused connectors |
| Content storage | Size of indexed documents | Truncate body to 50KB; skip attachments over 10MB |

## API Call Reduction

```typescript
class GleanIndexFilter {
  private staleThreshold = 365 * 24 * 60 * 60 * 1000; // 12 months

  shouldIndex(doc: { status: string; updatedAt: number; title: string; content: string }): boolean {
    if (doc.status === 'draft' || doc.status === 'archived') return false;
    if (Date.now() - doc.updatedAt > this.staleThreshold) return false;
    if (doc.title.startsWith('[Template]')) return false;
    if (doc.content.length < 50) return false;
    return true;
  }

  async incrementalIndex(docs: any[], lastSyncTimestamp: number): Promise<any[]> {
    // Only process documents modified since last sync — reduces indexing calls by 80-90%
    const modified = docs.filter(d => d.updatedAt > lastSyncTimestamp);
    const eligible = modified.filter(d => this.shouldIndex(d));
    return eligible.map(d => ({
      ...d,
      content: d.content.slice(0, 50_000) // Truncate to 50KB
    }));
  }
}
```

## Usage Monitoring

```typescript
class GleanCostMonitor {
  private indexedDocs = 0;
  private queriesThisHour = 0;
  private budgetDocs = 100_000;

  recordIndexed(count: number): void {
    this.indexedDocs += count;
    const utilization = (this.indexedDocs / this.budgetDocs) * 100;
    if (utilization > 80) {
      console.warn(`Glean index at ${utilization.toFixed(0)}% capacity: ${this.indexedDocs}/${this.budgetDocs} docs`);
    }
  }

  getUtilization(): string {
    return `${((this.indexedDocs / this.budgetDocs) * 100).toFixed(1)}% index capacity used`;
  }
}
```

## Cost Optimization Checklist

- [ ] Filter drafts, templates, and archived documents before indexing
- [ ] Prune documents not updated in 12+ months
- [ ] Use incremental indexing — only process changed documents
- [ ] Truncate document bodies to 50KB maximum
- [ ] Consolidate overlapping datasource connectors
- [ ] Audit user seats quarterly and deprovision inactive accounts
- [ ] Skip attachments larger than 10MB
- [ ] Monitor index utilization with 80% threshold alerts

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| Index bloat exceeding budget | No content filtering on connectors | Apply shouldIndex filter to all datasource pipelines |
| Stale search results | Deleted docs still in index | Run nightly reconciliation to remove orphaned entries |
| Connector timeouts | Source system rate limiting | Implement backoff and schedule syncs during off-peak |
| Duplicate documents indexed | Same content in multiple datasources | Deduplicate by content hash before indexing |
| Query costs spiking | Bot or automated search traffic | Rate-limit API search consumers; whitelist known clients |

## Resources

- [Glean Developer Portal](https://developers.glean.com/)
- [Glean Pricing](https://www.glean.com/pricing)

## Next Steps

See `glean-performance-tuning`.
