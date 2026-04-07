---
name: glean-migration-deep-dive
description: |
  Migrate from Elasticsearch/Algolia: 1) Export all documents from source, 2) Transform to Glean document schema (id, title, url, body, permissions), 3) Create datasource with adddatasource, 4) Bulk index with bulkindexdocuments, 5) Validate search quality with test queries, 6) Switch search UI to use Glean Client API.
  Trigger: "glean migration deep dive", "migration-deep-dive".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, enterprise-search, glean]
compatible-with: claude-code
---

# Glean Migration Deep Dive

## Overview

Comprehensive guide for migrating enterprise search from Elasticsearch or Algolia to
Glean. Covers connector migration (replacing custom crawlers with Glean's push indexing
API), permission model changes (mapping ACLs to Glean's datasource-level permissions),
and full index rebuilds using `bulkindexdocuments`. Typical timeline is 2-4 weeks for
a mid-size deployment with 100K-1M documents across multiple datasources.

## Migration Assessment

```typescript
// Scan current integration for deprecated patterns and index health
const assessment = {
  source: process.env.SEARCH_PROVIDER ?? 'elasticsearch',
  indices: await sourceClient.cat.indices({ format: 'json' }),
  totalDocs: 0, connectors: [] as string[], permissionModel: '',
};
for (const idx of assessment.indices) {
  assessment.totalDocs += parseInt(idx['docs.count'] ?? '0', 10);
  assessment.connectors.push(idx.index);
}
assessment.permissionModel = assessment.source === 'elasticsearch' ? 'index-level' : 'api-key';
console.log(`Source: ${assessment.source}`);
console.log(`Indices: ${assessment.connectors.length} | Total docs: ${assessment.totalDocs}`);
console.log(`Permission model: ${assessment.permissionModel} → Glean datasource ACLs`);
```

## Step-by-Step Migration

### Phase 1: Prepare

Export all documents from the current search provider and map them to Glean's document
schema. Each document needs `id`, `title`, `url`, `body`, and `permissions`.

```typescript
interface GleanDocument {
  id: string;
  datasource: string;
  title: string;
  url: string;
  body: { mimeType: 'text/plain' | 'text/html'; content: string };
  permissions: { allowedUsers?: string[]; allowedGroups?: string[] };
  updatedAt: string;
}

async function exportAndTransform(sourceIndex: string): Promise<GleanDocument[]> {
  const docs: GleanDocument[] = [];
  let scrollId: string | undefined;
  do {
    const batch = scrollId
      ? await sourceClient.scroll({ scroll: '2m', scroll_id: scrollId })
      : await sourceClient.search({ index: sourceIndex, scroll: '2m', size: 500 });
    scrollId = batch._scroll_id;
    for (const hit of batch.hits.hits) {
      docs.push({
        id: hit._id, datasource: 'custom_' + sourceIndex,
        title: hit._source.title, url: hit._source.url,
        body: { mimeType: 'text/plain', content: hit._source.body },
        permissions: { allowedGroups: hit._source.acl_groups ?? ['everyone'] },
        updatedAt: hit._source.updated_at ?? new Date().toISOString(),
      });
    }
  } while (scrollId && docs.length < 1_000_000);
  return docs;
}
```

### Phase 2: Migrate

Create the Glean datasource and bulk-index all transformed documents.

```typescript
// Create datasource
await gleanClient.post('/api/index/v1/adddatasource', {
  name: 'custom_knowledge_base',
  displayName: 'Knowledge Base',
  homeUrl: 'https://kb.example.com',
  objectDefinitions: [{ name: 'Article', propertyDefinitions: [] }],
});

// Bulk index in batches of 200
const BATCH_SIZE = 200;
for (let i = 0; i < docs.length; i += BATCH_SIZE) {
  const batch = docs.slice(i, i + BATCH_SIZE);
  await gleanClient.post('/api/index/v1/bulkindexdocuments', {
    datasource: 'custom_knowledge_base',
    documents: batch.map(d => ({
      id: d.id, title: d.title, url: d.url, body: d.body,
      permissions: d.permissions, updatedAt: d.updatedAt,
    })),
  });
  console.log(`Indexed ${Math.min(i + BATCH_SIZE, docs.length)}/${docs.length}`);
}
```

### Phase 3: Validate

Run test queries against both old and new systems and compare result quality.

```typescript
const testQueries = ['onboarding process', 'security policy', 'API authentication'];
for (const query of testQueries) {
  const result = await gleanClient.post('/api/client/v1/search', {
    query, pageSize: 5, requestOptions: { datasourceFilter: 'custom_knowledge_base' },
  });
  console.log(`"${query}" → ${result.results.length} results, top: ${result.results[0]?.title}`);
}
```

## Rollback Plan

```bash
# Delete the Glean datasource (removes all indexed documents)
curl -X DELETE "https://your-instance.glean.com/api/index/v1/deletedatasource" \
  -H "Authorization: Bearer $GLEAN_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "custom_knowledge_base"}'

# Re-enable old search provider
export SEARCH_PROVIDER=elasticsearch
echo "Rollback complete — old search provider re-enabled"
```

## Migration Checklist

- [ ] Inventory all source indices and document counts
- [ ] Map permission model (index-level ACLs to Glean datasource permissions)
- [ ] Export and transform documents to Glean schema
- [ ] Create datasource via `adddatasource` API
- [ ] Bulk index all documents in batches of 200
- [ ] Run validation queries and compare relevance
- [ ] Update search UI to use Glean Client API
- [ ] Decommission old search crawlers and indices
- [ ] Monitor search quality metrics for 7 days post-migration
- [ ] Remove old provider SDK dependencies from codebase

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Invalid Glean API token | Regenerate token in admin console |
| `409 Datasource exists` | Name collision | Delete or rename existing datasource |
| `413 Payload Too Large` | Batch exceeds 10 MB | Reduce batch size from 200 |
| `422 Invalid document` | Missing required field | Validate `id`, `title`, `url` before indexing |
| Stale search results | Index not refreshed | Wait 5 min or trigger manual refresh |

## Resources

- [Glean Developer Portal](https://developers.glean.com/)
- [Indexing API](https://developers.glean.com/api-info/indexing/getting-started/overview)
- [Search API](https://developers.glean.com/api/client-api/search/overview)

## Next Steps

After migration, configure Glean's built-in connectors for Google Drive, Confluence,
and Slack to replace custom crawlers. See `glean-core-workflow-a` for search integration.
