---
name: obsidian-performance-tuning
description: |
  Optimize Obsidian plugin performance for smooth operation in large vaults.
  Use when experiencing lag, memory issues, slow startup, or optimizing
  plugin code for vaults with thousands of files.
  Trigger with phrases like "obsidian performance", "obsidian slow",
  "optimize obsidian plugin", "obsidian memory usage", "obsidian lag".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [obsidian, performance, optimization, memory, profiling]

---
# Obsidian Performance Tuning

## Overview
Optimize Obsidian plugin performance for large vaults (10,000+ files): profile bottlenecks with DevTools, implement lazy initialization, process files in batches with UI yielding, use LRU caches with bounded memory, debounce event handlers, and optimize DOM rendering with virtual scrolling and DocumentFragment.

## Prerequisites
- Working Obsidian plugin with at least one performance concern
- Developer Console access (Ctrl+Shift+I / Cmd+Option+I)
- Understanding of async JavaScript and the event loop

## Performance Benchmarks

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Plugin load time (`onload`) | < 100ms | 100-500ms | > 500ms |
| Command execution | < 50ms | 50-200ms | > 200ms |
| Single file operation | < 10ms | 10-50ms | > 50ms |
| Memory increase on load | < 10MB | 10-50MB | > 50MB |
| Event handler execution | < 5ms | 5-20ms | > 20ms |

## Instructions

### Step 1: Profile with DevTools Performance Tab
```typescript
// Add timing instrumentation to identify bottlenecks
export default class MyPlugin extends Plugin {
  async onload() {
    const loadStart = performance.now();

    await this.loadSettings();
    console.log(`[perf] loadSettings: ${(performance.now() - loadStart).toFixed(1)}ms`);

    const indexStart = performance.now();
    await this.buildIndex();
    console.log(`[perf] buildIndex: ${(performance.now() - indexStart).toFixed(1)}ms`);

    const cmdStart = performance.now();
    this.registerCommands();
    console.log(`[perf] registerCommands: ${(performance.now() - cmdStart).toFixed(1)}ms`);

    console.log(`[perf] total onload: ${(performance.now() - loadStart).toFixed(1)}ms`);
  }
}
```

For deeper analysis, use the DevTools Performance tab:
1. Open DevTools (Ctrl+Shift+I)
2. Go to Performance tab
3. Click Record
4. Toggle your plugin off/on in Settings > Community Plugins
5. Stop recording
6. Look for long tasks (yellow bars > 50ms) in the flame chart

### Step 2: Lazy Initialization — Defer Expensive Work
```typescript
// BAD: build index on load (blocks startup)
async onload() {
  this.index = await this.buildFullIndex(); // 2 seconds on large vaults
}

// GOOD: lazy — build on first use
export default class MyPlugin extends Plugin {
  private _index: Map<string, string[]> | null = null;
  private indexPromise: Promise<Map<string, string[]>> | null = null;

  async getIndex(): Promise<Map<string, string[]>> {
    if (this._index) return this._index;
    if (!this.indexPromise) {
      this.indexPromise = this.buildFullIndex().then(idx => {
        this._index = idx;
        this.indexPromise = null;
        return idx;
      });
    }
    return this.indexPromise;
  }

  async onload() {
    // Register commands immediately — index builds on first command use
    this.addCommand({
      id: 'search',
      name: 'Search indexed notes',
      callback: async () => {
        const index = await this.getIndex(); // builds on first call only
        // ... use index
      },
    });
  }

  private async buildFullIndex(): Promise<Map<string, string[]>> {
    const index = new Map<string, string[]>();
    const files = this.app.vault.getMarkdownFiles();
    for (const file of files) {
      const cache = this.app.metadataCache.getFileCache(file);
      if (cache?.tags) {
        index.set(file.path, cache.tags.map(t => t.tag));
      }
    }
    return index;
  }
}
```

### Step 3: Batch File Processing with UI Yielding
```typescript
import { TFile, Notice } from 'obsidian';

async processAllFiles(statusEl?: HTMLElement): Promise<number> {
  const files = this.app.vault.getMarkdownFiles();
  const BATCH_SIZE = 50;
  let processed = 0;

  for (let i = 0; i < files.length; i += BATCH_SIZE) {
    const batch = files.slice(i, i + BATCH_SIZE);

    for (const file of batch) {
      // Use cachedRead — avoids hitting disk on every call
      const content = await this.app.vault.cachedRead(file);
      this.processContent(file, content);
      processed++;
    }

    // Yield to UI thread — prevents "not responding" dialog
    await sleep(0);

    // Update progress
    if (statusEl) {
      const pct = Math.round((processed / files.length) * 100);
      statusEl.setText(`Processing: ${pct}% (${processed}/${files.length})`);
    }
  }

  return processed;
}

// Helper: Obsidian exports sleep(), or use this
function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}
```

### Step 4: LRU Cache for Bounded Memory
```typescript
// src/services/lru-cache.ts
export class LRUCache<K, V> {
  private cache = new Map<K, V>();

  constructor(private maxSize: number) {}

  get(key: K): V | undefined {
    const value = this.cache.get(key);
    if (value !== undefined) {
      // Move to end (most recently used)
      this.cache.delete(key);
      this.cache.set(key, value);
    }
    return value;
  }

  set(key: K, value: V) {
    this.cache.delete(key); // remove if exists (reinserts at end)
    this.cache.set(key, value);
    if (this.cache.size > this.maxSize) {
      // Evict oldest (first) entry
      const oldest = this.cache.keys().next().value;
      if (oldest !== undefined) this.cache.delete(oldest);
    }
  }

  has(key: K): boolean { return this.cache.has(key); }
  delete(key: K): boolean { return this.cache.delete(key); }
  clear() { this.cache.clear(); }
  get size(): number { return this.cache.size; }
}

// Usage: cache processed file results by mtime
class FileProcessor {
  private cache = new LRUCache<string, { mtime: number; result: string }>(500);

  async process(file: TFile): Promise<string> {
    const cached = this.cache.get(file.path);
    if (cached && cached.mtime === file.stat.mtime) {
      return cached.result; // cache hit — skip expensive processing
    }

    const content = await this.app.vault.cachedRead(file);
    const result = this.expensiveTransform(content);
    this.cache.set(file.path, { mtime: file.stat.mtime, result });
    return result;
  }
}
```

### Step 5: Debounce and Throttle Event Handlers
```typescript
import { Plugin, TFile, debounce } from 'obsidian';

export default class MyPlugin extends Plugin {
  // Global debounce: runs 500ms after last modify event
  private handleModify = debounce(
    (file: TFile) => {
      const cache = this.app.metadataCache.getFileCache(file);
      if (cache?.frontmatter?.tracked) {
        this.reindexFile(file);
      }
    },
    500,
    true // trailing edge
  );

  // Per-file debounce: separate timer for each file
  private fileTimers = new Map<string, ReturnType<typeof setTimeout>>();

  private debouncedPerFile(file: TFile, fn: () => void, delay = 1000) {
    const existing = this.fileTimers.get(file.path);
    if (existing) clearTimeout(existing);
    this.fileTimers.set(file.path, setTimeout(() => {
      this.fileTimers.delete(file.path);
      fn();
    }, delay));
  }

  async onload() {
    this.registerEvent(
      this.app.vault.on('modify', (file) => {
        if (file instanceof TFile && file.extension === 'md') {
          this.handleModify(file);
        }
      })
    );
  }

  onunload() {
    for (const timer of this.fileTimers.values()) clearTimeout(timer);
    this.fileTimers.clear();
  }
}
```

### Step 6: Optimize DOM Rendering
```typescript
// BAD: updating DOM on every event
this.registerEvent(this.app.vault.on('modify', () => {
  this.containerEl.empty();
  this.renderFullList(); // re-renders 1000 items on every keystroke
}));

// GOOD: DocumentFragment for batch DOM updates
private renderFileList(container: HTMLElement, files: TFile[]) {
  const fragment = document.createDocumentFragment();
  for (const file of files) {
    const el = document.createElement('div');
    el.className = 'file-item';
    el.textContent = file.basename;
    el.addEventListener('click', () => {
      this.app.workspace.getLeaf().openFile(file);
    });
    fragment.appendChild(el);
  }
  container.empty();
  container.appendChild(fragment);
}

// GOOD: requestAnimationFrame for coalesced updates
private pendingRender = false;

private scheduleRender() {
  if (!this.pendingRender) {
    this.pendingRender = true;
    requestAnimationFrame(() => {
      this.render();
      this.pendingRender = false;
    });
  }
}

// GOOD: Virtual scrolling for long lists
private renderVirtualList(container: HTMLElement, items: string[], itemHeight = 24) {
  const visibleCount = Math.ceil(container.clientHeight / itemHeight);
  let scrollTop = 0;

  const content = container.createEl('div', {
    attr: { style: `height: ${items.length * itemHeight}px; position: relative;` },
  });

  const renderVisible = () => {
    const start = Math.floor(scrollTop / itemHeight);
    const end = Math.min(start + visibleCount + 5, items.length);

    content.empty();
    for (let i = start; i < end; i++) {
      content.createEl('div', {
        text: items[i],
        attr: { style: `position: absolute; top: ${i * itemHeight}px; height: ${itemHeight}px;` },
      });
    }
  };

  container.addEventListener('scroll', () => {
    scrollTop = container.scrollTop;
    requestAnimationFrame(renderVisible);
  });

  renderVisible();
}
```

### Step 7: Memory Leak Prevention
```typescript
// Common leak: WeakRef/WeakMap for file references
// Files can be deleted — holding TFile references prevents GC
private fileData = new WeakMap<TFile, ProcessedData>();

// Common leak: unregistered event listeners
// BAD:
document.addEventListener('click', this.handler); // leaks on unload

// GOOD:
this.registerDomEvent(document, 'click', this.handler); // auto-cleaned

// Common leak: uncleaned intervals
// BAD:
setInterval(() => this.sync(), 60000); // runs forever after unload

// GOOD:
this.registerInterval(window.setInterval(() => this.sync(), 60000)); // auto-cleaned

// Audit: check memory in DevTools
// Console > Performance.memory.usedJSHeapSize
// Enable/disable your plugin, check if memory drops back to baseline
```

## Output
- Performance profiler identifying specific bottlenecks in `onload` and commands
- Lazy initialization deferring index builds until first use
- Batch file processing with `await sleep(0)` yielding to prevent UI freezes
- LRU cache with bounded memory (500 entries) and mtime-based invalidation
- Debounced event handlers (global and per-file) for `vault.on('modify')`
- DOM optimization with DocumentFragment, requestAnimationFrame, and virtual scrolling
- Memory leak prevention checklist with WeakMap, registerEvent, registerInterval

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Plugin slow to load | Heavy initialization in `onload` | Use lazy loading pattern (Step 2) |
| UI freezes during processing | Synchronous loop over all files | Batch with `await sleep(0)` (Step 3) |
| Memory keeps growing | Unbounded caches or leaked references | Use LRU cache (Step 4), WeakMap for file refs |
| Event handlers lag | Unthrottled `modify` handler | Debounce at 500ms minimum (Step 5) |
| Layout thrashing | DOM updates on every event | Coalesce with `requestAnimationFrame` (Step 6) |
| `cachedRead` returns stale data | Cache not yet updated | Use `vault.read()` when freshness is critical |
| Plugin doesn't release memory on disable | Missing cleanup | Use `registerEvent`/`registerInterval` exclusively |

## Examples

### Pre-Release Performance Checklist
- [ ] `onload` completes in < 100ms (check console timing)
- [ ] No synchronous loops over all vault files in `onload`
- [ ] File operations use `cachedRead` (not `read`) where possible
- [ ] All event handlers debounced or throttled
- [ ] Caches have explicit size limits (LRU or max-age)
- [ ] Works smoothly in vault with 5,000+ files
- [ ] Memory returns to baseline after disabling plugin
- [ ] No raw `addEventListener` / `setInterval` (use `register*` methods)

### Quick Memory Check
```javascript
// Paste in Obsidian DevTools Console
// Check before and after enabling your plugin
console.log('Heap:', Math.round(performance.memory.usedJSHeapSize / 1048576), 'MB');
```

## Resources
- [Obsidian Performance Guide](https://docs.obsidian.md/Plugins/Guides/Performance)
- [Chrome DevTools Performance](https://developer.chrome.com/docs/devtools/performance/)
- [Obsidian API — debounce](https://docs.obsidian.md/Reference/TypeScript+API/debounce)
- [requestAnimationFrame](https://developer.mozilla.org/en-US/docs/Web/API/window/requestAnimationFrame)

## Next Steps
For resource cost optimization, see `obsidian-cost-tuning`.
For rate limiting and throttling patterns, see `obsidian-rate-limits`.
