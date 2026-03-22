---
name: glean-webhooks-events
description: |
  Implement event-driven Glean indexing triggered by source system webhooks from
  GitHub, Confluence, Notion, and other content platforms.
  Trigger: "glean webhooks", "glean event indexing", "incremental glean index".
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, enterprise-search, glean]
compatible-with: claude-code
---

# Glean Webhooks & Events

## Overview

Glean does not send webhooks. Instead, build event-driven connectors that receive webhooks from source systems (GitHub, Confluence, Notion) and push incremental updates to the Glean Indexing API.

## Instructions

### GitHub Webhook -> Glean Indexing

```typescript
// Receive GitHub wiki/page webhooks, index into Glean
app.post('/webhooks/github', async (req, res) => {
  const event = req.body;

  if (event.action === 'created' || event.action === 'edited') {
    await glean.indexDocuments('github_wiki', [{
      id: `wiki-${event.page.sha}`,
      title: event.page.title,
      url: event.page.html_url,
      body: { mimeType: 'text/html', textContent: event.page.body },
      author: { email: event.sender.email },
      updatedAt: new Date().toISOString(),
      permissions: { allowAnonymousAccess: true },
    }]);
  }

  res.sendStatus(200);
});
```

### Confluence Webhook -> Glean Indexing

```typescript
app.post('/webhooks/confluence', async (req, res) => {
  const { event, page } = req.body;

  if (event === 'page_updated' || event === 'page_created') {
    const content = await fetchConfluencePage(page.id);
    await glean.indexDocuments('confluence_custom', [{
      id: `conf-${page.id}`,
      title: content.title,
      url: `${CONFLUENCE_URL}/wiki/spaces/${content.space.key}/pages/${page.id}`,
      body: { mimeType: 'text/html', textContent: content.body.storage.value },
      updatedAt: content.version.when,
    }]);
  }

  if (event === 'page_removed') {
    await glean.deleteDocument('confluence_custom', `conf-${page.id}`);
  }

  res.sendStatus(200);
});
```

## Resources

- [Glean Index Documents](https://developers.glean.com/api/indexing-api/index-documents)
