# Obsidian SDK Patterns -- Implementation Reference

## Overview

Production-ready TypeScript patterns for Obsidian plugin development: settings management,
modal components, leaf/view registration, workspace events, and editor extensions.

## Prerequisites

- Obsidian v1.0+ with TypeScript plugin scaffold
- Node.js 18+ with esbuild bundler
- `obsidian` npm package for type definitions

## Settings Pattern

```typescript
import { App, Plugin, PluginSettingTab, Setting } from 'obsidian';

interface MyPluginSettings {
    apiEndpoint: string;
    enableSync: boolean;
    syncInterval: number;
    ignoredFolders: string[];
}

const DEFAULT_SETTINGS: MyPluginSettings = {
    apiEndpoint: 'https://api.example.com',
    enableSync: false,
    syncInterval: 30,
    ignoredFolders: ['templates', '.trash'],
};

class MyPlugin extends Plugin {
    settings: MyPluginSettings;

    async onload() {
        await this.loadSettings();
        this.addSettingTab(new MySettingTab(this.app, this));
    }

    async loadSettings() {
        this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
    }

    async saveSettings() {
        await this.saveData(this.settings);
    }
}

class MySettingTab extends PluginSettingTab {
    constructor(app: App, private plugin: MyPlugin) {
        super(app, plugin);
    }

    display(): void {
        const { containerEl } = this;
        containerEl.empty();
        containerEl.createEl('h2', { text: 'My Plugin Settings' });

        new Setting(containerEl)
            .setName('API Endpoint')
            .setDesc('URL of your API service')
            .addText(text =>
                text
                    .setPlaceholder('https://api.example.com')
                    .setValue(this.plugin.settings.apiEndpoint)
                    .onChange(async value => {
                        this.plugin.settings.apiEndpoint = value;
                        await this.plugin.saveSettings();
                    })
            );

        new Setting(containerEl)
            .setName('Enable Sync')
            .setDesc('Automatically sync notes')
            .addToggle(toggle =>
                toggle
                    .setValue(this.plugin.settings.enableSync)
                    .onChange(async value => {
                        this.plugin.settings.enableSync = value;
                        await this.plugin.saveSettings();
                    })
            );

        new Setting(containerEl)
            .setName('Sync Interval')
            .setDesc('Minutes between automatic syncs')
            .addSlider(slider =>
                slider
                    .setLimits(5, 120, 5)
                    .setValue(this.plugin.settings.syncInterval)
                    .setDynamicTooltip()
                    .onChange(async value => {
                        this.plugin.settings.syncInterval = value;
                        await this.plugin.saveSettings();
                    })
            );
    }
}
```

## Custom Modal Pattern

```typescript
import { App, Modal, ButtonComponent, TextComponent } from 'obsidian';

export class InputModal extends Modal {
    private result: string = '';
    private onSubmit: (result: string) => void;

    constructor(app: App, onSubmit: (result: string) => void) {
        super(app);
        this.onSubmit = onSubmit;
    }

    onOpen(): void {
        const { contentEl } = this;
        contentEl.createEl('h2', { text: 'Enter a value' });

        let input: TextComponent;

        new Setting(contentEl)
            .setName('Value')
            .addText(text => {
                input = text;
                text.inputEl.addEventListener('keydown', e => {
                    if (e.key === 'Enter') this.submit(input.getValue());
                });
            });

        const buttonRow = contentEl.createDiv({ cls: 'modal-button-container' });

        new ButtonComponent(buttonRow)
            .setButtonText('Cancel')
            .onClick(() => this.close());

        new ButtonComponent(buttonRow)
            .setButtonText('Submit')
            .setCta()
            .onClick(() => this.submit(input.getValue()));
    }

    private submit(value: string): void {
        this.result = value;
        this.close();
        this.onSubmit(value);
    }

    onClose(): void {
        this.contentEl.empty();
    }
}
```

## Custom View (Leaf Panel)

```typescript
import { ItemView, WorkspaceLeaf } from 'obsidian';

export const MY_VIEW_TYPE = 'my-plugin-view';

export class MyView extends ItemView {
    getViewType(): string {
        return MY_VIEW_TYPE;
    }

    getDisplayText(): string {
        return 'My Plugin';
    }

    getIcon(): string {
        return 'star';  // Lucide icon name
    }

    async onOpen(): Promise<void> {
        const container = this.containerEl.children[1];
        container.empty();
        container.createEl('h4', { text: 'My Plugin Panel' });
        container.createEl('p', { text: 'Content goes here' });
    }

    async onClose(): Promise<void> {
        this.containerEl.children[1].empty();
    }
}

// Register and activate in Plugin
export default class MyPlugin extends Plugin {
    async onload() {
        this.registerView(MY_VIEW_TYPE, (leaf) => new MyView(leaf));

        this.addRibbonIcon('star', 'My Plugin', () => this.activateView());
    }

    async activateView(): Promise<void> {
        const { workspace } = this.app;

        let leaf = workspace.getLeavesOfType(MY_VIEW_TYPE)[0];
        if (!leaf) {
            leaf = workspace.getRightLeaf(false)!;
            await leaf.setViewState({ type: MY_VIEW_TYPE, active: true });
        }

        workspace.revealLeaf(leaf);
    }
}
```

## Workspace Event Patterns

```typescript
export default class MyPlugin extends Plugin {
    async onload() {
        // File open event
        this.registerEvent(
            this.app.workspace.on('file-open', async (file) => {
                if (!file) return;
                console.log(`Opened: ${file.path}`);
            })
        );

        // Active leaf change
        this.registerEvent(
            this.app.workspace.on('active-leaf-change', (leaf) => {
                const view = leaf?.view;
                console.log(`View type: ${view?.getViewType()}`);
            })
        );

        // Layout change (sidebars toggled, splits changed)
        this.registerEvent(
            this.app.workspace.on('layout-change', () => {
                console.log('Layout changed');
            })
        );

        // File rename/delete
        this.registerEvent(
            this.app.vault.on('rename', (file, oldPath) => {
                console.log(`Renamed: ${oldPath} -> ${file.path}`);
            })
        );
    }
}
```

## Command with Editor Callback

```typescript
export default class MyPlugin extends Plugin {
    async onload() {
        this.addCommand({
            id: 'insert-timestamp',
            name: 'Insert current timestamp',
            editorCallback: (editor) => {
                const ts = new Date().toISOString();
                editor.replaceSelection(ts);
            },
        });

        this.addCommand({
            id: 'wrap-selection',
            name: 'Wrap selection in backticks',
            editorCheckCallback: (checking, editor) => {
                const hasSelection = editor.somethingSelected();
                if (checking) return hasSelection;
                const selected = editor.getSelection();
                editor.replaceSelection(`\`${selected}\``);
            },
        });
    }
}
```

## Resources

- [Obsidian Plugin API Reference](https://github.com/obsidianmd/obsidian-api)
- [Obsidian Developer Docs](https://docs.obsidian.md/Plugins/Getting+started/Build+a+plugin)
- [Marcus Olsson Obsidian Plugin Guide](https://marcus.se.net/obsidian-plugin-docs/)

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
