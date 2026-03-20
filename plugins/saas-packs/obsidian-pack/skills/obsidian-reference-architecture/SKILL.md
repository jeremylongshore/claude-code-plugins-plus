---
name: obsidian-reference-architecture
description: |
  Implement Obsidian reference architecture with best-practice project layout.
  Use when designing new plugins, reviewing project structure,
  or establishing architecture standards for Obsidian development.
  Trigger with phrases like "obsidian architecture", "obsidian project structure",
  "obsidian best practices", "organize obsidian plugin".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Obsidian Reference Architecture

## Overview
Architecture patterns for complex Obsidian plugins: modular project structure with separate files for views, commands, settings, and services; state management; a service layer for vault operations; command registry; view manager; and CSS scoping.

## Prerequisites
- TypeScript and Obsidian API familiarity
- Working build pipeline (esbuild recommended)
- Plugin scaffolding complete (`manifest.json`, `package.json`, `tsconfig.json`)

## Instructions

### Step 1: Project Structure
```
my-plugin/
├── src/
│   ├── main.ts              # Plugin entry — thin orchestrator
│   ├── types.ts              # Shared interfaces and type definitions
│   ├── constants.ts          # Plugin-wide constants
│   ├── commands/
│   │   ├── index.ts          # Command registry
│   │   ├── insert-template.ts
│   │   └── toggle-sidebar.ts
│   ├── views/
│   │   ├── index.ts          # View registry
│   │   ├── sidebar-view.ts
│   │   └── modal-view.ts
│   ├── settings/
│   │   ├── settings.ts       # Settings interface and defaults
│   │   └── settings-tab.ts   # Settings UI tab
│   └── services/
│       ├── vault-service.ts  # File read/write/search operations
│       ├── metadata-service.ts  # Frontmatter and cache operations
│       └── sync-service.ts   # External sync or background tasks
├── styles.css
├── manifest.json
├── versions.json
├── package.json
├── tsconfig.json
└── esbuild.config.mjs
```

### Step 2: Thin Main Entry Point
```typescript
// src/main.ts — orchestrates, does not implement
import { Plugin } from 'obsidian';
import { MyPluginSettings, DEFAULT_SETTINGS } from './settings/settings';
import { MySettingTab } from './settings/settings-tab';
import { registerCommands } from './commands';
import { registerViews } from './views';
import { VaultService } from './services/vault-service';

export default class MyPlugin extends Plugin {
  settings: MyPluginSettings;
  vaultService: VaultService;

  async onload() {
    await this.loadSettings();
    this.vaultService = new VaultService(this.app);

    registerCommands(this);
    registerViews(this);
    this.addSettingTab(new MySettingTab(this.app, this));
  }

  onunload() {
    // Services clean up their own resources
    this.vaultService.destroy();
  }

  async loadSettings() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
  }

  async saveSettings() {
    await this.saveData(this.settings);
  }
}
```

### Step 3: Command Registry Pattern
```typescript
// src/commands/index.ts
import type MyPlugin from '../main';
import { insertTemplate } from './insert-template';
import { toggleSidebar } from './toggle-sidebar';

export function registerCommands(plugin: MyPlugin) {
  plugin.addCommand({
    id: 'insert-template',
    name: 'Insert Template',
    editorCallback: (editor, view) => insertTemplate(plugin, editor, view),
  });

  plugin.addCommand({
    id: 'toggle-sidebar',
    name: 'Toggle Sidebar',
    callback: () => toggleSidebar(plugin),
  });
}
```

```typescript
// src/commands/insert-template.ts
import { Editor, MarkdownView } from 'obsidian';
import type MyPlugin from '../main';

export function insertTemplate(plugin: MyPlugin, editor: Editor, view: MarkdownView) {
  const template = plugin.settings.defaultTemplate;
  editor.replaceSelection(template);
}
```

### Step 4: View Manager
```typescript
// src/views/index.ts
import type MyPlugin from '../main';
import { SidebarView, VIEW_TYPE_SIDEBAR } from './sidebar-view';

export function registerViews(plugin: MyPlugin) {
  plugin.registerView(VIEW_TYPE_SIDEBAR, (leaf) => new SidebarView(leaf, plugin));

  // Add ribbon icon to activate view
  plugin.addRibbonIcon('layout-sidebar-right', 'Open Sidebar', () => {
    activateView(plugin);
  });
}

async function activateView(plugin: MyPlugin) {
  const { workspace } = plugin.app;

  let leaf = workspace.getLeavesOfType(VIEW_TYPE_SIDEBAR)[0];
  if (!leaf) {
    const rightLeaf = workspace.getRightLeaf(false);
    if (rightLeaf) {
      await rightLeaf.setViewState({ type: VIEW_TYPE_SIDEBAR, active: true });
      leaf = rightLeaf;
    }
  }
  if (leaf) {
    workspace.revealLeaf(leaf);
  }
}
```

```typescript
// src/views/sidebar-view.ts
import { ItemView, WorkspaceLeaf } from 'obsidian';
import type MyPlugin from '../main';

export const VIEW_TYPE_SIDEBAR = 'my-plugin-sidebar';

export class SidebarView extends ItemView {
  plugin: MyPlugin;

  constructor(leaf: WorkspaceLeaf, plugin: MyPlugin) {
    super(leaf);
    this.plugin = plugin;
  }

  getViewType(): string {
    return VIEW_TYPE_SIDEBAR;
  }

  getDisplayText(): string {
    return 'My Plugin';
  }

  getIcon(): string {
    return 'layout-sidebar-right';
  }

  async onOpen() {
    const container = this.containerEl.children[1];
    container.empty();
    container.addClass('my-plugin-sidebar');

    container.createEl('h3', { text: 'My Plugin' });
    const list = container.createEl('ul');

    // Populate from service layer
    const files = await this.plugin.vaultService.getRecentFiles(10);
    for (const file of files) {
      list.createEl('li', { text: file.basename });
    }
  }

  async onClose() {
    // Clean up DOM references
    this.containerEl.empty();
  }
}
```

### Step 5: Service Layer for Vault Operations
```typescript
// src/services/vault-service.ts
import { App, TFile, TFolder, CachedMetadata } from 'obsidian';

export class VaultService {
  constructor(private app: App) {}

  // File operations
  async readFile(path: string): Promise<string> {
    const file = this.app.vault.getAbstractFileByPath(path);
    if (!(file instanceof TFile)) throw new Error(`Not a file: ${path}`);
    return this.app.vault.read(file);
  }

  async writeFile(path: string, content: string): Promise<void> {
    const file = this.app.vault.getAbstractFileByPath(path);
    if (file instanceof TFile) {
      await this.app.vault.modify(file, content);
    } else {
      await this.app.vault.create(path, content);
    }
  }

  // Search operations
  getFilesInFolder(folderPath: string): TFile[] {
    const folder = this.app.vault.getAbstractFileByPath(folderPath);
    if (!(folder instanceof TFolder)) return [];
    return folder.children.filter((f): f is TFile => f instanceof TFile);
  }

  getRecentFiles(limit: number): TFile[] {
    return this.app.vault.getMarkdownFiles()
      .sort((a, b) => b.stat.mtime - a.stat.mtime)
      .slice(0, limit);
  }

  // Metadata operations
  getMetadata(file: TFile): CachedMetadata | null {
    return this.app.metadataCache.getFileCache(file);
  }

  getFrontmatter(file: TFile): Record<string, unknown> | undefined {
    return this.getMetadata(file)?.frontmatter;
  }

  // Cleanup
  destroy() {
    // Release any held references
  }
}
```

### Step 6: Settings Architecture
```typescript
// src/settings/settings.ts
export interface MyPluginSettings {
  version: number;
  defaultTemplate: string;
  showStatusBar: boolean;
  syncInterval: number;
}

export const DEFAULT_SETTINGS: MyPluginSettings = {
  version: 1,
  defaultTemplate: '## New Section\n\n',
  showStatusBar: true,
  syncInterval: 300,
};
```

```typescript
// src/settings/settings-tab.ts
import { App, PluginSettingTab, Setting } from 'obsidian';
import type MyPlugin from '../main';

export class MySettingTab extends PluginSettingTab {
  plugin: MyPlugin;

  constructor(app: App, plugin: MyPlugin) {
    super(app, plugin);
    this.plugin = plugin;
  }

  display(): void {
    const { containerEl } = this;
    containerEl.empty();

    new Setting(containerEl)
      .setName('Default template')
      .setDesc('Content inserted by the Insert Template command')
      .addTextArea(text => text
        .setValue(this.plugin.settings.defaultTemplate)
        .onChange(async (value) => {
          this.plugin.settings.defaultTemplate = value;
          await this.plugin.saveSettings();
        }));

    new Setting(containerEl)
      .setName('Show status bar')
      .setDesc('Display plugin status in the bottom bar')
      .addToggle(toggle => toggle
        .setValue(this.plugin.settings.showStatusBar)
        .onChange(async (value) => {
          this.plugin.settings.showStatusBar = value;
          await this.plugin.saveSettings();
        }));

    new Setting(containerEl)
      .setName('Sync interval')
      .setDesc('Seconds between background syncs (0 to disable)')
      .addSlider(slider => slider
        .setLimits(0, 3600, 60)
        .setValue(this.plugin.settings.syncInterval)
        .setDynamicTooltip()
        .onChange(async (value) => {
          this.plugin.settings.syncInterval = value;
          await this.plugin.saveSettings();
        }));
  }
}
```

### Step 7: CSS Architecture with Plugin-Scoped Classes
```css
/* styles.css — all classes prefixed with plugin id */

/* Layout */
.my-plugin-sidebar {
  padding: 8px 12px;
}

.my-plugin-sidebar h3 {
  margin: 0 0 12px;
  font-size: var(--font-ui-medium);
  color: var(--text-normal);
}

.my-plugin-sidebar ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.my-plugin-sidebar li {
  padding: 4px 8px;
  border-radius: var(--radius-s);
  cursor: pointer;
  color: var(--text-muted);
}

.my-plugin-sidebar li:hover {
  background: var(--background-modifier-hover);
  color: var(--text-normal);
}

/* Modal styles */
.my-plugin-modal .modal-content {
  padding: 16px;
}

/* Use Obsidian CSS variables — never hardcode colors */
.my-plugin-highlight {
  background: var(--background-modifier-success);
  color: var(--text-on-accent);
  border-radius: var(--radius-s);
  padding: 2px 6px;
}

/* Responsive: Obsidian handles mobile layout, but adjust spacing */
.is-mobile .my-plugin-sidebar {
  padding: 4px 8px;
}

.is-mobile .my-plugin-sidebar li {
  padding: 8px;  /* Larger touch targets */
}
```

Key CSS rules:
- Prefix every class with your plugin id to avoid collisions
- Use Obsidian CSS variables (`--text-normal`, `--background-modifier-hover`, etc.) for theme compatibility
- Use `.is-mobile` for mobile-specific overrides
- Never use `!important` — it breaks theme compatibility

### Step 8: State Management Pattern
For plugins with complex state (multiple views, background sync, shared data):

```typescript
// src/services/state-service.ts
import { Events } from 'obsidian';

interface PluginState {
  isProcessing: boolean;
  lastSync: number | null;
  activeItems: string[];
}

export class StateService extends Events {
  private state: PluginState = {
    isProcessing: false,
    lastSync: null,
    activeItems: [],
  };

  get(): Readonly<PluginState> {
    return this.state;
  }

  update(partial: Partial<PluginState>) {
    Object.assign(this.state, partial);
    this.trigger('state-changed', this.state);
  }

  // Views subscribe to state changes
  // In a view: plugin.stateService.on('state-changed', (state) => this.refresh(state));
}
```

## Output
- Modular `src/` directory with separate folders for commands, views, settings, and services
- Thin `main.ts` that wires components together without implementing business logic
- Command registry that scales to dozens of commands without cluttering main.ts
- View manager with proper lifecycle (onOpen/onClose) and leaf management
- Service layer abstracting vault operations behind a clean API
- Type-safe settings with defaults and migration support
- Plugin-scoped CSS using Obsidian's CSS variable system

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Circular dependencies | Services importing main, main importing services | Use `type` imports or interface segregation |
| Missing types at runtime | Interface-only imports | Create `types.ts` for shared interfaces |
| Event listener leaks | Direct `addEventListener` calls | Use `this.registerEvent()` for automatic cleanup |
| Settings lost on upgrade | No migration path | Version your settings interface (see `obsidian-prod-checklist`) |
| CSS conflicts with other plugins | Generic class names | Prefix all classes with your plugin id |
| View not restoring on restart | Missing `registerView` | Register in `onload`, Obsidian restores state from layout |
| Service holds stale references | No cleanup on unload | Call `destroy()` on services in `onunload()` |

## Examples

### Adding a New Command
```typescript
// 1. Create src/commands/export-notes.ts
import type MyPlugin from '../main';

export async function exportNotes(plugin: MyPlugin) {
  const files = plugin.vaultService.getRecentFiles(50);
  // ... export logic
}

// 2. Register in src/commands/index.ts
import { exportNotes } from './export-notes';

// Add to registerCommands():
plugin.addCommand({
  id: 'export-notes',
  name: 'Export Recent Notes',
  callback: () => exportNotes(plugin),
});
```

### Adding a New Service
```typescript
// src/services/search-service.ts
import { App, TFile, PreparedQuery, prepareQuery, fuzzySearch } from 'obsidian';

export class SearchService {
  constructor(private app: App) {}

  fuzzyFind(query: string): TFile[] {
    const prepared: PreparedQuery = prepareQuery(query);
    return this.app.vault.getMarkdownFiles()
      .filter(f => fuzzySearch(prepared, f.basename)?.score !== undefined)
      .sort((a, b) => {
        const sa = fuzzySearch(prepared, a.basename)?.score ?? -Infinity;
        const sb = fuzzySearch(prepared, b.basename)?.score ?? -Infinity;
        return sb - sa;
      });
  }
}
```

## Resources
- [Obsidian Plugin API Reference](https://docs.obsidian.md/Reference/TypeScript+API)
- [Obsidian Plugin Guidelines](https://docs.obsidian.md/Plugins/Releasing/Plugin+guidelines)
- [Clean Architecture (Robert C. Martin)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Obsidian Sample Plugin](https://github.com/obsidianmd/obsidian-sample-plugin)

## Next Steps
For SDK patterns and API usage, see `obsidian-sdk-patterns`.
For production readiness, see `obsidian-prod-checklist`.
