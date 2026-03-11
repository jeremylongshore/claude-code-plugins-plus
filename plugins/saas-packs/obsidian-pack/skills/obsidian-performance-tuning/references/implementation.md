# Obsidian Performance Tuning - Implementation Details

## Performance Profiler

```typescript
// src/utils/profiler.ts
export class PerformanceProfiler {
  private marks: Map<string, number> = new Map();
  private enabled: boolean;

  constructor(enabled: boolean = true) { this.enabled = enabled; }

  start(label: string): void {
    if (!this.enabled) return;
    this.marks.set(label, performance.now());
  }

  end(label: string): number {
    if (!this.enabled) return 0;
    const start = this.marks.get(label);
    if (!start) return 0;
    const duration = performance.now() - start;
    this.marks.delete(label);
    if (duration > 50) console.warn(`[Performance] ${label}: ${duration.toFixed(2)}ms (slow)`);
    return duration;
  }

  async measure<T>(label: string, fn: () => Promise<T>): Promise<T> {
    this.start(label);
    try { return await fn(); } finally { this.end(label); }
  }
}
```

## Lazy Initialization

```typescript
export class LazyService<T> {
  private instance: T | null = null;
  private initializing: Promise<T> | null = null;

  constructor(private factory: () => Promise<T>) {}

  async get(): Promise<T> {
    if (this.instance) return this.instance;
    if (this.initializing) return this.initializing;
    this.initializing = this.factory().then(i => { this.instance = i; this.initializing = null; return i; });
    return this.initializing;
  }
}

// Usage - defer expensive initialization
export default class MyPlugin extends Plugin {
  private indexService = new LazyService(() => this.buildIndex());

  async onload() {
    this.addCommand({
      id: 'search', name: 'Search',
      callback: async () => {
        const index = await this.indexService.get(); // Only builds on first use
      },
    });
  }
}
```

## Efficient File Processing

```typescript
export class EfficientFileProcessor {
  private vault: Vault;
  private cache: Map<string, { content: string; mtime: number }> = new Map();

  async readWithCache(file: TFile): Promise<string> {
    const cached = this.cache.get(file.path);
    if (cached && cached.mtime === file.stat.mtime) return cached.content;
    const content = await this.vault.cachedRead(file);
    this.cache.set(file.path, { content, mtime: file.stat.mtime });
    return content;
  }

  async processFilesInChunks<T>(
    files: TFile[], processor: (file: TFile) => Promise<T>,
    options: { chunkSize?: number; pauseMs?: number; onProgress?: (p: number, t: number) => void } = {}
  ): Promise<T[]> {
    const { chunkSize = 50, pauseMs = 10, onProgress } = options;
    const results: T[] = [];
    for (let i = 0; i < files.length; i += chunkSize) {
      const chunk = files.slice(i, i + chunkSize);
      const chunkResults = await Promise.all(chunk.map(file => processor(file)));
      results.push(...chunkResults);
      onProgress?.(Math.min(i + chunkSize, files.length), files.length);
      if (i + chunkSize < files.length) await new Promise(r => setTimeout(r, pauseMs));
    }
    return results;
  }
}
```

## Memory-Efficient Data Structures

### LRU Cache
```typescript
export class LRUCache<K, V> {
  private cache = new Map<K, V>();
  constructor(private maxSize: number) {}

  get(key: K): V | undefined {
    const value = this.cache.get(key);
    if (value !== undefined) {
      this.cache.delete(key);
      this.cache.set(key, value); // Move to end
    }
    return value;
  }

  set(key: K, value: V): void {
    if (this.cache.has(key)) this.cache.delete(key);
    else if (this.cache.size >= this.maxSize) {
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }
    this.cache.set(key, value);
  }
}
```

### WeakMap File Cache
```typescript
export class WeakFileCache<T> {
  private cache = new WeakMap<object, T>();
  set(file: object, value: T): void { this.cache.set(file, value); }
  get(file: object): T | undefined { return this.cache.get(file); }
}
```

## Event Handler Optimization

```typescript
import { debounce, throttle } from 'lodash-es';

export class OptimizedEventManager {
  registerDebouncedModify(handler: (file: TFile) => void, wait = 500): void {
    const debouncedHandler = debounce(handler, wait);
    this.plugin.registerEvent(
      this.plugin.app.vault.on('modify', (file) => {
        if (file instanceof TFile) debouncedHandler(file);
      })
    );
  }

  registerBatchedEvents(handler: (files: TFile[]) => void, wait = 100): void {
    let pendingFiles: TFile[] = [];
    let timeoutId: NodeJS.Timeout | null = null;
    this.plugin.registerEvent(
      this.plugin.app.vault.on('modify', (file) => {
        if (file instanceof TFile) {
          pendingFiles.push(file);
          if (timeoutId) clearTimeout(timeoutId);
          timeoutId = setTimeout(() => {
            handler([...new Set(pendingFiles)]);
            pendingFiles = [];
            timeoutId = null;
          }, wait);
        }
      })
    );
  }
}
```

## UI Rendering Optimization

```typescript
export class RenderOptimizer {
  static batchRender(container: HTMLElement, items: string[], renderer: (item: string) => HTMLElement): void {
    const fragment = document.createDocumentFragment();
    for (const item of items) fragment.appendChild(renderer(item));
    container.empty();
    container.appendChild(fragment);
  }

  static createVirtualList(container: HTMLElement, items: any[], itemHeight: number, renderItem: (item: any) => HTMLElement): void {
    const visibleCount = Math.ceil(container.clientHeight / itemHeight) + 2;
    let startIndex = 0;
    const render = () => {
      const newStartIndex = Math.floor(container.scrollTop / itemHeight);
      if (newStartIndex !== startIndex) {
        startIndex = newStartIndex;
        // Render only visible items with spacers
      }
    };
    container.addEventListener('scroll', render);
    render();
  }
}
```

## Memory Usage Monitor
```typescript
function logMemoryUsage(label: string): void {
  if (performance.memory) {
    const used = performance.memory.usedJSHeapSize / 1048576;
    console.log(`[Memory] ${label}: ${used.toFixed(2)} MB`);
  }
}
```
