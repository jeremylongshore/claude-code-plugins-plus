---
name: stackblitz-local-dev-loop
description: |
  Configure local development for WebContainer applications with hot reload and testing.
  Use when building browser-based IDEs, testing WebContainer file operations,
  or setting up development workflows for WebContainer projects.
  Trigger: "stackblitz dev setup", "webcontainer local", "test webcontainers locally".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ide, webcontainers, stackblitz]
compatible-with: claude-code
---

# StackBlitz Local Dev Loop

## Overview

Set up a Vite-based development environment for WebContainer applications with cross-origin headers, hot module replacement, and Vitest for testing file system operations.

## Instructions

### Step 1: Vite Project with WebContainers

```bash
npm create vite@latest wc-app -- --template vanilla-ts
cd wc-app
npm install @webcontainer/api
```

### Step 2: Configure Vite Headers

```typescript
// vite.config.ts
import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    headers: {
      'Cross-Origin-Embedder-Policy': 'require-corp',
      'Cross-Origin-Opener-Policy': 'same-origin',
    },
  },
});
```

### Step 3: Test WebContainer Operations

```typescript
// tests/webcontainer.test.ts
import { describe, it, expect } from 'vitest';

// Note: WebContainer tests require a browser environment
// Use Playwright for full integration tests
describe('FileSystemTree Builder', () => {
  it('creates valid tree from flat paths', () => {
    const tree = buildFileTree({
      'src/index.ts': 'console.log("hello")',
      'package.json': '{"name":"test"}',
    });
    expect(tree['package.json']).toHaveProperty('file');
    expect(tree.src).toHaveProperty('directory');
  });
});

function buildFileTree(flatFiles: Record<string, string>) {
  const tree: any = {};
  for (const [path, contents] of Object.entries(flatFiles)) {
    const parts = path.split('/');
    let current = tree;
    for (let i = 0; i < parts.length - 1; i++) {
      if (!current[parts[i]]) current[parts[i]] = { directory: {} };
      current = current[parts[i]].directory;
    }
    current[parts[parts.length - 1]] = { file: { contents } };
  }
  return tree;
}
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| COOP/COEP errors | Missing headers | Add to vite.config.ts |
| `SharedArrayBuffer` undefined | Not cross-origin isolated | Check response headers |
| Test failures | WebContainer needs browser | Use Playwright for integration |

## Resources

- [Vite Config](https://vitejs.dev/config/)
- [WebContainer Guides](https://webcontainers.io/guides/introduction)

## Next Steps

Proceed to `stackblitz-sdk-patterns` for production patterns.
