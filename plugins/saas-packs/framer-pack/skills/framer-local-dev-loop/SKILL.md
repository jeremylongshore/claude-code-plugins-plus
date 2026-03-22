---
name: framer-local-dev-loop
description: |
  Configure Framer local development with hot reload and testing.
  Use when setting up a development environment, configuring test workflows,
  or establishing a fast iteration cycle with Framer.
  Trigger with phrases like "framer dev setup", "framer local development",
  "framer dev environment", "develop with framer".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, framer]
compatible-with: claude-code
---

# Framer Local Dev Loop

## Overview

Set up a fast development workflow for Framer plugins and code components with Vite hot-reload, TypeScript, and testing.

## Prerequisites

- Completed `framer-install-auth` setup
- Node.js 18+ with npm
- Framer editor open

## Instructions

### Step 1: Plugin Dev Environment

```bash
npx create-framer-plugin@latest my-plugin
cd my-plugin
npm install
npm run dev  # Starts Vite dev server — hot-reloads into Framer editor
```

Project structure:
```
my-plugin/
├── src/
│   ├── App.tsx           # Plugin UI (React)
│   ├── main.tsx          # Entry point
│   └── framer.d.ts       # Type definitions
├── package.json
├── vite.config.ts        # Vite config with framer-plugin
└── tsconfig.json
```

### Step 2: Connect to Framer Editor

1. Open Framer, go to your project
2. Click **Plugins** > **Development** in the toolbar
3. Select your local dev plugin
4. Changes in `src/App.tsx` hot-reload instantly

### Step 3: Testing Plugin Logic

```typescript
// tests/sync.test.ts — test data transformation outside Framer
import { describe, it, expect } from 'vitest';

// Extract pure functions for testability
function transformPosts(posts: any[]) {
  return posts.map(p => ({
    fieldData: {
      title: p.title,
      body: `<p>${p.body}</p>`,
      slug: p.title.toLowerCase().replace(/[^a-z0-9]+/g, '-').slice(0, 50),
    },
  }));
}

describe('CMS Sync', () => {
  it('should transform posts into CMS items', () => {
    const posts = [{ title: 'Hello World', body: 'Content here', userId: 1 }];
    const items = transformPosts(posts);
    expect(items[0].fieldData.title).toBe('Hello World');
    expect(items[0].fieldData.slug).toBe('hello-world');
    expect(items[0].fieldData.body).toContain('<p>');
  });

  it('should handle slugs with special characters', () => {
    const posts = [{ title: 'What\'s New in 2025?', body: 'test', userId: 1 }];
    const items = transformPosts(posts);
    expect(items[0].fieldData.slug).toBe('what-s-new-in-2025-');
  });
});
```

### Step 4: Code Component Development

```bash
# Code components are edited directly in Framer editor
# For local development of shared component libraries:
mkdir framer-components && cd framer-components
npm init -y
npm install react framer typescript @types/react
```

```tsx
// components/Button.tsx — develop locally, paste into Framer
import { addPropertyControls, ControlType } from 'framer';

export default function Button({ label = 'Click me', variant = 'primary' }) {
  const styles = {
    primary: { background: '#000', color: '#fff' },
    secondary: { background: '#eee', color: '#000' },
  };
  return <button style={{ ...styles[variant], padding: '12px 24px', border: 'none', borderRadius: 8, fontSize: 16, cursor: 'pointer' }}>{label}</button>;
}

addPropertyControls(Button, {
  label: { type: ControlType.String, title: 'Label', defaultValue: 'Click me' },
  variant: { type: ControlType.Enum, title: 'Variant', options: ['primary', 'secondary'], defaultValue: 'primary' },
});
```

### Step 5: Server API Development

```typescript
// server-dev.ts — develop Server API integrations locally
import { framer } from 'framer-api';
import 'dotenv/config';

async function dev() {
  const client = await framer.connect({
    apiKey: process.env.FRAMER_API_KEY!,
    siteId: process.env.FRAMER_SITE_ID!,
  });

  // Test CMS operations
  const collections = await client.getCollections();
  console.log('Collections:', collections.map(c => `${c.name} (${c.type})`));
}

dev().catch(console.error);
```

## Output

- Vite-powered plugin with hot-reload into Framer editor
- Testable data transformation functions
- Local component development workflow
- Server API development setup

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Plugin not showing | Dev server not running | Run `npm run dev` |
| Hot-reload not working | Wrong Vite config | Ensure `framer-plugin` Vite plugin is configured |
| `framer` undefined in tests | Editor-only API | Mock `framer` or extract pure functions |
| Component type errors | Missing Framer types | Install `@types/framer` or use `framer.d.ts` |

## Resources

- [create-framer-plugin](https://www.framer.com/developers/plugins-introduction)
- [Framer Developer Reference](https://www.framer.com/developers/reference)
- [Vitest](https://vitest.dev/)

## Next Steps

See `framer-sdk-patterns` for production-ready patterns.
