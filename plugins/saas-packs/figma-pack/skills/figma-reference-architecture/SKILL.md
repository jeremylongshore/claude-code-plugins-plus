---
name: figma-reference-architecture
description: |
  Reference architecture for production Figma API integrations.
  Use when designing a new Figma integration, planning project structure,
  or establishing patterns for design-to-code pipelines.
  Trigger with phrases like "figma architecture", "figma project structure",
  "figma integration design", "figma best practices layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, figma]
compatible-with: claude-code
---

# Figma Reference Architecture

## Overview
Production-ready architecture for Figma REST API integrations. Covers the three most common use cases: design token pipelines, asset export systems, and webhook-driven automation.

## Prerequisites
- Understanding of Figma REST API endpoints
- TypeScript project setup
- Decision on deployment platform

## Instructions

### Step 1: Project Structure
```
figma-integration/
├── src/
│   ├── figma/
│   │   ├── client.ts           # Typed REST API wrapper
│   │   ├── types.ts            # Figma API response types
│   │   ├── errors.ts           # FigmaApiError, FigmaRateLimitError
│   │   ├── cache.ts            # LRU cache for API responses
│   │   └── walker.ts           # Node tree traversal utilities
│   ├── services/
│   │   ├── token-extractor.ts  # Design token extraction
│   │   ├── asset-exporter.ts   # Image/icon export pipeline
│   │   ├── comment-syncer.ts   # Comment sync to Slack/Jira
│   │   └── variable-syncer.ts  # Variables API sync (Enterprise)
│   ├── webhooks/
│   │   ├── handler.ts          # Webhook event router
│   │   ├── verify.ts           # Passcode verification
│   │   └── processors/
│   │       ├── file-update.ts  # FILE_UPDATE handler
│   │       ├── comment.ts      # FILE_COMMENT handler
│   │       └── library.ts      # LIBRARY_PUBLISH handler
│   ├── api/
│   │   ├── health.ts           # Health check endpoint
│   │   ├── tokens.ts           # Token API endpoint
│   │   └── assets.ts           # Asset download endpoint
│   └── index.ts
├── scripts/
│   ├── extract-tokens.mjs      # CLI: extract tokens from Figma
│   ├── export-icons.mjs        # CLI: export icons from Figma
│   └── setup-webhooks.mjs      # CLI: create/manage webhooks
├── output/
│   ├── tokens.css              # Generated CSS custom properties
│   ├── tokens.json             # Generated JSON tokens
│   └── icons/                  # Exported SVG/PNG icons
├── tests/
│   ├── fixtures/               # Saved Figma API responses
│   └── *.test.ts
├── .env.example
└── package.json
```

### Step 2: Data Flow Architecture
```
┌────────────────────────────────────────────────┐
│                  Figma Cloud                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │
│  │ Files API │  │Images API│  │ Webhooks V2  │ │
│  │ /v1/files │  │/v1/images│  │ /v2/webhooks │ │
│  └─────┬─────┘  └────┬─────┘  └──────┬───────┘ │
└────────┼──────────────┼───────────────┼─────────┘
         │              │               │
    ┌────▼────┐    ┌────▼────┐    ┌─────▼────┐
    │  Token  │    │  Asset  │    │ Webhook  │
    │Extractor│    │Exporter │    │ Handler  │
    └────┬────┘    └────┬────┘    └─────┬────┘
         │              │               │
    ┌────▼────┐    ┌────▼────┐    ┌─────▼────┐
    │  Cache  │    │  Cache  │    │  Event   │
    │  (LRU)  │    │ (URLs)  │    │  Queue   │
    └────┬────┘    └────┬────┘    └─────┬────┘
         │              │               │
    ┌────▼──────────────▼───────────────▼────┐
    │              Output Layer               │
    │  tokens.css  │  icons/  │  Slack/Jira   │
    └─────────────────────────────────────────┘
```

### Step 3: Key Components

**Figma Client** (see `figma-sdk-patterns`):
```typescript
// Singleton with retry, rate limit handling, and caching
const client = new FigmaClient(process.env.FIGMA_PAT!);

// All API calls go through the client
const file = await client.getFile(fileKey);           // GET /v1/files/:key
const nodes = await client.getFileNodes(fileKey, ids); // GET /v1/files/:key/nodes
const images = await client.getImages(fileKey, ids);   // GET /v1/images/:key
const comments = await client.getComments(fileKey);    // GET /v1/files/:key/comments
const vars = await client.getLocalVariables(fileKey);  // GET /v1/files/:key/variables/local
```

**Token Extraction Pipeline** (see `figma-core-workflow-a`):
```typescript
// file → styles → nodes → CSS/JSON tokens
export async function extractTokens(fileKey: string): Promise<DesignToken[]> {
  const file = await client.getFile(fileKey);
  const styleNodes = await client.getFileNodes(fileKey, Object.keys(file.styles));
  return parseTokensFromNodes(file.styles, styleNodes);
}
```

**Asset Export Pipeline** (see `figma-core-workflow-b`):
```typescript
// file → find components → render images → download
export async function exportIcons(fileKey: string, frameId: string) {
  const frame = await client.getFileNodes(fileKey, [frameId]);
  const componentIds = findComponents(frame).map(n => n.id);
  const imageUrls = await client.getImages(fileKey, componentIds, { format: 'svg' });
  return downloadAll(imageUrls);
}
```

**Webhook Handler** (see `figma-webhooks-events`):
```typescript
// Verify passcode → route event → process async
export function webhookRouter(event: FigmaWebhookEvent) {
  switch (event.event_type) {
    case 'FILE_UPDATE': return handleFileUpdate(event);
    case 'LIBRARY_PUBLISH': return handleLibraryPublish(event);
    case 'FILE_COMMENT': return handleComment(event);
  }
}
```

### Step 4: Configuration
```typescript
// src/config.ts
export const config = {
  figma: {
    token: process.env.FIGMA_PAT!,
    fileKey: process.env.FIGMA_FILE_KEY!,
    webhookPasscode: process.env.FIGMA_WEBHOOK_PASSCODE,
  },
  cache: {
    fileTTL: 5 * 60 * 1000,      // 5 minutes for file metadata
    imageTTL: 24 * 60 * 60 * 1000, // 24 hours for image URLs
    maxEntries: 500,
  },
  api: {
    maxConcurrent: 3,
    retryAttempts: 3,
    requestTimeout: 30_000,
  },
};
```

## Output
- Structured project layout with clear separation
- Data flow from Figma API to local artifacts
- Reusable client, cache, and pipeline components
- Configuration management for all environments

## Error Handling
| Layer | Error | Recovery |
|-------|-------|----------|
| Client | 429 Rate Limited | Retry with `Retry-After` header |
| Client | 403 Forbidden | Alert on token expiry; fail gracefully |
| Cache | Cache miss storm | Stale-while-revalidate pattern |
| Webhook | Duplicate events | Idempotency via event timestamp |
| Export | Image render null | Skip node, log warning |

## Resources
- [Figma REST API](https://developers.figma.com/docs/rest-api/)
- [Figma REST API OpenAPI Spec](https://github.com/figma/rest-api-spec)
- [Figma Webhooks V2](https://developers.figma.com/docs/rest-api/webhooks/)

## Next Steps
For multi-environment setup, see `figma-multi-env-setup`.
