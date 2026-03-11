---
name: obsidian-sdk-patterns
description: |
  Apply production-ready Obsidian plugin patterns for TypeScript.
  Use when implementing complex features, refactoring plugins,
  or establishing coding standards for Obsidian development.
  Trigger with phrases like "obsidian patterns", "obsidian best practices",
  "obsidian code patterns", "idiomatic obsidian plugin".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Obsidian SDK Patterns

## Overview
Production patterns for Obsidian plugin development using the Obsidian TypeScript API. Covers vault operations, workspace management, event handling, and UI components with proper lifecycle management.

## Prerequisites
- Obsidian development environment set up
- TypeScript compilation configured
- Understanding of Obsidian's plugin lifecycle

## Instructions

### Step 1: Type-Safe Settings with Migration

```typescript
interface PluginSettings {
  version: number;
  theme: 'default' | 'minimal' | 'custom';
  syncInterval: number;
  excludedFolders: string[];
}

const DEFAULT_SETTINGS: PluginSettings = {
  version: 2,
  theme: 'default',
  syncInterval: 300,
  excludedFolders: []
};

async function loadAndMigrateSettings(plugin: Plugin): Promise<PluginSettings> {
  const raw = await plugin.loadData();
  if (!raw) return { ...DEFAULT_SETTINGS };

  // Migrate from v1 to v2
  if (!raw.version || raw.version < 2) {
    raw.version = 2;
    raw.excludedFolders = raw.excludedFolders || [];
    await plugin.saveData(raw);
  }
  return { ...DEFAULT_SETTINGS, ...raw };
}
```

### Step 2: Safe Vault Operations

```typescript
class VaultHelper {
  constructor(private app: App) {}

  async safeRead(path: string): Promise<string | null> {
    const file = this.app.vault.getAbstractFileByPath(path);
    if (file instanceof TFile) {
      return await this.app.vault.read(file);
    }
    return null;
  }

  async safeWrite(path: string, content: string): Promise<void> {
    const existing = this.app.vault.getAbstractFileByPath(path);
    if (existing instanceof TFile) {
      await this.app.vault.modify(existing, content);
    } else {
      await this.app.vault.create(path, content);
    }
  }

  async ensureFolder(path: string): Promise<void> {
    const existing = this.app.vault.getAbstractFileByPath(path);
    if (!existing) {
      await this.app.vault.createFolder(path);
    }
  }
}
```

### Step 3: Event Registration with Cleanup

```typescript
export default class MyPlugin extends Plugin {
  async onload() {
    // All events auto-cleanup on plugin unload
    this.registerEvent(
      this.app.vault.on('modify', (file) => {
        if (file instanceof TFile && file.extension === 'md') {
          this.handleFileChange(file);
        }
      })
    );

    this.registerEvent(
      this.app.workspace.on('active-leaf-change', (leaf) => {
        if (leaf?.view instanceof MarkdownView) {
          this.onActiveFileChanged(leaf.view.file);
        }
      })
    );

    // Register interval (also auto-cleanup)
    this.registerInterval(
      window.setInterval(() => this.periodicSync(), 60000)
    );
  }
}
```

### Step 4: Custom View with State Persistence

```typescript
import { ItemView, WorkspaceLeaf } from 'obsidian';

const VIEW_TYPE = 'my-custom-view';

class MyCustomView extends ItemView {
  private state: { filter: string; sort: string } = { filter: '', sort: 'name' };

  getViewType() { return VIEW_TYPE; }
  getDisplayText() { return 'My View'; }

  async onOpen() {
    const container = this.containerEl.children[1];
    container.empty();
    container.createEl('h4', { text: 'My Custom View' });
    this.renderContent(container);
  }

  getState() { return this.state; }

  async setState(state: any, result: any) {
    this.state = { ...this.state, ...state };
    this.renderContent(this.containerEl.children[1]);
    return super.setState(state, result);
  }

  private renderContent(container: Element) {
    // Render based on this.state
  }
}
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `null` file reference | File deleted between check and use | Always re-check with `getAbstractFileByPath` |
| Stale metadata cache | Cache not updated | Use `this.app.metadataCache.on('changed')` |
| Settings lost on update | Missing migration logic | Version settings, migrate on load |
| Memory leak | Unregistered events | Use `this.registerEvent()` always |

## Examples

### Frontmatter Parsing
```typescript
function getFrontmatter(app: App, file: TFile): any {
  const cache = app.metadataCache.getFileCache(file);
  return cache?.frontmatter || {};
}
```

## Resources
- [Obsidian Plugin API](https://docs.obsidian.md/Reference/TypeScript+API)
- [Obsidian Plugin Guidelines](https://docs.obsidian.md/Plugins/Releasing/Plugin+guidelines)
