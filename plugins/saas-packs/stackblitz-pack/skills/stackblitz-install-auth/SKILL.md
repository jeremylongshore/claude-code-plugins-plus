---
name: stackblitz-install-auth
description: |
  Install the WebContainer API and configure StackBlitz SDK for browser-based Node.js.
  Use when setting up WebContainers, embedding StackBlitz projects,
  or initializing the @stackblitz/sdk package.
  Trigger: "install stackblitz", "setup webcontainers", "stackblitz SDK".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ide, webcontainers, stackblitz]
compatible-with: claude-code
---

# StackBlitz Install & Auth

## Overview

Set up the WebContainer API for running Node.js in the browser, or the StackBlitz SDK for embedding interactive code editors. WebContainers require no auth -- they run entirely client-side. The StackBlitz SDK is for embedding projects from stackblitz.com.

## Prerequisites

- Node.js 18+ for build tooling
- Modern browser with SharedArrayBuffer support (requires HTTPS + COOP/COEP headers)

## Instructions

### Step 1: Install WebContainer API

```bash
npm install @webcontainer/api
```

### Step 2: Install StackBlitz SDK (for embedding)

```bash
npm install @stackblitz/sdk
```

### Step 3: Configure Required HTTP Headers

WebContainers require cross-origin isolation. Add these headers to your server:

```typescript
// Express middleware
app.use((req, res, next) => {
  res.setHeader('Cross-Origin-Embedder-Policy', 'require-corp');
  res.setHeader('Cross-Origin-Opener-Policy', 'same-origin');
  next();
});
```

```javascript
// Vite config
export default defineConfig({
  server: {
    headers: {
      'Cross-Origin-Embedder-Policy': 'require-corp',
      'Cross-Origin-Opener-Policy': 'same-origin',
    },
  },
});
```

### Step 4: Verify WebContainer Boot

```typescript
import { WebContainer } from '@webcontainer/api';

const wc = await WebContainer.boot();
console.log('WebContainer booted successfully');

// Verify filesystem works
await wc.mount({ 'test.txt': { file: { contents: 'Hello WebContainers!' } } });
const content = await wc.fs.readFile('/test.txt', 'utf-8');
console.log(`File content: ${content}`);
```

## Output

```
WebContainer booted successfully
File content: Hello WebContainers!
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `SharedArrayBuffer is not defined` | Missing COOP/COEP headers | Add cross-origin isolation headers |
| `Failed to boot` | Multiple instances | Only one WebContainer per page |
| `Not in secure context` | HTTP instead of HTTPS | Use HTTPS or localhost |

## Resources

- [WebContainer API Docs](https://webcontainers.io/)
- [WebContainer Quickstart](https://webcontainers.io/guides/quickstart)
- [StackBlitz SDK](https://developer.stackblitz.com/platform/api/javascript-sdk)

## Next Steps

Proceed to `stackblitz-hello-world` for your first WebContainer project.
