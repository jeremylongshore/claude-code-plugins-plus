---
name: obsidian-sdk-patterns
description: |
  Production-ready Obsidian plugin patterns: typed settings with migration,
  safe vault operations, event auto-cleanup, workspace layout, metadata cache,
  and debounced file handlers. Use when hardening a plugin for release,
  refactoring for reliability, or learning idiomatic Obsidian TypeScript.
  Trigger with "obsidian patterns", "obsidian best practices",
  "obsidian production code", "idiomatic obsidian plugin".
allowed-tools: Read, Write, Edit, Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [obsidian, patterns, production, typescript, best-practices]
---

# Obsidian SDK Patterns

## Overview

Six production patterns that prevent the most common Obsidian plugin bugs: lost
settings on upgrade, null-reference crashes on deleted files, memory leaks from
unregistered events, stale metadata, and UI jank from rapid file changes. Each
pattern is self-contained and copy-pasteable.

## Prerequisites

- A working Obsidian plugin (see `obsidian-core-workflow-a`)
- TypeScript strict mode enabled (`"strictNullChecks": true` in tsconfig)
- Familiarity with `Plugin.onload()` / `onunload()` lifecycle

## Instructions

### Step 1: Typed settings with versioned migration

Settings break when you add or rename fields between releases. Version the
settings object and migrate on load so existing users keep their data.

```typescript
// src/settings.ts
interface PluginSettingsV1 {
  apiKey: string;
  interval: number;
}

interface PluginSettingsV2 {
  version: 2;
  apiKey: string;
  syncInterval: number;      // renamed from "interval"
  excludedFolders: string[]; // new field
  theme: "default" | "minimal";
}

// Current version is always the latest
type PluginSettings = PluginSettingsV2;

const DEFAULTS: PluginSettings = {
  version: 2,
  apiKey: "",
  syncInterval: 300,
  excludedFolders: [],
  theme: "default",
};

export async function loadSettings(plugin: Plugin): Promise<PluginSettings> {
  const raw = (await plugin.loadData()) as any;
  if (!raw) return { ...DEFAULTS };

  // Migrate v1 -> v2
  if (!raw.version || raw.version < 2) {
    raw.version = 2;
    if (raw.interval !== undefined) {
      raw.syncInterval = raw.interval;
      delete raw.interval;
    }
    raw.excludedFolders = raw.excludedFolders ?? [];
    raw.theme = raw.theme ?? "default";
    await plugin.saveData(raw);
  }

  // Merge with defaults to pick up any newly added fields
  return { ...DEFAULTS, ...raw };
}
```

Why: `Object.assign({}, DEFAULTS, raw)` handles new fields added in patch
releases. The explicit migration block handles renames and type changes between
major versions.

### Step 2: Safe vault operations (check-before-act)

The Vault API throws if you create a file that exists or read one that was
deleted between your check and your call. Wrap every operation.

```typescript
// src/vault-helpers.ts
import { App, TFile, TFolder, TAbstractFile, normalizePath } from "obsidian";

export class VaultHelper {
  constructor(private app: App) {}

  /** Read file content, return null if file doesn't exist */
  async safeRead(path: string): Promise<string | null> {
    const file = this.app.vault.getAbstractFileByPath(normalizePath(path));
    if (!(file instanceof TFile)) return null;
    return this.app.vault.read(file);
  }

  /** Create or overwrite a file. Creates parent folders as needed. */
  async safeWrite(path: string, content: string): Promise<TFile> {
    const normalized = normalizePath(path);
    await this.ensureParentFolder(normalized);

    const existing = this.app.vault.getAbstractFileByPath(normalized);
    if (existing instanceof TFile) {
      await this.app.vault.modify(existing, content);
      return existing;
    }
    return this.app.vault.create(normalized, content);
  }

  /** Append content to a file. Creates the file if it doesn't exist. */
  async safeAppend(path: string, content: string): Promise<void> {
    const normalized = normalizePath(path);
    const existing = this.app.vault.getAbstractFileByPath(normalized);
    if (existing instanceof TFile) {
      const current = await this.app.vault.read(existing);
      await this.app.vault.modify(existing, current + content);
    } else {
      await this.ensureParentFolder(normalized);
      await this.app.vault.create(normalized, content);
    }
  }

  /** Delete a file if it exists, moving to trash by default. */
  async safeDelete(path: string, useTrash = true): Promise<boolean> {
    const file = this.app.vault.getAbstractFileByPath(normalizePath(path));
    if (!(file instanceof TFile)) return false;
    if (useTrash) {
      await this.app.vault.trash(file, false);
    } else {
      await this.app.vault.delete(file);
    }
    return true;
  }

  /** Ensure a folder (and all parents) exist. */
  private async ensureParentFolder(filePath: string): Promise<void> {
    const parts = filePath.split("/");
    parts.pop(); // remove filename
    let current = "";
    for (const part of parts) {
      current = current ? `${current}/${part}` : part;
      const existing = this.app.vault.getAbstractFileByPath(current);
      if (!existing) {
        await this.app.vault.createFolder(current);
      }
    }
  }
}
```

### Step 3: Event management with automatic cleanup

Every `this.registerEvent(...)` call in `onload()` is automatically cleaned up
when the plugin unloads. Never use raw `addEventListener` or `app.vault.on()`
without registering -- those leak.

```typescript
export default class MyPlugin extends Plugin {
  async onload() {
    // File events -- auto-cleaned on unload
    this.registerEvent(
      this.app.vault.on("create", (file) => {
        if (file instanceof TFile) this.onFileCreated(file);
      })
    );

    this.registerEvent(
      this.app.vault.on("delete", (file) => {
        if (file instanceof TFile) this.onFileDeleted(file);
      })
    );

    this.registerEvent(
      this.app.vault.on("rename", (file, oldPath) => {
        if (file instanceof TFile) this.onFileRenamed(file, oldPath);
      })
    );

    // Workspace events
    this.registerEvent(
      this.app.workspace.on("active-leaf-change", (leaf) => {
        this.onActiveLeafChange(leaf);
      })
    );

    this.registerEvent(
      this.app.workspace.on("layout-change", () => {
        this.onLayoutChange();
      })
    );

    // Periodic tasks -- also auto-cleaned
    this.registerInterval(
      window.setInterval(() => this.periodicSync(), 60_000)
    );

    // DOM events -- use registerDomEvent for auto-cleanup
    this.registerDomEvent(document, "keydown", (evt: KeyboardEvent) => {
      if (evt.key === "F5") this.refreshData();
    });
  }

  // No cleanup code needed in onunload() -- all registered events
  // are automatically removed by the Plugin base class.
}
```

Anti-pattern to avoid:
```typescript
// BAD: leaks on plugin unload
this.app.vault.on("modify", handler);
document.addEventListener("click", handler);

// GOOD: auto-cleaned
this.registerEvent(this.app.vault.on("modify", handler));
this.registerDomEvent(document, "click", handler);
```

### Step 4: Workspace layout manipulation

Open files in specific panes, split views, and restore layout state.

```typescript
import { MarkdownView, WorkspaceLeaf } from "obsidian";

export class WorkspaceHelper {
  constructor(private app: App) {}

  /** Open a file in a new tab */
  async openInNewTab(path: string): Promise<void> {
    const file = this.app.vault.getAbstractFileByPath(path);
    if (!(file instanceof TFile)) return;
    const leaf = this.app.workspace.getLeaf("tab");
    await leaf.openFile(file);
  }

  /** Open a file in a vertical split to the right */
  async openInSplit(path: string): Promise<void> {
    const file = this.app.vault.getAbstractFileByPath(path);
    if (!(file instanceof TFile)) return;
    const leaf = this.app.workspace.getLeaf("split", "vertical");
    await leaf.openFile(file);
  }

  /** Get the currently active markdown file (or null) */
  getActiveFile(): TFile | null {
    const view = this.app.workspace.getActiveViewOfType(MarkdownView);
    return view?.file ?? null;
  }

  /** Iterate all open markdown leaves */
  forEachOpenNote(callback: (file: TFile, leaf: WorkspaceLeaf) => void): void {
    this.app.workspace.iterateAllLeaves((leaf) => {
      if (leaf.view instanceof MarkdownView && leaf.view.file) {
        callback(leaf.view.file, leaf);
      }
    });
  }

  /** Pin/unpin the active tab */
  togglePin(): void {
    const leaf = this.app.workspace.getLeaf();
    if (leaf) {
      const pinned = (leaf as any).pinned;
      (leaf as any).setPinned(!pinned);
    }
  }
}
```

### Step 5: Metadata cache for fast queries

`metadataCache` is Obsidian's pre-parsed index of all vault files. It avoids
reading file content for frontmatter, tags, links, and headings.

```typescript
import { App, TFile, CachedMetadata } from "obsidian";

export class MetadataHelper {
  constructor(private app: App) {}

  /** Get parsed metadata for a file (frontmatter, tags, links, headings) */
  getCache(file: TFile): CachedMetadata | null {
    return this.app.metadataCache.getFileCache(file);
  }

  /** Get frontmatter value, returns undefined if missing */
  getFrontmatterValue(file: TFile, key: string): any | undefined {
    const cache = this.getCache(file);
    return cache?.frontmatter?.[key];
  }

  /** Find all files with a specific tag */
  filesWithTag(tag: string): TFile[] {
    const normalized = tag.startsWith("#") ? tag : `#${tag}`;
    return this.app.vault.getMarkdownFiles().filter((file) => {
      const cache = this.getCache(file);
      // Tags in body
      const bodyTags = cache?.tags?.map((t) => t.tag) ?? [];
      // Tags in frontmatter
      const fmTags = (cache?.frontmatter?.tags ?? []).map((t: string) =>
        t.startsWith("#") ? t : `#${t}`
      );
      return [...bodyTags, ...fmTags].includes(normalized);
    });
  }

  /** Get all outgoing links from a file */
  outgoingLinks(file: TFile): string[] {
    const cache = this.getCache(file);
    const links = cache?.links?.map((l) => l.link) ?? [];
    const embeds = cache?.embeds?.map((e) => e.link) ?? [];
    return [...new Set([...links, ...embeds])];
  }

  /** Get files that link to this file (backlinks) */
  backlinks(file: TFile): TFile[] {
    const resolved = this.app.metadataCache.resolvedLinks;
    const results: TFile[] = [];
    for (const [sourcePath, targets] of Object.entries(resolved)) {
      if (file.path in targets) {
        const source = this.app.vault.getAbstractFileByPath(sourcePath);
        if (source instanceof TFile) results.push(source);
      }
    }
    return results;
  }

  /** Wait for metadata cache to be fully indexed (useful on plugin load) */
  onCacheReady(callback: () => void): void {
    if (this.app.metadataCache.initialized) {
      callback();
    } else {
      this.app.metadataCache.on("initialized", callback);
    }
  }

  /** Listen for metadata changes on a specific file */
  onFileMetadataChange(
    plugin: Plugin,
    filePath: string,
    callback: (cache: CachedMetadata) => void
  ): void {
    plugin.registerEvent(
      this.app.metadataCache.on("changed", (file, _data, cache) => {
        if (file.path === filePath) callback(cache);
      })
    );
  }
}
```

### Step 6: Debounced file modification handlers

Plugins that react to file changes (auto-save, indexing, sync) fire too often
without debouncing. Obsidian's vault `modify` event fires on every keystroke
when live preview is active.

```typescript
import { Plugin, TFile, debounce } from "obsidian";

export default class IndexerPlugin extends Plugin {
  // Debounce: wait 2s after last modification before processing
  private processFile = debounce(
    async (file: TFile) => {
      console.log(`[Indexer] Processing ${file.path}`);
      const content = await this.app.vault.read(file);
      await this.updateIndex(file, content);
    },
    2000,
    true  // true = reset timer on each call (trailing edge)
  );

  async onload() {
    this.registerEvent(
      this.app.vault.on("modify", (file) => {
        if (file instanceof TFile && file.extension === "md") {
          this.processFile(file);
        }
      })
    );
  }

  private async updateIndex(file: TFile, content: string): Promise<void> {
    // Your indexing logic here -- runs at most once per 2s per file
  }
}
```

For per-file debouncing (different timers for different files):

```typescript
private fileTimers = new Map<string, ReturnType<typeof setTimeout>>();

private debouncedProcess(file: TFile, delayMs = 2000): void {
  const existing = this.fileTimers.get(file.path);
  if (existing) clearTimeout(existing);

  this.fileTimers.set(
    file.path,
    setTimeout(async () => {
      this.fileTimers.delete(file.path);
      const content = await this.app.vault.read(file);
      await this.updateIndex(file, content);
    }, delayMs)
  );
}

// Clean up all timers on unload
onunload() {
  for (const timer of this.fileTimers.values()) {
    clearTimeout(timer);
  }
  this.fileTimers.clear();
}
```

## Output

After applying these patterns:
- Settings survive across plugin updates with automatic migration
- File operations never crash on missing files or duplicate paths
- All events auto-clean on plugin unload (zero memory leaks)
- Workspace manipulation opens files in tabs, splits, or sidebar
- Metadata cache provides instant tag/link/frontmatter queries without reading files
- File modification handlers are debounced to prevent UI jank and redundant work

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| Settings lost after update | No version field / no migration | Add `version` to settings interface, migrate in `loadSettings` |
| `null` file reference | File deleted between check and use | Always re-fetch with `getAbstractFileByPath` immediately before use |
| Memory leak warning | Events registered without `registerEvent` | Wrap every `.on()` with `this.registerEvent()` |
| Stale metadata | Cache not yet updated after `vault.modify` | Listen to `metadataCache.on('changed')` instead of reading immediately |
| Plugin slows Obsidian | Processing every keystroke | Debounce `modify` handlers (2s+ delay) |
| `createFolder` throws | Folder already exists | Check `getAbstractFileByPath` first |
| `normalizePath` undefined | Forgot import | Import from `"obsidian"` |

## Examples

**Complete plugin using all patterns together:**
```typescript
import { Plugin, TFile, debounce, normalizePath } from "obsidian";
import { loadSettings, PluginSettings } from "./settings";
import { VaultHelper } from "./vault-helpers";
import { MetadataHelper } from "./metadata-helpers";

export default class MyPlugin extends Plugin {
  settings: PluginSettings;
  vault: VaultHelper;
  meta: MetadataHelper;

  async onload() {
    this.settings = await loadSettings(this);
    this.vault = new VaultHelper(this.app);
    this.meta = new MetadataHelper(this.app);

    // Debounced auto-index
    const reindex = debounce(
      (file: TFile) => this.indexFile(file), 2000, true
    );
    this.registerEvent(
      this.app.vault.on("modify", (f) => {
        if (f instanceof TFile) reindex(f);
      })
    );
  }

  private async indexFile(file: TFile) {
    const content = await this.vault.safeRead(file.path);
    if (!content) return;
    const tags = this.meta.filesWithTag("index");
    // ... indexing logic
  }
}
```

## Resources
- [Obsidian Plugin API](https://docs.obsidian.md/Reference/TypeScript+API)
- [Vault API](https://docs.obsidian.md/Reference/TypeScript+API/Vault)
- [MetadataCache API](https://docs.obsidian.md/Reference/TypeScript+API/MetadataCache)
- [Plugin Guidelines](https://docs.obsidian.md/Plugins/Releasing/Plugin+guidelines)

## Next Steps
Debug and test: `obsidian-local-dev-loop`. Common errors: `obsidian-common-errors`. Release: `obsidian-prod-checklist`.
