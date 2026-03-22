---
name: stackblitz-debug-bundle
description: |
  Collect WebContainer diagnostic info: boot state, file system, process list.
  Use when working with WebContainers or StackBlitz SDK.
  Trigger: "stackblitz debug".
allowed-tools: Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ide, webcontainers, stackblitz]
compatible-with: claude-code
---

# StackBlitz Debug Bundle

## Overview

Collect WebContainer diagnostic info: boot state, file system, process list.

## Instructions

### Step 1: Check Boot State

```typescript
async function diagnoseWebContainer(wc: WebContainer) {
  const report: Record<string, any> = {};

  // File system check
  try {
    const entries = await wc.fs.readdir('/');
    report.filesystem = { status: 'ok', rootEntries: entries.length };
  } catch (e: any) {
    report.filesystem = { status: 'error', message: e.message };
  }

  // Node.js check
  try {
    const proc = await wc.spawn('node', ['-e', 'console.log(JSON.stringify({version: process.version, arch: process.arch}))']);
    let output = '';
    proc.output.pipeTo(new WritableStream({ write(data) { output += data; } }));
    await proc.exit;
    report.node = JSON.parse(output);
  } catch (e: any) {
    report.node = { status: 'error', message: e.message };
  }

  // Memory check
  try {
    const proc = await wc.spawn('node', ['-e', 'console.log(JSON.stringify(process.memoryUsage()))']);
    let output = '';
    proc.output.pipeTo(new WritableStream({ write(data) { output += data; } }));
    await proc.exit;
    report.memory = JSON.parse(output);
  } catch { report.memory = 'unavailable'; }

  return report;
}
```

### Step 2: Check Browser Support

```typescript
function checkBrowserSupport() {
  return {
    sharedArrayBuffer: typeof SharedArrayBuffer !== 'undefined',
    crossOriginIsolated: window.crossOriginIsolated,
    serviceWorker: 'serviceWorker' in navigator,
    userAgent: navigator.userAgent,
  };
}
```

## Error Handling

| Check | Expected | Failed Action |
|-------|----------|---------------|
| SharedArrayBuffer | defined | Add COOP/COEP headers |
| crossOriginIsolated | true | Check all headers present |
| Node.js version | v18+ | WebContainer ships its own |
| Root FS entries | > 0 | Re-mount files |

## Resources

- [WebContainer API Reference](https://webcontainers.io/api)
- [Browser Support](https://webcontainers.io/guides/browser-support)

## Next Steps

For resource limits, see `stackblitz-rate-limits`.
