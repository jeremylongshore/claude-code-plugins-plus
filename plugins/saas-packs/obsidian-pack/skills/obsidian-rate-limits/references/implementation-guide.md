# Obsidian Rate Limits - Implementation Guide

> Full implementation details for the parent SKILL.md.

## Detailed Instructions

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


## Complete Examples

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


## Obsidian Operation Limits

| Operation | Safe Limit | Risk if Exceeded |
|-----------|-----------|------------------|
| File reads | 100/sec | UI freeze |
| File writes | 10/sec | Sync conflicts, data corruption |
| Metadata cache reads | 500/sec | Memory pressure |
| DOM updates | 60/sec | Visual lag, dropped frames |
