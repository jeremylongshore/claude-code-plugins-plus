# Obsidian Reference Architecture - Implementation Guide

> Full implementation details for the parent SKILL.md.


## Complete Examples

### Quick Setup Script
```bash
#!/bin/bash

mkdir -p src/{services,commands,ui/{modals,views,components},events,utils,settings}
mkdir -p tests/{services,commands}

touch src/main.ts
touch src/types.ts
touch src/constants.ts
touch src/settings/{settings,settings-tab,settings-migration}.ts
touch src/services/{vault-service,metadata-service,search-service}.ts
touch src/commands/{index,note-commands,utility-commands}.ts
touch src/events/{event-manager,event-handlers}.ts
touch src/utils/{debounce,async-queue,cache,logger}.ts

echo "Plugin structure created!"
```


## Project Structure

```
my-obsidian-plugin/
├── src/
│   ├── main.ts                    # Plugin entry point
│   ├── types.ts                   # TypeScript type definitions
│   ├── constants.ts               # Constants and configuration
│   │
│   ├── settings/
│   │   ├── settings.ts            # Settings interface & defaults
│   │   ├── settings-tab.ts        # Settings UI component
│   │   └── settings-migration.ts  # Settings version migration
│   │
│   ├── services/
│   │   ├── vault-service.ts       # Vault operations
│   │   ├── metadata-service.ts    # Frontmatter/cache operations
│   │   ├── search-service.ts      # Search functionality
│   │   └── api-service.ts         # External API integration
│   │
│   ├── commands/
│   │   ├── index.ts               # Command registration
│   │   ├── note-commands.ts       # Note-related commands
│   │   └── utility-commands.ts    # Utility commands
│   │
│   ├── ui/
│   │   ├── modals/
│   │   │   ├── input-modal.ts
│   │   │   └── confirm-modal.ts
│   │   ├── views/
│   │   │   ├── sidebar-view.ts
│   │   │   └── view-registry.ts
│   │   └── components/
│   │       ├── status-bar.ts
│   │       └── ribbon-icon.ts
│   │
│   ├── events/
│   │   ├── event-manager.ts       # Event registration
│   │   └── event-handlers.ts      # Event handler implementations
│   │
│   └── utils/
│       ├── debounce.ts
│       ├── async-queue.ts
│       ├── cache.ts
│       └── logger.ts
│
├── tests/
│   ├── services/
│   │   └── vault-service.test.ts
│   ├── commands/
│   │   └── note-commands.test.ts
│   └── setup.ts                   # Test configuration
│
├── styles/
│   └── styles.css                 # Plugin styles
│
├── docs/
│   └── ARCHITECTURE.md            # Architecture documentation
│
├── manifest.json                  # Plugin manifest
├── versions.json                  # Version compatibility
├── package.json                   # Node dependencies
├── tsconfig.json                  # TypeScript configuration
├── esbuild.config.mjs            # Build configuration
├── .eslintrc.js                  # Linting rules
└── .gitignore
```


## Layer Architecture

```
┌─────────────────────────────────────────┐
│            UI Layer                      │
│   (Views, Modals, Components)            │
├─────────────────────────────────────────┤
│          Command Layer                   │
│   (Commands, Event Handlers)             │
├─────────────────────────────────────────┤
│          Service Layer                   │
│   (Business Logic, Data Access)          │
├─────────────────────────────────────────┤
│        Infrastructure Layer              │
│   (Cache, Logger, Utilities)             │
└─────────────────────────────────────────┘
```


## Key Components

### Step 1: Main Plugin Entry Point
```typescript
// src/main.ts
import { Plugin } from 'obsidian';
import { MyPluginSettings, DEFAULT_SETTINGS, MyPluginSettingsTab } from './settings';
import { VaultService } from './services/vault-service';
import { registerCommands } from './commands';
import { EventManager } from './events/event-manager';
import { registerViews } from './ui/views/view-registry';
import { Logger } from './utils/logger';

export default class MyPlugin extends Plugin {
  settings: MyPluginSettings;
  private logger: Logger;
  private vaultService: VaultService;
  private eventManager: EventManager;

  async onload() {
    this.logger = new Logger(this.manifest.id);
    this.logger.info('Loading plugin');

    // Load settings
    await this.loadSettings();

    // Initialize services
    this.vaultService = new VaultService(this.app);

    // Initialize event manager
    this.eventManager = new EventManager(this);

    // Register UI components
    this.addSettingTab(new MyPluginSettingsTab(this.app, this));
    registerViews(this);
    registerCommands(this);

    // Setup events after layout is ready
    this.app.workspace.onLayoutReady(() => {
      this.eventManager.registerAll();
      this.logger.info('Plugin ready');
    });
  }

  onunload() {
    this.logger.info('Unloading plugin');
    // Cleanup handled automatically by Obsidian
  }

  async loadSettings() {
    const data = await this.loadData();
    this.settings = Object.assign({}, DEFAULT_SETTINGS, data);
  }

  async saveSettings() {
    await this.saveData(this.settings);
  }

  // Public API for other plugins
  getVaultService(): VaultService {
    return this.vaultService;
  }
}
```

### Step 2: Service Layer Pattern
```typescript
// src/services/vault-service.ts
import { App, TFile, TFolder, Vault, CachedMetadata } from 'obsidian';

export class VaultService {
  constructor(private app: App) {}

  get vault(): Vault {
    return this.app.vault;
  }

  // File operations
  async readFile(file: TFile): Promise<string> {
    return this.vault.read(file);
  }

  async writeFile(file: TFile, content: string): Promise<void> {
    await this.vault.modify(file, content);
  }

  async createFile(path: string, content: string): Promise<TFile> {
    await this.ensureFolder(path);
    return this.vault.create(path, content);
  }

  getFileByPath(path: string): TFile | null {
    const file = this.vault.getAbstractFileByPath(path);
    return file instanceof TFile ? file : null;
  }

  // Folder operations
  private async ensureFolder(filePath: string): Promise<void> {
    const folderPath = filePath.substring(0, filePath.lastIndexOf('/'));
    if (!folderPath) return;

    const folder = this.vault.getAbstractFileByPath(folderPath);
    if (!folder) {
      await this.vault.createFolder(folderPath);
    }
  }

  // Query operations
  getMarkdownFiles(): TFile[] {
    return this.vault.getMarkdownFiles();
  }

  getFilesInFolder(folderPath: string): TFile[] {
    return this.getMarkdownFiles().filter(f => f.path.startsWith(folderPath + '/'));
  }

  // Metadata operations
  getMetadata(file: TFile): CachedMetadata | null {
    return this.app.metadataCache.getFileCache(file);
  }

  getFrontmatter(file: TFile): Record<string, any> | null {
    return this.getMetadata(file)?.frontmatter || null;
  }
}
```

### Step 3: Command Registration Pattern
```typescript
// src/commands/index.ts
import { Plugin } from 'obsidian';
import { registerNoteCommands } from './note-commands';
import { registerUtilityCommands } from './utility-commands';

export function registerCommands(plugin: Plugin): void {
  registerNoteCommands(plugin);
  registerUtilityCommands(plugin);
}

// src/commands/note-commands.ts
import { Plugin, MarkdownView, Editor } from 'obsidian';

export function registerNoteCommands(plugin: Plugin): void {
  // Simple command
  plugin.addCommand({
    id: 'my-plugin-action',
    name: 'Perform Action',
    callback: () => {
      // Action implementation
    },
  });

  // Editor command
  plugin.addCommand({
    id: 'my-plugin-editor-action',
    name: 'Editor Action',
    editorCallback: (editor: Editor, view: MarkdownView) => {
      // Editor-specific action
    },
  });

  // Conditional command
  plugin.addCommand({
    id: 'my-plugin-conditional',
    name: 'Conditional Action',
    checkCallback: (checking: boolean) => {
      const view = plugin.app.workspace.getActiveViewOfType(MarkdownView);
      if (view) {
        if (!checking) {
          // Execute action
        }
        return true;
      }
      return false;
    },
  });
}
```

### Step 4: Event Manager Pattern
```typescript
// src/events/event-manager.ts
import { Plugin, TFile, TAbstractFile } from 'obsidian';
import { debounce } from '../utils/debounce';

export class EventManager {
  constructor(private plugin: Plugin) {}

  registerAll(): void {
    this.registerVaultEvents();
    this.registerWorkspaceEvents();
  }

  private registerVaultEvents(): void {
    // Debounced file modify handler
    const onModify = debounce((file: TAbstractFile) => {
      if (file instanceof TFile) {
        this.handleFileModify(file);
      }
    }, 500);

    this.plugin.registerEvent(
      this.plugin.app.vault.on('modify', onModify)
    );

    this.plugin.registerEvent(
      this.plugin.app.vault.on('create', (file) => {
        if (file instanceof TFile) {
          this.handleFileCreate(file);
        }
      })
    );

    this.plugin.registerEvent(
      this.plugin.app.vault.on('delete', (file) => {
        this.handleFileDelete(file);
      })
    );

    this.plugin.registerEvent(
      this.plugin.app.vault.on('rename', (file, oldPath) => {
        if (file instanceof TFile) {
          this.handleFileRename(file, oldPath);
        }
      })
    );
  }

  private registerWorkspaceEvents(): void {
    this.plugin.registerEvent(
      this.plugin.app.workspace.on('file-open', (file) => {
        if (file) {
          this.handleFileOpen(file);
        }
      })
    );
  }

  private handleFileModify(file: TFile): void {
    // Handle file modification
  }

  private handleFileCreate(file: TFile): void {
    // Handle file creation
  }

  private handleFileDelete(file: TAbstractFile): void {
    // Handle file deletion
  }

  private handleFileRename(file: TFile, oldPath: string): void {
    // Handle file rename
  }

  private handleFileOpen(file: TFile): void {
    // Handle file open
  }
}
```

### Step 5: Settings Pattern
```typescript
// src/settings/settings.ts
export interface MyPluginSettings {
  enabled: boolean;
  apiEndpoint: string;
  maxItems: number;
  excludeFolders: string[];
  settingsVersion: number;
}

export const DEFAULT_SETTINGS: MyPluginSettings = {
  enabled: true,
  apiEndpoint: '',
  maxItems: 100,
  excludeFolders: [],
  settingsVersion: 1,
};

// src/settings/settings-tab.ts
import { App, PluginSettingTab, Setting } from 'obsidian';
import type MyPlugin from '../main';

export class MyPluginSettingsTab extends PluginSettingTab {
  plugin: MyPlugin;

  constructor(app: App, plugin: MyPlugin) {
    super(app, plugin);
    this.plugin = plugin;
  }

  display(): void {
    const { containerEl } = this;
    containerEl.empty();

    containerEl.createEl('h2', { text: 'My Plugin Settings' });

    new Setting(containerEl)
      .setName('Enable Plugin')
      .setDesc('Turn the plugin features on or off')
      .addToggle(toggle => toggle
        .setValue(this.plugin.settings.enabled)
        .onChange(async (value) => {
          this.plugin.settings.enabled = value;
          await this.plugin.saveSettings();
        }));

    new Setting(containerEl)
      .setName('Max Items')
      .setDesc('Maximum number of items to display')
      .addSlider(slider => slider
        .setLimits(10, 500, 10)
        .setValue(this.plugin.settings.maxItems)
        .setDynamicTooltip()
        .onChange(async (value) => {
          this.plugin.settings.maxItems = value;
          await this.plugin.saveSettings();
        }));
  }
}
```


## Data Flow Diagram

```
User Action (Command/Event)
         │
         ▼
┌─────────────────┐
│   UI Layer      │
│ (Modal/View)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Command Handler │
│ (Orchestration) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────┐
│ Service Layer   │────▶│   Cache     │
│ (Business)      │     │  (Memory)   │
└────────┬────────┘     └─────────────┘
         │
         ▼
┌─────────────────┐
│ Obsidian API    │
│ (Vault/Cache)   │
└─────────────────┘
```


## Flagship Skills

For multi-environment setup, see `obsidian-multi-env-setup`.
