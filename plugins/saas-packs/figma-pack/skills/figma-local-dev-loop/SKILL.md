---
name: figma-local-dev-loop
description: |
  Set up a local development workflow for Figma plugin and REST API projects.
  Use when building Figma plugins, creating design-to-code pipelines,
  or developing against the Figma API with hot reload.
  Trigger with phrases like "figma dev setup", "figma plugin development",
  "figma local development", "develop figma plugin".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, figma]
compatible-with: claude-code
---

# Figma Local Dev Loop

## Overview
Set up fast local development for two workflows: building Figma plugins that run inside the Figma editor, and building external apps that consume the Figma REST API.

## Prerequisites
- Node.js 18+ with npm/pnpm
- `FIGMA_PAT` configured (see `figma-install-auth`)
- Figma desktop app (for plugin development)

## Instructions

### Step 1: REST API Project Structure
```
figma-integration/
├── src/
│   ├── figma-client.ts       # Shared fetch wrapper
│   ├── extract-tokens.ts     # Design token extraction
│   └── export-assets.ts      # Asset export pipeline
├── tests/
│   ├── figma-client.test.ts
│   └── fixtures/             # Saved API responses for offline testing
│       └── sample-file.json
├── .env.local                # FIGMA_PAT, FIGMA_FILE_KEY (git-ignored)
├── .env.example              # Template for team
├── tsconfig.json
└── package.json
```

### Step 2: Figma Plugin Project Structure
```
my-figma-plugin/
├── manifest.json             # Plugin manifest (required by Figma)
├── code.ts                   # Plugin backend (runs in sandbox)
├── ui.html                   # Plugin UI (runs in iframe)
├── package.json
└── tsconfig.json
```

**manifest.json** (required):
```json
{
  "name": "My Plugin",
  "id": "1234567890",
  "api": "1.0.0",
  "main": "dist/code.js",
  "ui": "dist/ui.html",
  "editorType": ["figma"],
  "permissions": ["currentuser"]
}
```

### Step 3: Plugin Development with Watch Mode
```json
{
  "scripts": {
    "build": "esbuild code.ts --bundle --outfile=dist/code.js --target=es2020",
    "watch": "esbuild code.ts --bundle --outfile=dist/code.js --target=es2020 --watch",
    "dev": "concurrently \"npm run watch\" \"npm run watch:ui\"",
    "watch:ui": "esbuild ui.tsx --bundle --outfile=dist/ui.html --loader:.html=copy --watch"
  },
  "devDependencies": {
    "@figma/plugin-typings": "^1.0.0",
    "esbuild": "^0.20.0",
    "typescript": "^5.0.0"
  }
}
```

Load the plugin in Figma:
1. Figma desktop > Plugins > Development > Import plugin from manifest
2. Select your `manifest.json`
3. Run with `npm run watch` -- changes auto-reload

### Step 4: REST API Dev Loop with Testing
```json
{
  "scripts": {
    "dev": "tsx watch src/extract-tokens.ts",
    "test": "vitest",
    "test:watch": "vitest --watch"
  }
}
```

```typescript
// tests/figma-client.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { readFileSync } from 'fs';

// Load a saved API response for offline testing
const sampleFile = JSON.parse(
  readFileSync('tests/fixtures/sample-file.json', 'utf-8')
);

describe('Figma token extraction', () => {
  beforeEach(() => {
    // Mock fetch to return saved fixture
    vi.spyOn(global, 'fetch').mockResolvedValue(
      new Response(JSON.stringify(sampleFile), { status: 200 })
    );
  });

  it('should extract color styles from file', async () => {
    const res = await fetch('https://api.figma.com/v1/files/test-key');
    const file = await res.json();
    const styles = Object.values(file.styles);
    expect(styles.length).toBeGreaterThan(0);
  });
});
```

### Step 5: Save API Fixtures for Offline Dev
```bash
# Snapshot a Figma file for offline testing
curl -s -H "X-Figma-Token: ${FIGMA_PAT}" \
  "https://api.figma.com/v1/files/${FIGMA_FILE_KEY}" \
  > tests/fixtures/sample-file.json

# Snapshot specific nodes
curl -s -H "X-Figma-Token: ${FIGMA_PAT}" \
  "https://api.figma.com/v1/files/${FIGMA_FILE_KEY}/nodes?ids=0:1,0:2" \
  > tests/fixtures/sample-nodes.json
```

## Output
- Working dev environment with hot reload
- Test suite with mocked Figma API responses
- Saved fixtures for offline development
- Plugin manifest configured for Figma desktop loading

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Plugin not appearing in Figma | Wrong manifest path | Re-import from correct `manifest.json` |
| `figma` global undefined | Running outside Figma sandbox | Use `@figma/plugin-typings` for types only |
| Fixture stale | File changed since snapshot | Re-run fixture download script |
| esbuild watch crash | Syntax error in TS | Fix error; watch auto-restarts |

## Examples

### Quick Plugin Skeleton
```typescript
// code.ts -- minimal Figma plugin
figma.showUI(__html__, { width: 300, height: 200 });

figma.ui.onmessage = (msg: { type: string; count: number }) => {
  if (msg.type === 'create-rectangles') {
    for (let i = 0; i < msg.count; i++) {
      const rect = figma.createRectangle();
      rect.x = i * 150;
      rect.fills = [{ type: 'SOLID', color: { r: 1, g: 0.5, b: 0 } }];
      figma.currentPage.appendChild(rect);
    }
    figma.closePlugin();
  }
};
```

## Resources
- [Figma Plugin Development Guide](https://developers.figma.com/docs/plugins/)
- [Plugin API Reference](https://developers.figma.com/docs/plugins/api/api-reference/)
- [@figma/plugin-typings](https://www.npmjs.com/package/@figma/plugin-typings)
- [Vitest Documentation](https://vitest.dev/)

## Next Steps
See `figma-sdk-patterns` for production-ready code patterns.
