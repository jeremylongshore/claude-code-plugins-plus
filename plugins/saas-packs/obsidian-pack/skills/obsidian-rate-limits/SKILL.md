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
Obsidian has no traditional API rate limits, but it runs on Electron with a single-threaded UI. This skill covers debouncing, batching, throttling, and async queue patterns to keep plugins responsive and prevent UI freezes.

## Prerequisites
- Understanding of JavaScript event loop and `requestAnimationFrame`
- Familiarity with async/await and Promises
- Working Obsidian plugin with file operations

## Instructions

### Step 1: Debounce vault.on('modify') Events

`vault.on('modify')` fires on every keystroke when a user types in a note. Without debouncing, your handler runs hundreds of times per second.

```typescript
import { Plugin, TFile, debounce } from 'obsidian';

export default class ThrottledPlugin extends Plugin {
  async onload() {
    // Obsidian provides a built-in debounce utility
    const debouncedHandler = debounce(
      (file: TFile) => this.handleFileModified(file),
      500,   // wait 500ms after last keystroke
      true   // run on leading edge too (immediate first call)
    );

    this.registerEvent(
      this.app.vault.on('modify', debouncedHandler)
    );
  }

  private async handleFileModified(file: TFile) {
    // This runs at most once per 500ms per burst of edits
    const cache = this.app.metadataCache.getFileCache(file);
    if (cache?.frontmatter?.tracked) {
      await this.updateIndex(file);
    }
  }
}
```

If you need per-file debouncing (common when multiple files change simultaneously):
```typescript
private fileTimers = new Map<string, NodeJS.Timeout>();

private debouncedPerFile(file: TFile, fn: () => void, delay = 500) {
  const existing = this.fileTimers.get(file.path);
  if (existing) clearTimeout(existing);

  const timer = setTimeout(() => {
    this.fileTimers.delete(file.path);
    fn();
  }, delay);

  // Use activeWindow for Obsidian's timeout tracking
  this.fileTimers.set(file.path, timer);
}
```

### Step 2: Batch File Operations with UI Yielding

Processing hundreds of files synchronously locks the UI. Yield back to the main thread between batches.

```typescript
async processAllFiles(): Promise<void> {
  const files = this.app.vault.getMarkdownFiles();
  const BATCH_SIZE = 50;
  const results: ProcessResult[] = [];

  for (let i = 0; i < files.length; i += BATCH_SIZE) {
    const batch = files.slice(i, i + BATCH_SIZE);

    // Process one batch
    for (const file of batch) {
      const content = await this.app.vault.cachedRead(file);
      results.push(this.processContent(file.path, content));
    }

    // Yield to UI thread between batches
    await sleep(0);

    // Update progress if you have a status bar or notice
    const pct = Math.round(((i + batch.length) / files.length) * 100);
    this.statusBar?.setText(`Processing: ${pct}%`);
  }

  this.statusBar?.setText(`Done: ${results.length} files processed`);
}

// Obsidian exports sleep(), or use this:
function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}
```

### Step 3: Throttle UI Updates

Updating DOM elements on every event causes layout thrashing. Throttle to animation frames.

```typescript
class ThrottledStatusView {
  private pendingUpdate = false;
  private el: HTMLElement;
  private data: { count: number; lastFile: string } = { count: 0, lastFile: '' };

  constructor(el: HTMLElement) {
    this.el = el;
  }

  // Call this as often as you want — it coalesces to one paint per frame
  update(count: number, lastFile: string) {
    this.data = { count, lastFile };
    if (!this.pendingUpdate) {
      this.pendingUpdate = true;
      requestAnimationFrame(() => {
        this.render();
        this.pendingUpdate = false;
      });
    }
  }

  private render() {
    this.el.empty();
    this.el.createEl('span', { text: `${this.data.count} files` });
    this.el.createEl('span', { text: this.data.lastFile, cls: 'nav-file-title' });
  }
}
```

### Step 4: Async Queue for Write Operations

Concurrent writes to the same file corrupt data. Queue writes so only one runs at a time.

```typescript
class WriteQueue {
  private queue: Array<() => Promise<void>> = [];
  private running = false;

  async enqueue(fn: () => Promise<void>): Promise<void> {
    return new Promise((resolve, reject) => {
      this.queue.push(async () => {
        try {
          await fn();
          resolve();
        } catch (e) {
          reject(e);
        }
      });
      this.process();
    });
  }

  private async process() {
    if (this.running) return;
    this.running = true;

    while (this.queue.length > 0) {
      const task = this.queue.shift()!;
      await task();
      // Small delay between writes to avoid overwhelming disk I/O
      await sleep(10);
    }

    this.running = false;
  }
}

// Usage in plugin
class MyPlugin extends Plugin {
  private writeQueue = new WriteQueue();

  async safeWrite(file: TFile, content: string) {
    await this.writeQueue.enqueue(async () => {
      await this.app.vault.modify(file, content);
    });
  }
}
```

### Step 5: Progress Notice for Long Operations

Give users feedback during operations that take more than a second.

```typescript
async bulkUpdateFrontmatter(
  files: TFile[],
  updater: (fm: any) => void
): Promise<{ success: number; failed: string[] }> {
  const failed: string[] = [];
  let success = 0;

  // Use Notice with a timeout of 0 to create a persistent notice
  const notice = new Notice(`Updating 0/${files.length} files...`, 0);

  try {
    for (let i = 0; i < files.length; i++) {
      try {
        await this.app.fileManager.processFrontMatter(files[i], updater);
        success++;
      } catch (e) {
        failed.push(files[i].path);
      }

      // Update notice every 10 files to avoid DOM thrashing
      if (i % 10 === 0 || i === files.length - 1) {
        notice.setMessage(`Updating ${i + 1}/${files.length} files...`);
        await sleep(0); // yield to UI
      }
    }
  } finally {
    // Replace persistent notice with a timed one
    notice.hide();
    new Notice(`Updated ${success} files. ${failed.length} failed.`);
  }

  return { success, failed };
}
```

### Step 6: registerInterval for Periodic Tasks

Use Obsidian's `registerInterval` instead of raw `setInterval` — it auto-clears on plugin unload.

```typescript
async onload() {
  // Sync data every 5 minutes
  this.registerInterval(
    window.setInterval(() => {
      this.syncData();
    }, 5 * 60 * 1000)
  );
}

private async syncData() {
  // Guard against overlapping runs
  if (this.syncing) return;
  this.syncing = true;
  try {
    await this.performSync();
  } finally {
    this.syncing = false;
  }
}
```

## Output
- Debounced event handlers that fire at most once per 500ms
- Batch file processor with UI yielding and progress feedback
- Throttled UI updates using `requestAnimationFrame`
- Serialized write queue preventing concurrent file corruption
- Periodic tasks with `registerInterval` and overlap guards

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| UI freezes during bulk operation | Processing all files synchronously | Batch with `await sleep(0)` between batches |
| Data corruption | Concurrent writes to same file | Use a write queue to serialize operations |
| Memory pressure on large vaults | Loading all file contents at once | Process in batches of 50, release references |
| Missed file changes | Debounce interval too long | Keep debounce under 500ms; use leading edge |
| Timers leak after disable | Using raw setInterval | Always use `this.registerInterval()` |
| Layout thrashing | Updating DOM on every event | Coalesce with `requestAnimationFrame` |

## Examples

### Vault Statistics Collector
```typescript
// Efficient vault scan that doesn't freeze UI
async getVaultStats(): Promise<{ total: number; words: number }> {
  const files = this.app.vault.getMarkdownFiles();
  let words = 0;

  for (let i = 0; i < files.length; i += 50) {
    const batch = files.slice(i, i + 50);
    for (const file of batch) {
      const content = await this.app.vault.cachedRead(file);
      words += content.split(/\s+/).length;
    }
    await sleep(0);
  }

  return { total: files.length, words };
}
```

### Debounced Search Index Rebuild
```typescript
// Rebuild search index at most once per 2 seconds
private rebuildIndex = debounce(async () => {
  const files = this.app.vault.getMarkdownFiles();
  this.index.clear();
  for (const file of files) {
    const cache = this.app.metadataCache.getFileCache(file);
    if (cache?.frontmatter) {
      this.index.set(file.path, cache.frontmatter);
    }
  }
}, 2000, true);
```

## Resources
- [Obsidian Performance Guide](https://docs.obsidian.md/Plugins/Guides/Performance)
- [Obsidian API — debounce](https://docs.obsidian.md/Reference/TypeScript+API/debounce)

## Next Steps
For event handling patterns that complement these throttling strategies, see `obsidian-webhooks-events`. For production deployment readiness, see `obsidian-prod-checklist`.
