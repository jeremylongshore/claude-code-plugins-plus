---
name: glean-core-workflow-a
description: |
  Execute Glean primary workflow: search, chat, and AI-powered answers across enterprise data.
  Use when building search integrations, implementing Glean chat, or creating AI assistants.
  Trigger: "glean search API", "glean chat", "glean AI answers", "enterprise search".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, enterprise-search, glean]
compatible-with: claude-code
---

# Glean Core Workflow A: Search & Chat

## Overview

Build search and chat experiences using the Glean Client API. Covers full-text search with filters, AI-powered chat answers, and autocomplete suggestions.

## Instructions

### Step 1: Search with Filters and Facets

```typescript
const results = await fetch(`${GLEAN}/client/v1/search`, {
  method: 'POST', headers: searchHeaders,
  body: JSON.stringify({
    query: 'kubernetes deployment best practices',
    pageSize: 20,
    requestOptions: {
      datasourceFilter: 'confluence,github',
      facetFilters: [{ fieldName: 'author', values: ['engineering-team'] }],
    },
  }),
}).then(r => r.json());

results.results?.forEach((r: any) => {
  console.log(`[${r.datasource}] ${r.title}`);
  console.log(`  ${r.snippets?.[0]?.snippet ?? ''}`);
});
```

### Step 2: AI Chat (Glean Assistant)

```typescript
const chatResponse = await fetch(`${GLEAN}/client/v1/chat`, {
  method: 'POST', headers: searchHeaders,
  body: JSON.stringify({
    messages: [{ role: 'USER', content: 'What is our deployment process for production?' }],
    applicationId: 'my-app',
  }),
}).then(r => r.json());

console.log('Answer:', chatResponse.messages?.[0]?.content);
console.log('Sources:', chatResponse.citations?.map((c: any) => c.title).join(', '));
```

### Step 3: Autocomplete / Suggestions

```typescript
const suggestions = await fetch(`${GLEAN}/client/v1/autocomplete`, {
  method: 'POST', headers: searchHeaders,
  body: JSON.stringify({ query: 'deploy', datasourceFilter: 'confluence' }),
}).then(r => r.json());

suggestions.results?.forEach((s: any) => console.log(`  ${s.text}`));
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Empty results | Query too specific or datasource not indexed | Broaden query, check datasource status |
| Chat returns no citations | Content not indexed for chat | Verify documents have body text |
| 403 on search | User permissions | Ensure token has search scope |

## Resources

- [Search API](https://developers.glean.com/api/client-api/search/search)
- [Chat API](https://developers.glean.com/api/client-api/search/overview)

## Next Steps

For bulk indexing workflow, see `glean-core-workflow-b`.
