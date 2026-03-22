---
name: glean-local-dev-loop
description: |
  Configure Glean local development with mock search responses, test datasources, and connector development workflow.
  Trigger: "glean dev setup", "glean local development", "glean connector development".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, enterprise-search, glean]
compatible-with: claude-code
---

# Glean Local Dev Loop

## Overview

Set up local development for Glean custom connectors and search integrations with mock data and test datasources.

## Instructions

### Project Structure

```
glean-connector/
├── src/
│   ├── glean/client.ts         # Typed Glean API client
│   ├── connectors/wiki.ts      # Wiki connector logic
│   └── index.ts
├── tests/
│   ├── mock-data.ts            # Mock Glean responses
│   └── connector.test.ts
├── .env.local
└── package.json
```

### Mock Glean Responses

```typescript
export const mockSearchResponse = {
  results: [
    { title: 'Test Doc', url: 'https://test.com/doc', score: 0.95, datasource: 'test_ds',
      snippets: [{ snippet: 'This is a <b>test</b> document' }] },
  ],
  totalCount: 1,
};

export const mockIndexResponse = { status: 'OK', documentsIndexed: 5 };
```

### Test Connector

```typescript
import { describe, it, expect, vi } from 'vitest';

describe('Wiki Connector', () => {
  it('transforms wiki pages to Glean documents', () => {
    const wikiPage = { id: '1', title: 'Setup', content: 'How to...', author: 'jane@co.com' };
    const gleanDoc = transformToGleanDoc(wikiPage);
    expect(gleanDoc).toHaveProperty('id', '1');
    expect(gleanDoc).toHaveProperty('title', 'Setup');
    expect(gleanDoc.body.textContent).toBe('How to...');
  });
});
```

## Resources

- [Glean Indexing API](https://developers.glean.com/api-info/indexing/getting-started/overview)
- [Vitest](https://vitest.dev/)
