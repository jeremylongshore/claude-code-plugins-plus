---
name: stackblitz-core-workflow-b
description: |
  Embed StackBlitz projects and manage WebContainer snapshots for sharing.
  Use when embedding code playgrounds in docs, creating shareable examples,
  or building interactive tutorials with StackBlitz.
  Trigger: "embed stackblitz", "stackblitz embed", "stackblitz share project".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ide, webcontainers, stackblitz]
compatible-with: claude-code
---

# StackBlitz Core Workflow B: Embedding & Sharing

## Overview

Embed interactive StackBlitz projects in documentation, blog posts, and tutorials using the StackBlitz SDK. Supports embedding from GitHub repos, existing StackBlitz projects, or inline code.

## Instructions

### Step 1: Embed from GitHub

```typescript
import sdk from '@stackblitz/sdk';

// Embed a GitHub repo as an interactive editor
sdk.embedGithubProject('embed-container', 'vitejs/vite/packages/create-vite/template-react-ts', {
  openFile: 'src/App.tsx',
  height: 500,
  theme: 'dark',
  clickToLoad: true,  // Don't load until user clicks
});
```

### Step 2: Embed Inline Project

```typescript
sdk.embedProject('embed-container', {
  title: 'React Counter Demo',
  template: 'node',
  files: {
    'src/App.tsx': `
import { useState } from 'react';
export default function App() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(c => c + 1)}>Count: {count}</button>;
}`,
    'package.json': JSON.stringify({
      dependencies: { react: '^18', 'react-dom': '^18' },
    }),
  },
}, {
  openFile: 'src/App.tsx',
  terminalHeight: 25,
});
```

### Step 3: Open in New Tab

```typescript
// Open project in full StackBlitz editor
sdk.openGithubProject('user/repo', { openFile: 'README.md' });

// Open inline project
sdk.openProject({
  title: 'Quick Demo',
  template: 'node',
  files: { 'index.js': 'console.log("Hello!")' },
});
```

### Step 4: URL-Based Embedding

```html
<!-- iframe embed (no SDK needed) -->
<iframe
  src="https://stackblitz.com/edit/vitejs-vite?embed=1&file=src/main.ts&theme=dark"
  style="width:100%;height:500px;border:0;border-radius:4px;overflow:hidden;"
></iframe>

<!-- GitHub repo embed -->
<iframe
  src="https://stackblitz.com/github/user/repo?embed=1&file=README.md"
  style="width:100%;height:500px;border:0;"
></iframe>
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Embed shows loading forever | Missing template files | Ensure `package.json` is included |
| `clickToLoad` not working | SDK version mismatch | Update `@stackblitz/sdk` |
| GitHub embed 404 | Wrong repo path | Use `owner/repo/path/to/subdir` format |

## Resources

- [StackBlitz SDK](https://developer.stackblitz.com/platform/api/javascript-sdk)
- [Embed URL Parameters](https://developer.stackblitz.com/platform/api/embed-url)
- [WebContainer API](https://developer.stackblitz.com/platform/api/webcontainer-api)

## Next Steps

For common errors, see `stackblitz-common-errors`.
