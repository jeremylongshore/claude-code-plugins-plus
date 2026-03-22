---
name: stackblitz-security-basics
description: |
  Secure WebContainer deployments: CSP headers, sandbox isolation, input validation.
  Use when working with WebContainers or StackBlitz SDK.
  Trigger: "stackblitz security".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ide, webcontainers, stackblitz]
compatible-with: claude-code
---

# StackBlitz Security Basics

## Overview

Secure WebContainer deployments: CSP headers, sandbox isolation, input validation.

## Instructions

### Step 1: WebContainer Security Model

WebContainers run in the browser sandbox -- no access to host filesystem, network is limited to HTTP, and all code runs in the user's browser tab. Key security points:

```typescript
// WebContainers are inherently sandboxed:
// - No file system access to host
// - No raw network sockets
// - Memory isolated to browser tab
// - Cross-origin isolation via COOP/COEP headers
```

### Step 2: Validate User Input

```typescript
// If users can provide code to run in WebContainer, validate:
function sanitizeFileTree(tree: FileSystemTree): FileSystemTree {
  const sanitized: FileSystemTree = {};
  for (const [name, entry] of Object.entries(tree)) {
    // Block path traversal
    if (name.includes('..') || name.startsWith('/')) continue;
    // Block sensitive files
    if (name === '.env' || name.endsWith('.key')) continue;
    sanitized[name] = entry;
  }
  return sanitized;
}
```

### Step 3: Content Security Policy

```
Content-Security-Policy: default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; frame-src https://*.webcontainer.io;
```

## Security Checklist

- [ ] COOP/COEP headers set correctly
- [ ] User-provided code sandboxed in WebContainer
- [ ] No secrets passed to WebContainer file system
- [ ] CSP headers configured
- [ ] Input validation on file paths

## Resources

- [WebContainer Security](https://webcontainers.io/guides/introduction)

## Next Steps

For production, see `stackblitz-prod-checklist`.
