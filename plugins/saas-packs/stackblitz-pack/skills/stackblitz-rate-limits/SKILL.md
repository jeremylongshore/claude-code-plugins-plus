---
name: stackblitz-rate-limits
description: |
  WebContainer resource limits: memory, CPU, file system size, process count.
  Use when working with WebContainers or StackBlitz SDK.
  Trigger: "webcontainer limits".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ide, webcontainers, stackblitz]
compatible-with: claude-code
---

# StackBlitz Rate Limits

## Overview

WebContainer resource limits: memory, CPU, file system size, process count.

## Instructions

### Step 1: WebContainer Resource Limits

| Resource | Limit | Notes |
|----------|-------|-------|
| Memory | ~2GB | Shared with browser tab |
| File system | Ephemeral, in-memory | Lost on page refresh |
| Processes | Multiple concurrent | Each consumes memory |
| Network | HTTP only | No raw TCP/UDP sockets |
| npm packages | Most work | Native addons not supported |

### Step 2: Handle Memory Pressure

```typescript
// Monitor memory usage inside WebContainer
const proc = await wc.spawn('node', ['-e', `
  setInterval(() => {
    const mem = process.memoryUsage();
    const mbUsed = Math.round(mem.heapUsed / 1024 / 1024);
    if (mbUsed > 500) console.warn('High memory: ' + mbUsed + 'MB');
  }, 5000);
`]);
```

### Step 3: Optimize File System Size

```typescript
// Mount only essential files -- skip test files, docs, etc.
const productionFiles: FileSystemTree = {
  'package.json': { file: { contents: minimalPackageJson } },
  src: { directory: { /* only source files */ } },
  // Skip: tests/, docs/, .git/, large assets
};
await wc.mount(productionFiles);
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Tab crashes | OOM | Reduce mounted files, fewer deps |
| Slow npm install | Large deps | Use --prefer-offline, fewer packages |
| Process killed | Memory limit | Monitor with memoryUsage() |

## Resources

- [WebContainer Guides](https://webcontainers.io/guides/introduction)

## Next Steps

For security, see `stackblitz-security-basics`.
