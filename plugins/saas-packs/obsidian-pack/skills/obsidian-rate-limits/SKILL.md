---
name: obsidian-rate-limits
description: |
  Handle Obsidian file system operations and throttling patterns.
  Use when processing many files, handling bulk operations,
  or preventing performance issues from excessive operations.
  Trigger with phrases like "obsidian rate limit", "obsidian bulk operations",
  "obsidian file throttling", "obsidian performance limits".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Obsidian Rate Limits

## Overview
Throttling patterns for Obsidian plugin file system operations. Obsidian runs on Electron with single-threaded UI -- excessive vault operations freeze the interface and risk data corruption.

## Prerequisites
- Understanding of Obsidian's event loop
- Familiarity with async JavaScript patterns
- Awareness of vault size impact on operations

## Obsidian Operation Limits

| Operation | Safe Limit | Risk if Exceeded |
|-----------|-----------|------------------|
| File reads | 100/sec | UI freeze |
| File writes | 10/sec | Sync conflicts, data corruption |
| Metadata cache reads | 500/sec | Memory pressure |
| DOM updates | 60/sec | Visual lag, dropped frames |

## Instructions

### Step 1: Throttled File Operations

```typescript
class ThrottledVault {
  private writeQueue: Array<() => Promise<void>> = [];
  private processing = false;
  private writeDelay = 100; // ms between writes

  async write(file: TFile, content: string): Promise<void> {
    return new Promise((resolve, reject) => {
      this.writeQueue.push(async () => {
        try {
          await this.app.vault.modify(file, content);
          resolve();
        } catch (e) { reject(e); }
      });
      this.processQueue();
    });
  }

  private async processQueue() {
    if (this.processing) return;
    this.processing = true;
    while (this.writeQueue.length > 0) {
      const task = this.writeQueue.shift()!;
      await task();
      await new Promise(r => setTimeout(r, this.writeDelay));
    }
    this.processing = false;
  }
}
```

### Step 2: Batch Read with UI Yielding

```typescript
async function batchRead(
  app: App,
  files: TFile[],
  batchSize: number = 50,
  yieldEvery: number = 10
): Promise<Map<string, string>> {
  const results = new Map<string, string>();
  for (let i = 0; i < files.length; i++) {
    results.set(files[i].path, await app.vault.read(files[i]));
    // Yield to UI thread periodically
    if (i % yieldEvery === 0) {
      await new Promise(r => setTimeout(r, 0));
    }
  }
  return results;
}
```

### Step 3: Debounced Event Handlers

```typescript
export default class MyPlugin extends Plugin {
  private saveDebounce: NodeJS.Timeout | null = null;

  async onload() {
    this.registerEvent(
      this.app.vault.on('modify', (file) => {
        // Debounce: only process after 500ms of no changes
        if (this.saveDebounce) clearTimeout(this.saveDebounce);
        this.saveDebounce = setTimeout(() => {
          this.handleFileChange(file as TFile);
        }, 500);
      })
    );
  }
}
```

### Step 4: Progress Feedback for Long Operations

```typescript
async function processAllFiles(app: App, files: TFile[]) {
  const notice = new Notice('Processing files... 0%', 0);
  const total = files.length;
  let processed = 0;

  for (let i = 0; i < total; i += 20) {
    const batch = files.slice(i, i + 20);
    await Promise.all(batch.map(f => processFile(f)));
    processed += batch.length;
    notice.setMessage(`Processing files... ${Math.round(processed / total * 100)}%`);
    await new Promise(r => setTimeout(r, 50)); // yield to UI
  }
  notice.hide();
  new Notice(`Processed ${total} files`);
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| UI freezes | Too many sync operations | Batch with UI yielding |
| Data corruption | Concurrent writes to same file | Queue writes, serialize per file |
| Memory pressure | Reading all files at once | Process in batches |
| Missed events | Over-debouncing | Set reasonable debounce (300-500ms) |

## Examples

### File Operation Monitor
```typescript
let readCount = 0, writeCount = 0;
setInterval(() => {
  if (readCount > 50 || writeCount > 5) {
    console.warn(`High I/O: ${readCount} reads, ${writeCount} writes in last second`);
  }
  readCount = 0; writeCount = 0;
}, 1000);
```

## Resources
- [Obsidian Performance Tips](https://docs.obsidian.md/Plugins/Guides/Performance)
