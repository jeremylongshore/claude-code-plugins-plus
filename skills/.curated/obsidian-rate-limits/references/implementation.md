# Obsidian Rate Limits -- Implementation Reference

## Overview

Handle Obsidian file system operation throttling to prevent performance degradation
when processing many files, running bulk operations, or syncing large vaults.

## Prerequisites

- Obsidian v1.0+
- TypeScript plugin project setup
- Understanding of Obsidian Vault API

## Throttled File Processor

```typescript
import { App, TFile, Notice } from 'obsidian';

interface ProcessOptions {
    batchSize?: number;
    delayBetweenBatches?: number;  // ms
    onProgress?: (done: number, total: number) => void;
}

export async function processFilesThrottled(
    app: App,
    files: TFile[],
    processor: (file: TFile) => Promise<void>,
    options: ProcessOptions = {}
): Promise<void> {
    const {
        batchSize = 10,
        delayBetweenBatches = 50,
        onProgress,
    } = options;

    let processed = 0;

    for (let i = 0; i < files.length; i += batchSize) {
        const batch = files.slice(i, i + batchSize);

        await Promise.all(batch.map(async (file) => {
            try {
                await processor(file);
                processed++;
                onProgress?.(processed, files.length);
            } catch (err) {
                console.error(`Error processing ${file.path}:`, err);
            }
        }));

        // Yield to the event loop between batches
        if (i + batchSize < files.length) {
            await sleep(delayBetweenBatches);
        }
    }
}

function sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
}
```

## Debounced File Watcher

```typescript
import { App, TFile } from 'obsidian';

export class DebouncedFileWatcher {
    private timers: Map<string, ReturnType<typeof setTimeout>> = new Map();
    private readonly delay: number;

    constructor(
        private app: App,
        private handler: (file: TFile) => Promise<void>,
        delayMs = 300
    ) {
        this.delay = delayMs;
    }

    onFileChange(file: TFile): void {
        const existing = this.timers.get(file.path);
        if (existing) clearTimeout(existing);

        const timer = setTimeout(() => {
            this.timers.delete(file.path);
            this.handler(file).catch(err =>
                console.error(`Handler error for ${file.path}:`, err)
            );
        }, this.delay);

        this.timers.set(file.path, timer);
    }

    destroy(): void {
        for (const timer of this.timers.values()) {
            clearTimeout(timer);
        }
        this.timers.clear();
    }
}

// Usage in plugin
export default class MyPlugin extends Plugin {
    private watcher: DebouncedFileWatcher;

    async onload() {
        this.watcher = new DebouncedFileWatcher(
            this.app,
            async (file) => {
                const content = await this.app.vault.read(file);
                // Process changed file
            },
            500  // Wait 500ms after last change
        );

        this.registerEvent(
            this.app.vault.on('modify', (file) => {
                if (file instanceof TFile && file.extension === 'md') {
                    this.watcher.onFileChange(file);
                }
            })
        );
    }

    onunload() {
        this.watcher.destroy();
    }
}
```

## Bulk Operation Queue

```typescript
type QueueTask<T> = () => Promise<T>;

export class AsyncQueue<T> {
    private queue: QueueTask<T>[] = [];
    private running = 0;

    constructor(private concurrency: number = 3) {}

    async add(task: QueueTask<T>): Promise<T> {
        return new Promise((resolve, reject) => {
            this.queue.push(async () => {
                try {
                    resolve(await task());
                } catch (err) {
                    reject(err);
                } finally {
                    this.running--;
                    this.drain();
                }
            });
            this.drain();
        });
    }

    private drain(): void {
        while (this.running < this.concurrency && this.queue.length > 0) {
            const task = this.queue.shift()!;
            this.running++;
            task();
        }
    }

    get pending(): number {
        return this.queue.length;
    }
}

// Usage: process vault files with limited concurrency
const queue = new AsyncQueue<void>(5);
const files = app.vault.getMarkdownFiles();

const results = await Promise.all(
    files.map(file => queue.add(() => processFile(app, file)))
);
```

## Progress Modal

```typescript
import { App, Modal, ProgressBarComponent } from 'obsidian';

export class ProgressModal extends Modal {
    private progressBar: ProgressBarComponent;
    private statusEl: HTMLElement;

    constructor(app: App, private title: string) {
        super(app);
    }

    onOpen() {
        const { contentEl } = this;
        contentEl.createEl('h2', { text: this.title });
        this.progressBar = new ProgressBarComponent(contentEl);
        this.statusEl = contentEl.createEl('p', { cls: 'progress-status' });
    }

    update(done: number, total: number, message = ''): void {
        this.progressBar.setValue(done / total);
        this.statusEl.setText(message || `${done} / ${total}`);
    }

    onClose() {
        this.contentEl.empty();
    }
}

// Usage
async function bulkRename(app: App, files: TFile[]) {
    const modal = new ProgressModal(app, 'Renaming files...');
    modal.open();

    await processFilesThrottled(
        app,
        files,
        async (file) => { /* rename logic */ },
        {
            batchSize: 5,
            delayBetweenBatches: 100,
            onProgress: (done, total) => modal.update(done, total),
        }
    );

    modal.close();
    new Notice(`Renamed ${files.length} files`);
}
```

## Resources

- [Obsidian Vault API](https://docs.obsidian.md/Plugins/Vault)
- [Obsidian Plugin API Reference](https://github.com/obsidianmd/obsidian-api)
- [TypeScript async patterns](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-0.html)

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
