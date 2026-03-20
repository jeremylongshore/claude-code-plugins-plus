---
name: obsidian-webhooks-events
description: |
  Handle Obsidian events and workspace callbacks for plugin development.
  Use when implementing reactive features, handling file changes,
  or responding to user interactions in your plugin.
  Trigger with phrases like "obsidian events", "obsidian callbacks",
  "obsidian file change", "obsidian workspace events".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Obsidian Webhooks & Events

## Overview
Complete guide to Obsidian's event system: vault events (create, modify, delete, rename), workspace events (layout, leaf changes, editor state), metadataCache events, DOM events, custom EventRef patterns, and periodic tasks. Every event registration uses `this.registerEvent()` for automatic cleanup on plugin unload.

## Prerequisites
- Working Obsidian plugin with `onload()` / `onunload()` lifecycle
- Understanding of TypeScript event handler signatures
- Familiarity with Obsidian's TFile, TFolder, and WorkspaceLeaf types

## Instructions

### Step 1: Vault Events — File Lifecycle

Vault events fire when files and folders are created, modified, deleted, or renamed.

```typescript
import { Plugin, TFile, TFolder, TAbstractFile } from 'obsidian';

export default class EventPlugin extends Plugin {
  async onload() {
    // File created
    this.registerEvent(
      this.app.vault.on('create', (file: TAbstractFile) => {
        if (file instanceof TFile) {
          console.log('New file:', file.path);
          this.onFileCreated(file);
        }
        if (file instanceof TFolder) {
          console.log('New folder:', file.path);
        }
      })
    );

    // File content modified (fires on save and on every sync update)
    this.registerEvent(
      this.app.vault.on('modify', (file: TAbstractFile) => {
        if (file instanceof TFile) {
          this.onFileModified(file);
        }
      })
    );

    // File deleted
    this.registerEvent(
      this.app.vault.on('delete', (file: TAbstractFile) => {
        if (file instanceof TFile) {
          this.removeFromIndex(file.path);
        }
      })
    );

    // File renamed or moved (includes folder moves)
    this.registerEvent(
      this.app.vault.on('rename', (file: TAbstractFile, oldPath: string) => {
        if (file instanceof TFile) {
          this.updatePathReferences(oldPath, file.path);
        }
      })
    );
  }
}
```

Note: `modify` fires on every keystroke during live editing in some configurations. Always debounce if your handler does non-trivial work (see `obsidian-rate-limits`).

### Step 2: Workspace Events — UI State Changes

Workspace events track what the user is looking at and how the UI layout changes.

```typescript
async onload() {
  // Active file changed (user clicked a different tab/pane)
  this.registerEvent(
    this.app.workspace.on('active-leaf-change', (leaf) => {
      if (leaf) {
        const view = leaf.view;
        if (view.getViewType() === 'markdown') {
          const file = (view as any).file as TFile;
          if (file) {
            this.onActiveFileChanged(file);
          }
        }
      }
    })
  );

  // File opened in any pane (fires even if already active)
  this.registerEvent(
    this.app.workspace.on('file-open', (file: TFile | null) => {
      if (file) {
        this.trackRecentFile(file);
      }
    })
  );

  // Layout changed (panes split, closed, rearranged)
  this.registerEvent(
    this.app.workspace.on('layout-change', () => {
      this.updateSidebarState();
    })
  );

  // Editor changed (cursor moved, selection changed, content edited)
  this.registerEvent(
    this.app.workspace.on('editor-change', (editor, info) => {
      // info is MarkdownView — gives you the file context
      const cursor = editor.getCursor();
      this.onCursorMoved(cursor.line, cursor.ch);
    })
  );

  // Window/pane resized
  this.registerEvent(
    this.app.workspace.on('resize', () => {
      this.adjustCustomViews();
    })
  );

  // Wait for layout to be fully initialized before accessing panes
  this.app.workspace.onLayoutReady(() => {
    this.initializeWithCurrentState();
  });
}
```

### Step 3: MetadataCache Events — Content Indexing

The metadataCache parses frontmatter, links, tags, and headings in the background. These events fire when parsing completes.

```typescript
async onload() {
  // Single file's metadata changed (fires after modify, once parsing is done)
  this.registerEvent(
    this.app.metadataCache.on('changed', (file: TFile, data: string, cache: CachedMetadata) => {
      // cache contains parsed frontmatter, links, tags, headings
      const tags = cache.tags?.map(t => t.tag) ?? [];
      const links = cache.links?.map(l => l.link) ?? [];
      this.updateFileIndex(file.path, { tags, links });
    })
  );

  // All files in vault have been indexed (fires once after startup)
  this.registerEvent(
    this.app.metadataCache.on('resolved', () => {
      console.log('Metadata cache fully resolved — safe to query all files');
      this.buildFullIndex();
    })
  );
}

private buildFullIndex() {
  const files = this.app.vault.getMarkdownFiles();
  for (const file of files) {
    const cache = this.app.metadataCache.getFileCache(file);
    if (cache) {
      this.updateFileIndex(file.path, {
        tags: cache.tags?.map(t => t.tag) ?? [],
        links: cache.links?.map(l => l.link) ?? [],
        headings: cache.headings?.map(h => h.heading) ?? [],
        frontmatter: cache.frontmatter,
      });
    }
  }
}
```

The `resolved` event is critical for plugins that build indexes — querying metadataCache before it fires returns incomplete data.

### Step 4: DOM Events with registerDomEvent

For custom UI elements, use `registerDomEvent` instead of raw `addEventListener`. Obsidian auto-removes these on plugin unload.

```typescript
async onload() {
  // Register click handler on a custom element
  const button = this.addStatusBarItem();
  button.setText('Click me');

  this.registerDomEvent(button, 'click', (evt: MouseEvent) => {
    new Notice('Status bar clicked!');
  });

  // Listen for keyboard shortcuts on the document
  this.registerDomEvent(document, 'keydown', (evt: KeyboardEvent) => {
    if (evt.ctrlKey && evt.key === 'q') {
      this.toggleFeature();
    }
  });

  // Drag and drop on a custom view
  const dropZone = createEl('div', { cls: 'my-drop-zone' });
  this.registerDomEvent(dropZone, 'dragover', (evt: DragEvent) => {
    evt.preventDefault();
    dropZone.addClass('drag-active');
  });

  this.registerDomEvent(dropZone, 'drop', async (evt: DragEvent) => {
    evt.preventDefault();
    dropZone.removeClass('drag-active');
    const files = evt.dataTransfer?.files;
    if (files?.length) {
      await this.handleDroppedFiles(files);
    }
  });
}
```

### Step 5: Periodic Tasks with registerInterval

Use `registerInterval` for timers — they auto-clear on unload. Never use raw `setInterval`.

```typescript
async onload() {
  // Auto-save draft every 30 seconds
  this.registerInterval(
    window.setInterval(() => {
      this.autoSaveDraft();
    }, 30_000)
  );

  // Refresh external data every 5 minutes
  this.registerInterval(
    window.setInterval(() => {
      this.refreshExternalData();
    }, 5 * 60_000)
  );
}

private draftSaving = false;

private async autoSaveDraft() {
  // Overlap guard — skip if previous save is still running
  if (this.draftSaving) return;
  this.draftSaving = true;
  try {
    const view = this.app.workspace.getActiveViewOfType(MarkdownView);
    if (view?.file) {
      const content = view.editor.getValue();
      await this.saveDraft(view.file.path, content);
    }
  } finally {
    this.draftSaving = false;
  }
}
```

### Step 6: Custom Event Bus for Plugin-Internal Communication

For complex plugins with multiple views or components, create an internal event bus.

```typescript
import { Events } from 'obsidian';

// Create a typed event bus
class PluginEventBus extends Events {
  // Type-safe event methods
  onIndexUpdated(callback: (paths: string[]) => void): EventRef {
    return this.on('index-updated', callback);
  }

  triggerIndexUpdated(paths: string[]) {
    this.trigger('index-updated', paths);
  }

  onSettingsChanged(callback: (settings: PluginSettings) => void): EventRef {
    return this.on('settings-changed', callback);
  }

  triggerSettingsChanged(settings: PluginSettings) {
    this.trigger('settings-changed', settings);
  }
}

// Usage in plugin
class MyPlugin extends Plugin {
  bus = new PluginEventBus();

  async onload() {
    // Views subscribe to events
    this.registerEvent(
      this.bus.onIndexUpdated((paths) => {
        this.sidebarView?.refresh(paths);
      })
    );

    // Something triggers the event
    this.registerEvent(
      this.app.vault.on('modify', async (file) => {
        if (file instanceof TFile) {
          await this.reindex(file);
          this.bus.triggerIndexUpdated([file.path]);
        }
      })
    );
  }
}
```

Obsidian's `Events` class is the same base class used by `Vault`, `Workspace`, and `MetadataCache`. Using it for your own bus gives you a consistent pattern with `on/off/trigger`.

## Output
- Vault event handlers for file create, modify, delete, rename
- Workspace event handlers for active leaf, file open, editor changes, layout
- MetadataCache handlers for content parsing and full-vault resolution
- DOM event registration with auto-cleanup
- Periodic tasks with overlap guards
- Custom event bus for internal plugin communication

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Memory leak | Using `addEventListener` directly | Always use `registerDomEvent` or `registerEvent` |
| Stale data in handler | MetadataCache not resolved yet | Wait for `resolved` event before building index |
| Handler fires before layout | Accessing workspace in `onload` | Wrap in `onLayoutReady` callback |
| Handler runs after unload | Raw setInterval not cleared | Use `registerInterval` exclusively |
| Performance hit from modify | Handler runs on every keystroke | Debounce the handler (500ms is a good default) |
| Null leaf in active-leaf-change | All panes closed | Guard with `if (leaf)` check |

## Examples

### File Change Logger
```typescript
// Log all file operations to a daily note
async onload() {
  const logEvent = async (action: string, path: string) => {
    const today = moment().format('YYYY-MM-DD');
    const logPath = `logs/${today}.md`;
    const line = `- ${moment().format('HH:mm:ss')} ${action}: ${path}`;
    await this.appendOrCreate(logPath, line);
  };

  this.registerEvent(this.app.vault.on('create', (f) => logEvent('created', f.path)));
  this.registerEvent(this.app.vault.on('delete', (f) => logEvent('deleted', f.path)));
  this.registerEvent(this.app.vault.on('rename', (f, old) => logEvent(`renamed from ${old}`, f.path)));
}
```

### Tag Watcher — React to Frontmatter Tag Changes
```typescript
private tagCache = new Map<string, string[]>();

async onload() {
  this.registerEvent(
    this.app.metadataCache.on('changed', (file, data, cache) => {
      const newTags = cache.frontmatter?.tags ?? [];
      const oldTags = this.tagCache.get(file.path) ?? [];

      const added = newTags.filter((t: string) => !oldTags.includes(t));
      const removed = oldTags.filter(t => !newTags.includes(t));

      if (added.length || removed.length) {
        this.onTagsChanged(file, added, removed);
      }

      this.tagCache.set(file.path, [...newTags]);
    })
  );
}
```

## Resources
- [Obsidian Events API](https://docs.obsidian.md/Reference/TypeScript+API/Events)
- [Workspace Events](https://docs.obsidian.md/Reference/TypeScript+API/Workspace)
- [Vault Events](https://docs.obsidian.md/Reference/TypeScript+API/Vault)
- [MetadataCache API](https://docs.obsidian.md/Reference/TypeScript+API/MetadataCache)

## Next Steps
For throttling and debouncing these events under load, see `obsidian-rate-limits`. For production readiness, see `obsidian-prod-checklist`.
