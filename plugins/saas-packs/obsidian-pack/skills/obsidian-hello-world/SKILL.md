---
name: obsidian-hello-world
description: |
  Create a minimal working Obsidian plugin with commands, settings, modals, and ribbon icons.
  Use when building your first plugin feature, testing your setup,
  or learning basic Obsidian plugin patterns.
  Trigger with phrases like "obsidian hello world", "first obsidian plugin",
  "obsidian quick start", "simple obsidian plugin".
allowed-tools: Read, Write, Edit, Bash(npm:*), Glob
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, obsidian, testing, getting-started]

---
# Obsidian Hello World

## Overview
Build a minimal working Obsidian plugin demonstrating the five core building blocks: commands (palette + editor + checkCallback), settings tab with typed config, ribbon icons, modals, and status bar. Every snippet uses real Obsidian API.

## Prerequisites
- Completed `obsidian-install-auth` setup (symlinked dev vault, `npm run dev` working)
- Build pipeline producing `main.js` from `src/main.ts`

## Instructions

### Step 1: Define Typed Settings
```typescript
// src/main.ts — top of file
import {
  App, Editor, MarkdownView, Modal, Notice,
  Plugin, PluginSettingTab, Setting, TFile
} from 'obsidian';

interface MyPluginSettings {
  greeting: string;
  showRibbon: boolean;
  dateFormat: string;
}

const DEFAULT_SETTINGS: MyPluginSettings = {
  greeting: 'Hello, Obsidian!',
  showRibbon: true,
  dateFormat: 'YYYY-MM-DD',
};
```

### Step 2: Create the Plugin Class with Commands
```typescript
export default class MyPlugin extends Plugin {
  settings: MyPluginSettings;

  async onload() {
    await this.loadSettings();

    // Ribbon icon — shows greeting as Notice
    if (this.settings.showRibbon) {
      this.addRibbonIcon('sparkles', 'My Plugin: Greet', () => {
        new Notice(this.settings.greeting);
      });
    }

    // Command: show greeting (available everywhere)
    this.addCommand({
      id: 'show-greeting',
      name: 'Show greeting',
      callback: () => new Notice(this.settings.greeting),
    });

    // Command: insert greeting at cursor (editor-only — greyed out when no editor is active)
    this.addCommand({
      id: 'insert-greeting',
      name: 'Insert greeting at cursor',
      editorCallback: (editor: Editor, view: MarkdownView) => {
        editor.replaceSelection(this.settings.greeting);
      },
    });

    // Command: word count with checkCallback (conditionally available)
    this.addCommand({
      id: 'count-words',
      name: 'Count words in current note',
      checkCallback: (checking: boolean) => {
        const view = this.app.workspace.getActiveViewOfType(MarkdownView);
        if (view) {
          if (!checking) {
            const text = view.editor.getValue();
            const count = text.split(/\s+/).filter(Boolean).length;
            new Notice(`Word count: ${count}`);
          }
          return true; // command is available
        }
        return false; // hide from palette when no editor
      },
    });

    // Command: open modal dialog
    this.addCommand({
      id: 'show-greeting-modal',
      name: 'Show greeting modal',
      callback: () => new GreetingModal(this.app, this.settings.greeting).open(),
    });

    // Command: insert today's date
    this.addCommand({
      id: 'insert-date',
      name: 'Insert today\'s date',
      editorCallback: (editor: Editor) => {
        const today = new Date().toISOString().slice(0, 10);
        editor.replaceSelection(today);
      },
    });

    // Status bar — persistent widget at bottom
    const statusEl = this.addStatusBarItem();
    statusEl.setText('Plugin loaded');

    // Update status bar when active file changes
    this.registerEvent(
      this.app.workspace.on('active-leaf-change', () => {
        const view = this.app.workspace.getActiveViewOfType(MarkdownView);
        if (view) {
          const count = view.editor.getValue().split(/\s+/).filter(Boolean).length;
          statusEl.setText(`Words: ${count}`);
        } else {
          statusEl.setText('No editor');
        }
      })
    );

    // Settings tab
    this.addSettingTab(new MySettingTab(this.app, this));
    console.log(`[${this.manifest.id}] loaded`);
  }

  onunload() {
    console.log(`[${this.manifest.id}] unloaded`);
  }

  async loadSettings() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
  }

  async saveSettings() {
    await this.saveData(this.settings);
  }
}
```

### Step 3: Create Settings Tab
```typescript
class MySettingTab extends PluginSettingTab {
  plugin: MyPlugin;

  constructor(app: App, plugin: MyPlugin) {
    super(app, plugin);
    this.plugin = plugin;
  }

  display(): void {
    const { containerEl } = this;
    containerEl.empty();

    new Setting(containerEl)
      .setName('Greeting message')
      .setDesc('Text shown by the greet command and ribbon icon.')
      .addText(text => text
        .setPlaceholder('Hello, Obsidian!')
        .setValue(this.plugin.settings.greeting)
        .onChange(async (value) => {
          this.plugin.settings.greeting = value;
          await this.plugin.saveSettings();
        }));

    new Setting(containerEl)
      .setName('Show ribbon icon')
      .setDesc('Toggle the sparkles icon in the left ribbon. Reload plugin to apply.')
      .addToggle(toggle => toggle
        .setValue(this.plugin.settings.showRibbon)
        .onChange(async (value) => {
          this.plugin.settings.showRibbon = value;
          await this.plugin.saveSettings();
        }));

    new Setting(containerEl)
      .setName('Date format')
      .setDesc('Format for the Insert Date command.')
      .addDropdown(dropdown => dropdown
        .addOption('YYYY-MM-DD', '2026-03-22')
        .addOption('MM/DD/YYYY', '03/22/2026')
        .addOption('DD.MM.YYYY', '22.03.2026')
        .setValue(this.plugin.settings.dateFormat)
        .onChange(async (value) => {
          this.plugin.settings.dateFormat = value;
          await this.plugin.saveSettings();
        }));
  }
}
```

### Step 4: Create a Modal
```typescript
class GreetingModal extends Modal {
  message: string;

  constructor(app: App, message: string) {
    super(app);
    this.message = message;
  }

  onOpen() {
    const { contentEl } = this;
    contentEl.createEl('h2', { text: this.message });
    contentEl.createEl('p', { text: 'This is a modal dialog from your plugin.' });

    // Add a button that does something
    const btn = contentEl.createEl('button', { text: 'Count vault files' });
    btn.addEventListener('click', () => {
      const count = this.app.vault.getMarkdownFiles().length;
      contentEl.createEl('p', { text: `Your vault has ${count} markdown files.` });
    });
  }

  onClose() {
    this.contentEl.empty();
  }
}
```

### Step 5: Build and Test
```bash
set -euo pipefail
npm run build

# In Obsidian:
# 1. Settings > Community plugins > Enable your plugin
# 2. Click the sparkles icon in the ribbon
# 3. Ctrl+P > "Show greeting"
# 4. Ctrl+P > "Count words in current note" (open a .md file first)
# 5. Ctrl+P > "Show greeting modal"
# 6. Settings > My Plugin > change the greeting
# 7. Check the status bar at bottom for word count
```

### Step 6: Listen to Vault Events
```typescript
// Add to onload() — react to file changes
this.registerEvent(
  this.app.workspace.on('file-open', (file: TFile | null) => {
    if (file) {
      console.log(`[${this.manifest.id}] Opened: ${file.path}`);
    }
  })
);

// Track file modifications (debounce for production — see obsidian-rate-limits)
this.registerEvent(
  this.app.vault.on('create', (file) => {
    if (file instanceof TFile) {
      new Notice(`New file: ${file.basename}`);
    }
  })
);
```

## Output
- Working plugin with:
  - Three command types: `callback`, `editorCallback`, `checkCallback`
  - Settings tab with text, toggle, and dropdown controls
  - Ribbon icon with click handler
  - Modal dialog with interactive button
  - Status bar widget with live word count
  - Event listeners for file-open and file-create

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Plugin not loading | Build errors or bad manifest | Check console (Ctrl+Shift+I) for red errors |
| Settings not saving | Missing `await` on `saveData` | Always `await this.saveSettings()` in `onChange` |
| Command greyed out | `editorCallback` needs active editor | Open a markdown note, or use `callback` instead |
| Ribbon icon missing | Invalid icon name | Use Lucide icon names: `sparkles`, `file-text`, `search` |
| Status bar not updating | Event not registered | Wrap in `this.registerEvent()` for auto-cleanup |
| Settings reset on restart | Forgot `saveData` call | `loadData` returns null on first run — `Object.assign` handles this |

## Examples

### Available Lucide Icon Names
Obsidian uses [Lucide icons](https://lucide.dev/icons/). Common examples:
- `file-text`, `folder`, `search`, `settings`, `star`
- `heart`, `bookmark`, `tag`, `link`, `external-link`
- `edit`, `trash-2`, `copy`, `clipboard`, `check`
- `dice`, `bot`, `sparkles`, `wand`, `calendar`
- `bar-chart-2`, `globe`, `download`, `upload`

### Command Types Summary
| Type | When Available | Use Case |
|------|---------------|----------|
| `callback` | Always | Non-editor commands (open modal, toggle feature) |
| `editorCallback` | When editor is active | Insert text, transform selection |
| `checkCallback` | Conditionally | Show/hide based on context |

### Register a Hotkey-Ready Command
```typescript
// Users assign hotkeys in Settings > Hotkeys
this.addCommand({
  id: 'toggle-feature',
  name: 'Toggle my feature',
  callback: () => this.toggleFeature(),
});
```

## Resources
- [Obsidian Plugin API](https://docs.obsidian.md/Reference/TypeScript+API)
- [Plugin Development Workflow](https://docs.obsidian.md/Plugins/Getting+started/Development+workflow)
- [Lucide Icons](https://lucide.dev/icons/) — icon names for `addRibbonIcon`
- [Obsidian Hub](https://publish.obsidian.md/hub/) — community knowledge base

## Next Steps
- Set up hot-reload development: `obsidian-local-dev-loop`
- Build advanced UI (views, fuzzy search, context menus): `obsidian-core-workflow-b`
- Apply production patterns: `obsidian-sdk-patterns`
