---
name: framer-performance-tuning
description: |
  Optimize Framer API performance with caching, batching, and connection pooling.
  Use when experiencing slow API responses, implementing caching strategies,
  or optimizing request throughput for Framer integrations.
  Trigger with phrases like "framer performance", "optimize framer",
  "framer latency", "framer caching", "framer slow", "framer batch".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, framer]
compatible-with: claude-code
---

# Framer Performance Tuning

## Overview

Optimize Framer plugin, component, and Server API performance. Key areas: CMS sync speed, component render performance, and plugin responsiveness.

## Instructions

### Step 1: Batch CMS Operations

```typescript
// Process large collections in batches to avoid timeouts
async function batchSync(collection: any, items: any[], batchSize = 50) {
  const total = items.length;
  for (let i = 0; i < total; i += batchSize) {
    await collection.setItems(items.slice(i, i + batchSize));
    const progress = Math.min(i + batchSize, total);
    framer.notify(`Synced ${progress}/${total}`);
  }
}
```

### Step 2: Optimize Code Component Rendering

```tsx
import { memo, useMemo } from 'react';

// Memoize expensive components
export default memo(function DataGrid({ data, columns }) {
  const processedData = useMemo(() =>
    data.map(row => columns.reduce((acc, col) => ({ ...acc, [col.key]: row[col.key] }), {})),
    [data, columns]
  );

  return (
    <div style={{ display: 'grid', gridTemplateColumns: `repeat(${columns.length}, 1fr)` }}>
      {processedData.map((row, i) => columns.map(col => (
        <div key={`${i}-${col.key}`} style={{ padding: 8 }}>{row[col.key]}</div>
      )))}
    </div>
  );
});
```

### Step 3: Persistent WebSocket Connection

```typescript
// Reuse Server API connection instead of reconnecting each time
let clientInstance: any = null;

async function getClient() {
  if (!clientInstance) {
    const { framer } = await import('framer-api');
    clientInstance = await framer.connect({
      apiKey: process.env.FRAMER_API_KEY!,
      siteId: process.env.FRAMER_SITE_ID!,
    });
  }
  return clientInstance;
}
```

### Step 4: Image Optimization

```typescript
// Pre-optimize image URLs before syncing to CMS
function optimizeImageUrl(url: string, width = 800): string {
  // Use image CDN if available
  if (url.includes('cloudinary.com')) {
    return url.replace('/upload/', `/upload/w_${width},q_auto,f_auto/`);
  }
  if (url.includes('imgix.net')) {
    return `${url}?w=${width}&auto=format,compress`;
  }
  return url;
}
```

## Output

- Batched CMS operations avoiding timeouts
- Memoized components for render performance
- Persistent WebSocket connections
- Image optimization before CMS sync

## Resources

- [Framer Performance](https://www.framer.com/developers/reference)
- [React Performance](https://react.dev/reference/react/memo)

## Next Steps

For cost optimization, see `framer-cost-tuning`.
