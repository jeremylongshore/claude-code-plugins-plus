---
name: obsidian-core-workflow-b
description: |
  Build advanced Obsidian plugin features: custom views (ItemView), modals,
  editor commands with selection manipulation, status bar, context menus,
  and Vault API file creation/modification. Use when adding UI components
  to a plugin, building sidebar views, or creating modal dialogs.
  Trigger with "obsidian modal", "obsidian custom view", "obsidian sidebar",
  "obsidian context menu", "obsidian editor command", "obsidian UI".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [obsidian, ui-components, views, modals, editor]
---

# Obsidian Core Workflow B: Advanced Plugin Features

## Overview

Add production UI to an existing Obsidian plugin: custom sidebar views,
modal dialogs with forms, fuzzy-search suggestion popups, editor commands
that manipulate selections, status bar widgets, context menus, and
programmatic file creation via the Vault API. Every snippet is a complete,
copy-pasteable class.

## Prerequisites

- A working plugin built with `obsidian-core-workflow-a` (or equivalent)
- `npm install --save-dev obsidian` already done
- Familiarity with the Plugin lifecycle (`onload` / `onunload`)

## Instructions

### Step 1: Custom sidebar view (ItemView)

A custom view registers a new panel type that can live in the left or right sidebar.

```typescript
// src/views/StatsView.ts
import { ItemView, WorkspaceLeaf, TFile } from "obsidian";

export const STATS_VIEW_TYPE = "vault-stats-view";

export class StatsView extends ItemView {
  constructor(leaf: WorkspaceLeaf) {
    super(leaf);
  }

  getViewType(): string {
    return STATS_VIEW_TYPE;
  }

  getDisplayText(): string {
    return "Vault Stats";
  }

  getIcon(): string {
    return "bar-chart-2";
  }

  async onOpen() {
    const container = this.containerEl.children[1];
    container.empty();
    container.addClass("stats-view");

    container.createEl("h4", { text: "Vault Statistics" });
    const listEl = container.createEl("ul");

    const files = this.app.vault.getMarkdownFiles();
    let totalWords = 0;

    for (const file of files) {
      const content = await this.app.vault.cachedRead(file);
      totalWords += content.split(/\s+/).filter(Boolean).length;
    }

    listEl.createEl("li", { text: `Notes: ${files.length}` });
    listEl.createEl("li", { text: `Total words: ${totalWords.toLocaleString()}` });
    listEl.createEl("li", {
      text: `Avg words/note: ${files.length ? Math.round(totalWords / files.length) : 0}`,
    });

    // Refresh button
    const btn = container.createEl("button", { text: "Refresh" });
    btn.addEventListener("click", () => this.onOpen());
  }

  async onClose() {
    // cleanup if needed
  }
}
```

Register and open it from your main plugin:

```typescript
// In your Plugin's onload():
import { StatsView, STATS_VIEW_TYPE } from "./views/StatsView";

this.registerView(STATS_VIEW_TYPE, (leaf) => new StatsView(leaf));

this.addCommand({
  id: "open-stats-view",
  name: "Open vault stats",
  callback: () => this.activateStatsView(),
});

this.addRibbonIcon("bar-chart-2", "Vault Stats", () => this.activateStatsView());

// Helper to open or reveal the view
async activateStatsView() {
  const { workspace } = this.app;
  let leaf = workspace.getLeavesOfType(STATS_VIEW_TYPE)[0];

  if (!leaf) {
    const rightLeaf = workspace.getRightLeaf(false);
    if (rightLeaf) {
      await rightLeaf.setViewState({ type: STATS_VIEW_TYPE, active: true });
      leaf = rightLeaf;
    }
  }
  if (leaf) workspace.revealLeaf(leaf);
}

// In onunload():
this.app.workspace.detachLeavesOfType(STATS_VIEW_TYPE);
```

### Step 2: Modal dialogs

**Confirmation modal** -- returns a boolean via callback:

```typescript
// src/modals/ConfirmModal.ts
import { App, Modal, Setting } from "obsidian";

export class ConfirmModal extends Modal {
  private resolved = false;
  constructor(
    app: App,
    private message: string,
    private onResult: (confirmed: boolean) => void
  ) {
    super(app);
  }

  onOpen() {
    const { contentEl } = this;
    contentEl.createEl("h3", { text: "Confirm" });
    contentEl.createEl("p", { text: this.message });

    new Setting(contentEl)
      .addButton((btn) =>
        btn.setButtonText("Cancel").onClick(() => this.close())
      )
      .addButton((btn) =>
        btn
          .setButtonText("Confirm")
          .setCta()
          .onClick(() => {
            this.resolved = true;
            this.close();
          })
      );
  }

  onClose() {
    this.onResult(this.resolved);
    this.contentEl.empty();
  }
}
```

**Text input modal** -- collects a single string:

```typescript
// src/modals/InputModal.ts
import { App, Modal, Setting } from "obsidian";

export class InputModal extends Modal {
  private value = "";
  constructor(
    app: App,
    private title: string,
    private placeholder: string,
    private onSubmit: (value: string | null) => void
  ) {
    super(app);
  }

  onOpen() {
    const { contentEl } = this;
    contentEl.createEl("h3", { text: this.title });

    new Setting(contentEl).addText((text) =>
      text
        .setPlaceholder(this.placeholder)
        .onChange((v) => (this.value = v))
    );

    new Setting(contentEl)
      .addButton((btn) =>
        btn.setButtonText("Cancel").onClick(() => {
          this.onSubmit(null);
          this.close();
        })
      )
      .addButton((btn) =>
        btn
          .setButtonText("OK")
          .setCta()
          .onClick(() => {
            this.onSubmit(this.value);
            this.close();
          })
      );
  }

  onClose() {
    this.contentEl.empty();
  }
}
```

### Step 3: Fuzzy suggestion modal (SuggestModal)

Opens a searchable list. Users type to filter, then pick an item.

```typescript
// src/modals/NotePicker.ts
import { App, FuzzySuggestModal, TFile } from "obsidian";

export class NotePicker extends FuzzySuggestModal<TFile> {
  constructor(app: App, private onPick: (file: TFile) => void) {
    super(app);
  }

  getItems(): TFile[] {
    return this.app.vault.getMarkdownFiles();
  }

  getItemText(file: TFile): string {
    return file.path;
  }

  onChooseItem(file: TFile): void {
    this.onPick(file);
  }
}

// Usage in a command:
this.addCommand({
  id: "pick-note",
  name: "Pick a note",
  callback: () => {
    new NotePicker(this.app, (file) => {
      new Notice(`Selected: ${file.basename}`);
    }).open();
  },
});
```

### Step 4: Editor commands with selection manipulation

`editorCallback` gives you the CodeMirror `Editor` and the active `MarkdownView`.

```typescript
// Wrap selection in callout
this.addCommand({
  id: "wrap-callout",
  name: "Wrap selection in callout",
  editorCallback: (editor, view) => {
    const selection = editor.getSelection();
    if (!selection) {
      new Notice("Select text first");
      return;
    }
    const callout = `> [!note]\n> ${selection.split("\n").join("\n> ")}`;
    editor.replaceSelection(callout);
  },
});

// Insert ISO timestamp at cursor
this.addCommand({
  id: "insert-timestamp",
  name: "Insert timestamp",
  editorCallback: (editor) => {
    const now = new Date().toISOString().slice(0, 19).replace("T", " ");
    editor.replaceSelection(now);
  },
});

// Sort selected lines alphabetically
this.addCommand({
  id: "sort-lines",
  name: "Sort selected lines",
  editorCallback: (editor) => {
    const selection = editor.getSelection();
    if (!selection) return;
    const sorted = selection.split("\n").sort((a, b) => a.localeCompare(b)).join("\n");
    editor.replaceSelection(sorted);
  },
});
```

### Step 5: Status bar items

Status bar items sit at the bottom of the Obsidian window.

```typescript
// In onload():
const statusEl = this.addStatusBarItem();
statusEl.setText("Words: --");

// Update word count when active file changes
this.registerEvent(
  this.app.workspace.on("active-leaf-change", async () => {
    const view = this.app.workspace.getActiveViewOfType(MarkdownView);
    if (view) {
      const content = view.editor.getValue();
      const count = content.split(/\s+/).filter(Boolean).length;
      statusEl.setText(`Words: ${count}`);
    } else {
      statusEl.setText("Words: --");
    }
  })
);
```

### Step 6: Context menus

Add items to the file explorer right-click menu and the editor right-click menu.

```typescript
// File explorer context menu -- only on markdown files
this.registerEvent(
  this.app.workspace.on("file-menu", (menu, file) => {
    if (file instanceof TFile && file.extension === "md") {
      menu.addItem((item) => {
        item
          .setTitle("Copy note title")
          .setIcon("clipboard-copy")
          .onClick(async () => {
            await navigator.clipboard.writeText(file.basename);
            new Notice(`Copied: ${file.basename}`);
          });
      });
    }
  })
);

// Editor context menu -- insert current date
this.registerEvent(
  this.app.workspace.on("editor-menu", (menu, editor) => {
    menu.addItem((item) => {
      item
        .setTitle("Insert today's date")
        .setIcon("calendar")
        .onClick(() => {
          const today = new Date().toISOString().slice(0, 10);
          editor.replaceSelection(today);
        });
    });
  })
);
```

### Step 7: File creation and modification via Vault API

Programmatically create, read, and modify notes.

```typescript
// Create a daily note if it doesn't exist
async ensureDailyNote(): Promise<TFile> {
  const today = new Date().toISOString().slice(0, 10);
  const path = `Daily/${today}.md`;

  const existing = this.app.vault.getAbstractFileByPath(path);
  if (existing instanceof TFile) return existing;

  // Ensure folder
  const folder = this.app.vault.getAbstractFileByPath("Daily");
  if (!folder) await this.app.vault.createFolder("Daily");

  const content = `# ${today}\n\n## Tasks\n\n- [ ] \n\n## Notes\n\n`;
  return this.app.vault.create(path, content);
}

// Append text to the end of a note
async appendToNote(file: TFile, text: string): Promise<void> {
  const current = await this.app.vault.read(file);
  await this.app.vault.modify(file, current + "\n" + text);
}

// Batch-update frontmatter tag across files
async addTagToFolder(folder: string, tag: string): Promise<number> {
  const files = this.app.vault.getMarkdownFiles()
    .filter((f) => f.path.startsWith(folder + "/"));

  let count = 0;
  for (const file of files) {
    let content = await this.app.vault.read(file);
    if (content.startsWith("---")) {
      // Has frontmatter -- insert tag
      content = content.replace(
        /^(---\n[\s\S]*?)(---)$/m,
        `$1tags:\n  - ${tag}\n$2`
      );
    } else {
      // No frontmatter -- add it
      content = `---\ntags:\n  - ${tag}\n---\n${content}`;
    }
    await this.app.vault.modify(file, content);
    count++;
  }
  return count;
}
```

## Output

After applying these patterns your plugin gains:
- A sidebar panel (ItemView) with live vault statistics
- Confirmation and text-input modal dialogs
- A fuzzy-search note picker
- Editor commands that transform selected text
- A live word-count status bar widget
- Right-click context menu extensions
- Vault API helpers for file creation and batch modification

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| View not appearing | Forgot `registerView` in `onload` | Must register before opening |
| `getRightLeaf` returns null | No sidebar available | Guard with `if (leaf)` |
| Modal closes without callback | Event order issue | Set result before calling `this.close()` |
| `editorCallback` greyed out | No active markdown editor | Use `callback` instead for non-editor commands |
| Context menu item missing | Wrong event name | `file-menu` for explorer, `editor-menu` for editor |
| `vault.create` throws | File already exists at path | Check with `getAbstractFileByPath` first |
| Stale `cachedRead` data | Cache not yet updated | Use `vault.read` when freshness matters |

## Examples

**Open a view in a new tab instead of sidebar:**
```typescript
const leaf = this.app.workspace.getLeaf("tab");
await leaf.setViewState({ type: STATS_VIEW_TYPE, active: true });
```

**Promise-based confirm modal:**
```typescript
function confirm(app: App, msg: string): Promise<boolean> {
  return new Promise((resolve) => {
    new ConfirmModal(app, msg, resolve).open();
  });
}

// Usage:
if (await confirm(this.app, "Delete all empty notes?")) {
  // proceed
}
```

## Resources

- [ItemView API](https://docs.obsidian.md/Reference/TypeScript+API/ItemView)
- [Modal API](https://docs.obsidian.md/Reference/TypeScript+API/Modal)
- [FuzzySuggestModal](https://docs.obsidian.md/Reference/TypeScript+API/FuzzySuggestModal)
- [Editor API](https://docs.obsidian.md/Reference/TypeScript+API/Editor)
- [Vault API](https://docs.obsidian.md/Reference/TypeScript+API/Vault)
- [Lucide Icons](https://lucide.dev/icons/)

## Next Steps

- Set up hot-reload development: see `obsidian-local-dev-loop`
- Apply production safety patterns: see `obsidian-sdk-patterns`
- Handle common errors: see `obsidian-common-errors`
