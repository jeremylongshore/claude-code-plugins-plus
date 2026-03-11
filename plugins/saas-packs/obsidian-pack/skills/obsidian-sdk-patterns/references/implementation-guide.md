# Obsidian SDK Patterns - Implementation Guide

> Full implementation details for the parent SKILL.md.

## Detailed Instructions

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


## Complete Examples

### Frontmatter Parsing
```typescript
function getFrontmatter(app: App, file: TFile): any {
  const cache = app.metadataCache.getFileCache(file);
  return cache?.frontmatter || {};
}
```
