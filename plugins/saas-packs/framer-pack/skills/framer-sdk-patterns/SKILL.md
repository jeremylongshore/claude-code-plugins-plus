---
name: framer-sdk-patterns
description: |
  Apply production-ready Framer SDK patterns for TypeScript and Python.
  Use when implementing Framer integrations, refactoring SDK usage,
  or establishing team coding standards for Framer.
  Trigger with phrases like "framer SDK patterns", "framer best practices",
  "framer code patterns", "idiomatic framer".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, framer]
compatible-with: claude-code
---

# Framer SDK Patterns

## Overview

Production-ready patterns for Framer plugins, Server API, code components, and CMS integrations. Covers plugin architecture, type-safe CMS operations, and reusable component patterns.

## Prerequisites

- Completed `framer-install-auth` setup
- Familiarity with React and TypeScript

## Instructions

### Step 1: Type-Safe CMS Operations

```typescript
// src/cms/types.ts — type-safe field definitions
interface BlogPost {
  title: string;
  body: string;
  author: string;
  publishDate: string;
  featured: boolean;
  slug: string;
}

const BLOG_FIELDS = [
  { id: 'title' as const, name: 'Title', type: 'string' as const },
  { id: 'body' as const, name: 'Body', type: 'formattedText' as const },
  { id: 'author' as const, name: 'Author', type: 'string' as const },
  { id: 'publishDate' as const, name: 'Published', type: 'date' as const },
  { id: 'featured' as const, name: 'Featured', type: 'boolean' as const },
  { id: 'slug' as const, name: 'Slug', type: 'slug' as const, userEditable: false },
] as const;

function toBlogItem(post: BlogPost) {
  return { fieldData: { ...post } };
}
```

### Step 2: Plugin State Management

```tsx
// src/hooks/usePluginState.ts
import { useState, useCallback } from 'react';
import { framer } from 'framer-plugin';

type SyncStatus = 'idle' | 'fetching' | 'syncing' | 'success' | 'error';

export function useSyncState() {
  const [status, setStatus] = useState<SyncStatus>('idle');
  const [error, setError] = useState<string | null>(null);
  const [count, setCount] = useState(0);

  const sync = useCallback(async (fn: () => Promise<number>) => {
    setStatus('syncing');
    setError(null);
    try {
      const synced = await fn();
      setCount(synced);
      setStatus('success');
      framer.notify(`Synced ${synced} items`);
    } catch (err: any) {
      setError(err.message);
      setStatus('error');
      framer.notify(`Sync failed: ${err.message}`);
    }
  }, []);

  return { status, error, count, sync };
}
```

### Step 3: Reusable Component Patterns

```tsx
// Responsive container pattern
import { addPropertyControls, ControlType } from 'framer';

export default function ResponsiveCard({ title, description, imageUrl, ctaText, ctaUrl }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', borderRadius: 12, overflow: 'hidden', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
      {imageUrl && <img src={imageUrl} style={{ width: '100%', aspectRatio: '16/9', objectFit: 'cover' }} />}
      <div style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 8 }}>
        <h3 style={{ margin: 0, fontSize: 20 }}>{title}</h3>
        <p style={{ margin: 0, color: '#666', fontSize: 14 }}>{description}</p>
        {ctaText && <a href={ctaUrl} style={{ color: '#007AFF', fontWeight: 600, textDecoration: 'none' }}>{ctaText}</a>}
      </div>
    </div>
  );
}

addPropertyControls(ResponsiveCard, {
  title: { type: ControlType.String, defaultValue: 'Card Title' },
  description: { type: ControlType.String, defaultValue: 'Card description here' },
  imageUrl: { type: ControlType.String, defaultValue: '' },
  ctaText: { type: ControlType.String, defaultValue: 'Learn More' },
  ctaUrl: { type: ControlType.String, defaultValue: '#' },
});
```

### Step 4: Server API Wrapper

```typescript
// src/server/framer-client.ts
import { framer } from 'framer-api';

export class FramerCMSClient {
  private client: any;

  async connect() {
    this.client = await framer.connect({
      apiKey: process.env.FRAMER_API_KEY!,
      siteId: process.env.FRAMER_SITE_ID!,
    });
  }

  async syncCollection(name: string, fields: any[], items: any[]) {
    const collections = await this.client.getCollections();
    let collection = collections.find(c => c.name === name);
    if (!collection) {
      collection = await this.client.createManagedCollection({ name, fields });
    }
    await collection.setItems(items);
    return items.length;
  }

  async publish() {
    await this.client.publish();
  }
}
```

### Step 5: Override Factory Pattern

```tsx
// src/overrides/factory.ts — generate overrides programmatically
import { Override } from 'framer';

export function createFadeIn(delay = 0, duration = 0.6): () => Override {
  return () => ({
    initial: { opacity: 0, y: 20 },
    whileInView: { opacity: 1, y: 0 },
    transition: { duration, delay, ease: [0.25, 0.1, 0.25, 1] },
    viewport: { once: true },
  });
}

// Usage in overrides file:
export const FadeIn1 = createFadeIn(0);
export const FadeIn2 = createFadeIn(0.1);
export const FadeIn3 = createFadeIn(0.2);
```

## Output

- Type-safe CMS field definitions
- Plugin state management hook
- Reusable component with property controls
- Server API wrapper class
- Override factory pattern

## Error Handling

| Pattern | Use Case | Benefit |
|---------|----------|---------|
| Type-safe fields | CMS collections | Catch schema errors at compile time |
| State hook | Plugin UI | Consistent loading/error states |
| Component patterns | Design systems | Reusable across projects |
| Override factory | Staggered animations | DRY animation code |

## Resources

- [Framer API Reference](https://www.framer.com/developers/reference)
- [Server API](https://www.framer.com/developers/server-api-introduction)
- [Plugin Components](https://www.framer.com/developers/plugins-with-components)

## Next Steps

Apply patterns in `framer-core-workflow-a` for CMS sync plugins.
