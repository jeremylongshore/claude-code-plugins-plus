---
name: obsidian-hello-world
description: |
  Create a minimal working Obsidian plugin with commands and settings.
  Use when building your first plugin feature, testing your setup,
  or learning basic Obsidian plugin patterns.
  Trigger with phrases like "obsidian hello world", "first obsidian plugin",
  "obsidian quick start", "simple obsidian plugin".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Obsidian Hello World

## Overview
Build a minimal working Obsidian plugin demonstrating core features: commands, settings, and ribbon icons.

## Prerequisites
- Completed `obsidian-install-auth` setup
- Development vault configured
- Build pipeline working

## Instructions

### Step 1: Create Main Plugin Class
```typescript
// src/main.ts
import { App, Editor, MarkdownView, Modal, Notice, Plugin, PluginSettingTab, Setting } from 'obsidian';

interface MyPluginSettings {
  greeting: string;
}

const DEFAULT_SETTINGS: MyPluginSettings = {
  greeting: 'Hello, Obsidian!'
}

export default class MyPlugin extends Plugin {
  settings: MyPluginSettings;

  async onload() {
    await this.loadSettings();

    // Add ribbon icon
    this.addRibbonIcon('dice', 'Greet Me', (evt: MouseEvent) => {
      new Notice(this.settings.greeting);
    });

    // Add command to command palette
    this.addCommand({
      id: 'show-greeting',
      name: 'Show Greeting',
      callback: () => {
        new Notice(this.settings.greeting);
      }
    });

    // Add command with editor context
    this.addCommand({
      id: 'insert-greeting',
      name: 'Insert Greeting at Cursor',
      editorCallback: (editor: Editor, view: MarkdownView) => {
        editor.replaceSelection(this.settings.greeting);
      }
    });

    // Add settings tab
    this.addSettingTab(new MySettingTab(this.app, this));
  }

  onunload() {
    console.log('Goodbye from My Plugin!');
  }

  async loadSettings() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
  }

  async saveSettings() {
    await this.saveData(this.settings);
  }
}
```

### Step 2: Create Settings Tab
```typescript
// Add to src/main.ts
class MySettingTab extends PluginSettingTab {
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
      .setName('Greeting')
      .setDesc('The message to display when greeting')
      .addText(text => text
        .setPlaceholder('Enter your greeting')
        .setValue(this.plugin.settings.greeting)
        .onChange(async (value) => {
          this.plugin.settings.greeting = value;
          await this.plugin.saveSettings();
        }));
  }
}
```

### Step 3: Create a Modal
```typescript
// Add to src/main.ts
class GreetingModal extends Modal {
  greeting: string;

  constructor(app: App, greeting: string) {
    super(app);
    this.greeting = greeting;
  }

  onOpen() {
    const { contentEl } = this;
    contentEl.createEl('h1', { text: this.greeting });
    contentEl.createEl('p', { text: 'Click outside or press Escape to close.' });
  }

  onClose() {
    const { contentEl } = this;
    contentEl.empty();
  }
}

// Add to onload():
this.addCommand({
  id: 'show-greeting-modal',
  name: 'Show Greeting Modal',
  callback: () => {
    new GreetingModal(this.app, this.settings.greeting).open();
  }
});
```

### Step 4: Build and Test
```bash
set -euo pipefail
# Build the plugin
npm run build

# In Obsidian:
# 1. Open Settings > Community plugins
# 2. Enable "My Plugin"
# 3. Click the dice icon in ribbon
# 4. Open command palette (Ctrl/Cmd+P) and search "Show Greeting"
```

## Output
- Working plugin with:
  - Ribbon icon that shows a notice
  - Commands in command palette
  - Editor command to insert text
  - Settings tab to configure greeting
  - Modal for displaying content

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Plugin not loading | Build errors | Check console for TypeScript errors |
| Settings not saving | Missing loadData/saveData | Verify async/await usage |
| Command not showing | Plugin not enabled | Enable in Community Plugins |
| Ribbon icon missing | Wrong icon name | Use valid Lucide icon name |

## Examples

### Available Icon Names
Obsidian uses Lucide icons. Common examples:
- `file-text`, `folder`, `search`, `settings`
- `star`, `heart`, `bookmark`, `tag`
- `edit`, `trash`, `copy`, `clipboard`
- `link`, `external-link`, `globe`
- `dice`, `bot`, `sparkles`, `wand`

### Status Bar Item
```typescript
// Add to onload():
const statusBarItem = this.addStatusBarItem();
statusBarItem.setText('Plugin Active');
```

### Register Event Listeners
```typescript
// Listen to file open
this.registerEvent(
  this.app.workspace.on('file-open', (file) => {
    if (file) {
      console.log('Opened:', file.path);
    }
  })
);
```

## Resources
- [Obsidian Plugin API](https://docs.obsidian.md/Reference/TypeScript+API)
- [Lucide Icons](https://lucide.dev/icons/)
- [Obsidian Hub](https://publish.obsidian.md/hub/)

## Next Steps
Proceed to `obsidian-local-dev-loop` for hot-reload development workflow.