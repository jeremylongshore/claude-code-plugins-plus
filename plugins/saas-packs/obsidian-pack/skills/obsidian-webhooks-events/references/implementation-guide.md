# Obsidian Webhooks & Events - Implementation Guide

> Full implementation details for the parent SKILL.md.

## Detailed Instructions

### Step 1: Workspace Events
```typescript
import { Plugin, TFile, WorkspaceLeaf } from 'obsidian';

export default class MyPlugin extends Plugin {
  async onload() {
    // File opened in editor
    this.registerEvent(
      this.app.workspace.on('file-open', (file: TFile | null) => {
        if (file) {
          console.log('Opened file:', file.path);
          this.onFileOpen(file);
        }
      })
    );

    // Active leaf (pane) changed
    this.registerEvent(
      this.app.workspace.on('active-leaf-change', (leaf: WorkspaceLeaf | null) => {
        if (leaf) {
          console.log('Active leaf changed:', leaf.view.getViewType());
        }
      })
    );

    // Layout changed (panes rearranged)
    this.registerEvent(
      this.app.workspace.on('layout-change', () => {
        console.log('Layout changed');
        this.onLayoutChange();
      })
    );

    // Editor mode changed (source/preview)
    this.registerEvent(
      this.app.workspace.on('layout-change', () => {
        const view = this.app.workspace.getActiveViewOfType(MarkdownView);
        if (view) {
          const mode = view.getMode(); // 'source' or 'preview'
          console.log('Editor mode:', mode);
        }
      })
    );

    // Window focus
    this.registerEvent(
      this.app.workspace.on('window-open', (win, window) => {
        console.log('New window opened');
      })
    );
  }

  private onFileOpen(file: TFile) {
    // React to file opening
  }

  private onLayoutChange() {
    // React to layout changes
  }
}
```

### Step 2: Vault Events
```typescript
import { Plugin, TFile, TFolder, TAbstractFile } from 'obsidian';

export default class MyPlugin extends Plugin {
  async onload() {
    // File created
    this.registerEvent(
      this.app.vault.on('create', (file: TAbstractFile) => {
        if (file instanceof TFile) {
          console.log('File created:', file.path);
          this.onFileCreated(file);
        } else if (file instanceof TFolder) {
          console.log('Folder created:', file.path);
        }
      })
    );

    // File modified
    this.registerEvent(
      this.app.vault.on('modify', (file: TAbstractFile) => {
        if (file instanceof TFile) {
          console.log('File modified:', file.path);
          this.onFileModified(file);
        }
      })
    );

    // File deleted
    this.registerEvent(
      this.app.vault.on('delete', (file: TAbstractFile) => {
        console.log('File deleted:', file.path);
        this.onFileDeleted(file);
      })
    );

    // File renamed/moved
    this.registerEvent(
      this.app.vault.on('rename', (file: TAbstractFile, oldPath: string) => {
        console.log(`File renamed: ${oldPath} -> ${file.path}`);
        this.onFileRenamed(file, oldPath);
      })
    );
  }

  private onFileCreated(file: TFile) {
    // Apply template, add frontmatter, etc.
  }

  private onFileModified(file: TFile) {
    // Update indexes, trigger sync, etc.
  }

  private onFileDeleted(file: TAbstractFile) {
    // Clean up references, update cache, etc.
  }

  private onFileRenamed(file: TAbstractFile, oldPath: string) {
    // Update links, references, etc.
  }
}
```

### Step 3: MetadataCache Events
```typescript
import { Plugin, TFile, CachedMetadata } from 'obsidian';

export default class MyPlugin extends Plugin {
  async onload() {
    // Metadata changed for a file
    this.registerEvent(
      this.app.metadataCache.on('changed', (file: TFile, data: string, cache: CachedMetadata) => {
        console.log('Metadata changed:', file.path);

        // Access frontmatter
        if (cache.frontmatter) {
          console.log('Frontmatter:', cache.frontmatter);
        }

        // Access tags
        if (cache.tags) {
          const tags = cache.tags.map(t => t.tag);
          console.log('Tags:', tags);
        }

        // Access links
        if (cache.links) {
          const links = cache.links.map(l => l.link);
          console.log('Links:', links);
        }
      })
    );

    // All files resolved (vault fully loaded)
    this.registerEvent(
      this.app.metadataCache.on('resolved', () => {
        console.log('All files resolved - vault fully loaded');
        this.onVaultReady();
      })
    );
  }

  private onVaultReady() {
    // Safe to do full vault operations
    const allFiles = this.app.vault.getMarkdownFiles();
    console.log(`Vault ready with ${allFiles.length} files`);
  }
}
```

### Step 4: Debounced Event Handling
```typescript
// src/utils/debounced-events.ts
import { Plugin, TFile } from 'obsidian';

export class DebouncedEventHandler {
  private modifyTimeout: Map<string, NodeJS.Timeout> = new Map();
  private debounceMs: number;
  private handler: (file: TFile) => void;

  constructor(debounceMs: number, handler: (file: TFile) => void) {
    this.debounceMs = debounceMs;
    this.handler = handler;
  }

  handleModify(file: TFile) {
    // Clear existing timeout for this file
    const existing = this.modifyTimeout.get(file.path);
    if (existing) {
      clearTimeout(existing);
    }

    // Set new debounced timeout
    const timeout = setTimeout(() => {
      this.modifyTimeout.delete(file.path);
      this.handler(file);
    }, this.debounceMs);

    this.modifyTimeout.set(file.path, timeout);
  }

  cleanup() {
    // Clear all pending timeouts
    for (const timeout of this.modifyTimeout.values()) {
      clearTimeout(timeout);
    }
    this.modifyTimeout.clear();
  }
}

// Usage in plugin:
export default class MyPlugin extends Plugin {
  private debouncedHandler: DebouncedEventHandler;

  async onload() {
    this.debouncedHandler = new DebouncedEventHandler(
      1000, // 1 second debounce
      (file) => this.processFileChange(file)
    );

    this.registerEvent(
      this.app.vault.on('modify', (file) => {
        if (file instanceof TFile) {
          this.debouncedHandler.handleModify(file);
        }
      })
    );
  }

  onunload() {
    this.debouncedHandler.cleanup();
  }

  private processFileChange(file: TFile) {
    // Handle the debounced file change
    console.log('Processing change for:', file.path);
  }
}
```

### Step 5: Custom Event Emitter
```typescript
// src/events/event-bus.ts
import { Events } from 'obsidian';

// Define custom events
interface MyPluginEvents {
  'index-updated': (count: number) => void;
  'sync-complete': (success: boolean, error?: string) => void;
  'settings-changed': (key: string, value: any) => void;
}

export class PluginEventBus extends Events {
  on<K extends keyof MyPluginEvents>(
    event: K,
    callback: MyPluginEvents[K],
    ctx?: any
  ): EventRef {
    return super.on(event as string, callback, ctx);
  }

  off<K extends keyof MyPluginEvents>(
    event: K,
    callback: MyPluginEvents[K]
  ): void {
    super.off(event as string, callback);
  }

  trigger<K extends keyof MyPluginEvents>(
    event: K,
    ...args: Parameters<MyPluginEvents[K]>
  ): void {
    super.trigger(event as string, ...args);
  }
}

// Usage:
const eventBus = new PluginEventBus();

// Subscribe
eventBus.on('index-updated', (count) => {
  console.log(`Index updated with ${count} items`);
});

// Emit
eventBus.trigger('index-updated', 42);
```

### Step 6: File Watcher Pattern
```typescript
// src/watchers/file-watcher.ts
import { Plugin, TFile } from 'obsidian';

interface WatchConfig {
  folder?: string;
  extension?: string;
  includePattern?: RegExp;
  excludePattern?: RegExp;
}

export class FileWatcher {
  private plugin: Plugin;
  private config: WatchConfig;
  private callbacks: {
    onCreate?: (file: TFile) => void;
    onModify?: (file: TFile) => void;
    onDelete?: (path: string) => void;
    onRename?: (file: TFile, oldPath: string) => void;
  };

  constructor(
    plugin: Plugin,
    config: WatchConfig,
    callbacks: typeof FileWatcher.prototype.callbacks
  ) {
    this.plugin = plugin;
    this.config = config;
    this.callbacks = callbacks;
    this.register();
  }

  private shouldWatch(path: string): boolean {
    if (this.config.folder && !path.startsWith(this.config.folder)) {
      return false;
    }
    if (this.config.extension && !path.endsWith(this.config.extension)) {
      return false;
    }
    if (this.config.includePattern && !this.config.includePattern.test(path)) {
      return false;
    }
    if (this.config.excludePattern && this.config.excludePattern.test(path)) {
      return false;
    }
    return true;
  }

  private register() {
    if (this.callbacks.onCreate) {
      this.plugin.registerEvent(
        this.plugin.app.vault.on('create', (file) => {
          if (file instanceof TFile && this.shouldWatch(file.path)) {
            this.callbacks.onCreate!(file);
          }
        })
      );
    }

    if (this.callbacks.onModify) {
      this.plugin.registerEvent(
        this.plugin.app.vault.on('modify', (file) => {
          if (file instanceof TFile && this.shouldWatch(file.path)) {
            this.callbacks.onModify!(file);
          }
        })
      );
    }

    if (this.callbacks.onDelete) {
      this.plugin.registerEvent(
        this.plugin.app.vault.on('delete', (file) => {
          if (this.shouldWatch(file.path)) {
            this.callbacks.onDelete!(file.path);
          }
        })
      );
    }

    if (this.callbacks.onRename) {
      this.plugin.registerEvent(
        this.plugin.app.vault.on('rename', (file, oldPath) => {
          if (file instanceof TFile && (this.shouldWatch(file.path) || this.shouldWatch(oldPath))) {
            this.callbacks.onRename!(file, oldPath);
          }
        })
      );
    }
  }
}

// Usage:
new FileWatcher(
  this,
  {
    folder: 'journal/',
    extension: '.md',
    excludePattern: /template/i,
  },
  {
    onCreate: (file) => console.log('Journal created:', file.path),
    onModify: (file) => console.log('Journal modified:', file.path),
  }
);
```


## Complete Examples

### Complete Event-Driven Plugin
```typescript
export default class MyPlugin extends Plugin {
  async onload() {
    // Wait for vault to be ready
    this.app.workspace.onLayoutReady(() => {
      this.initializeAfterVaultReady();
    });
  }

  private initializeAfterVaultReady() {
    // Now safe to access all files
    this.buildInitialIndex();
    this.registerAllEvents();
  }

  private registerAllEvents() {
    // File events
    this.registerEvent(
      this.app.vault.on('modify', this.handleModify.bind(this))
    );

    // Workspace events
    this.registerEvent(
      this.app.workspace.on('file-open', this.handleFileOpen.bind(this))
    );
  }

  private handleModify(file: TAbstractFile) {
    if (file instanceof TFile) {
      // Update index
    }
  }

  private handleFileOpen(file: TFile | null) {
    if (file) {
      // Track recently opened
    }
  }
}
```


## Event Categories

### Available Events
| Category | Events | Use Case |
|----------|--------|----------|
| Workspace | file-open, active-leaf-change, layout-change | UI state changes |
| Vault | create, modify, delete, rename | File system changes |
| MetadataCache | changed, resolved | Metadata/link updates |
| Editor | change, cursor-activity | Text editing |
