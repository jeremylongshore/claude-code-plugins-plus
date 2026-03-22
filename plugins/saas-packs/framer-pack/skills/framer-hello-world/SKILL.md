---
name: framer-hello-world
description: |
  Create a minimal working Framer example.
  Use when starting a new Framer integration, testing your setup,
  or learning basic Framer API patterns.
  Trigger with phrases like "framer hello world", "framer example",
  "framer quick start", "simple framer code".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, framer]
compatible-with: claude-code
---

# Framer Hello World

## Overview

Build a minimal Framer plugin that inserts a styled text layer onto the canvas, and a code component that renders inside Framer sites. Both use the `framer-plugin` SDK which provides the `framer` global for editor interaction.

## Prerequisites

- Completed `framer-install-auth` setup
- Framer editor open with a project
- Plugin dev server running (`npm run dev`)

## Instructions

### Step 1: Hello World Plugin

```tsx
// src/App.tsx — Plugin UI that runs inside Framer editor
import { framer } from 'framer-plugin';

framer.showUI({ width: 300, height: 200, title: 'Hello World Plugin' });

export function App() {
  const insertText = async () => {
    await framer.addText('Hello from my plugin!', {
      position: { x: 100, y: 100 },
      style: { fontSize: 24, color: '#333' },
    });
    framer.notify('Text inserted on canvas!');
  };

  const insertImage = async () => {
    await framer.addImage({
      url: 'https://picsum.photos/400/300',
      position: { x: 100, y: 200 },
    });
  };

  return (
    <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 8 }}>
      <h2>Hello World</h2>
      <button onClick={insertText}>Insert Text</button>
      <button onClick={insertImage}>Insert Image</button>
    </div>
  );
}
```

### Step 2: Hello World Code Component

```tsx
// Code component — renders inside Framer sites (not a plugin)
// Create via: Framer editor > Assets > Code > New Component
import { addPropertyControls, ControlType } from 'framer';

interface Props {
  text: string;
  color: string;
}

export default function HelloComponent({ text, color }: Props) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100%',
      fontSize: 24,
      fontWeight: 600,
      color,
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      borderRadius: 12,
      padding: 20,
    }}>
      {text}
    </div>
  );
}

addPropertyControls(HelloComponent, {
  text: { type: ControlType.String, title: 'Text', defaultValue: 'Hello Framer!' },
  color: { type: ControlType.Color, title: 'Color', defaultValue: '#ffffff' },
});
```

### Step 3: Hello World Code Override

```tsx
// Code override — modifies existing layer behavior
// Create via: Framer editor > Assets > Code > New Override
import { Override } from 'framer';

export function FadeInOnScroll(): Override {
  return {
    initial: { opacity: 0, y: 20 },
    whileInView: { opacity: 1, y: 0 },
    transition: { duration: 0.6, ease: 'easeOut' },
    viewport: { once: true },
  };
}

export function HoverScale(): Override {
  return {
    whileHover: { scale: 1.05 },
    whileTap: { scale: 0.95 },
    transition: { type: 'spring', stiffness: 400, damping: 17 },
  };
}
```

### Step 4: Server API Hello World

```typescript
// server-hello.ts — headless access without opening Framer
import { framer } from 'framer-api';

async function main() {
  const client = await framer.connect({
    apiKey: process.env.FRAMER_API_KEY!,
    siteId: process.env.FRAMER_SITE_ID!,
  });

  // List all pages
  const pages = await client.getPages();
  console.log('Pages:', pages.map(p => p.name));

  // List CMS collections
  const collections = await client.getCollections();
  for (const col of collections) {
    const items = await col.getItems();
    console.log(`Collection "${col.name}": ${items.length} items`);
  }
}

main().catch(console.error);
```

## Output

- Working plugin that inserts text and images onto the Framer canvas
- Code component with property controls
- Code overrides for animation behaviors
- Server API script listing pages and CMS collections

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `framer is not defined` | Running outside editor | Plugin code only works in Framer editor iframe |
| Component not rendering | Missing export default | Code components must use `export default` |
| Override not applying | Wrong export name | Each override must be a named export function |
| Server API timeout | Invalid site ID | Check FRAMER_SITE_ID in site settings |

## Resources

- [Framer Plugin Introduction](https://www.framer.com/developers/plugins-introduction)
- [Code Components](https://www.framer.com/developers/plugins-with-components)
- [Code Overrides](https://www.framer.com/developers/overrides-introduction)
- [Server API](https://www.framer.com/developers/server-api-introduction)

## Next Steps

Proceed to `framer-local-dev-loop` for development workflow.
