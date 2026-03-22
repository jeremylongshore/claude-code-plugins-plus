---
name: glean-cost-tuning
description: |
  Optimize Glean costs by managing indexed content volume, datasource efficiency,
  and connector resource usage.
  Trigger: "glean costs", "glean optimization", "reduce glean indexing".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, enterprise-search, glean]
compatible-with: claude-code
---

# Glean Cost Tuning

## Overview

Glean pricing scales with indexed content volume and user count. Reduce costs by indexing only relevant content, pruning stale data, and using incremental indexing.

## Cost Reduction Strategies

| Strategy | Savings | Implementation |
|----------|---------|---------------|
| Filter irrelevant content | 20-40% | Skip drafts, templates, archived pages |
| Prune stale documents | 10-20% | Delete docs not updated in 12+ months |
| Use incremental indexing | Compute savings | Index only changed docs, not full corpus |
| Consolidate datasources | Admin savings | Fewer connectors to maintain |
| Set content size limits | Storage savings | Truncate body to ~50KB per doc |

### Content Filtering Example

```typescript
function shouldIndex(doc: SourceDocument): boolean {
  if (doc.status === 'draft' || doc.status === 'archived') return false;
  if (doc.updatedAt < oneYearAgo) return false;
  if (doc.title.startsWith('[Template]')) return false;
  if (doc.content.length < 50) return false;  // Skip near-empty pages
  return true;
}

const filtered = allDocs.filter(shouldIndex);
// Typically reduces corpus by 30-50%
```

## Resources

- [Glean Developer Portal](https://developers.glean.com/)
