---
name: obsidian-data-handling
description: |
  Implement vault data backup, sync, and recovery strategies.
  Use when building backup features, implementing data export,
  or handling vault synchronization in your plugin.
  Trigger with phrases like "obsidian backup", "obsidian sync",
  "obsidian data export", "vault backup strategy".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Obsidian Data Handling

## Overview
Data management patterns for Obsidian plugins: plugin config with loadData/saveData, vault file I/O, frontmatter parsing via metadataCache, handling renames and deletes, cross-device sync considerations, and IndexedDB fallback for large datasets.

## Prerequisites
- Working Obsidian plugin (`export default class extends Plugin`)
- Understanding of Obsidian's `Vault` and `MetadataCache` APIs
- TypeScript compilation configured

## Instructions

### Step 1: Plugin Config with loadData / saveData

Obsidian stores plugin data in `.obsidian/plugins/<plugin-id>/data.json`. Use `loadData()` and `saveData()` — never read that file directly.

```typescript
interface PluginConfig {
  version: number;
  apiEndpoint: string;
  syncInterval: number;
  excludedFolders: string[];
}

const DEFAULT_CONFIG: PluginConfig = {
  version: 1,
  apiEndpoint: 'https://api.example.com',
  syncInterval: 300,
  excludedFolders: [],
};

export default class DataPlugin extends Plugin {
  config: PluginConfig;

  async onload() {
    await this.loadConfig();
  }

  async loadConfig() {
    const saved = await this.loadData();
    this.config = Object.assign({}, DEFAULT_CONFIG, saved);

    // Migrate from older config versions
    if (this.config.version < 1) {
      this.config.excludedFolders = [];
      this.config.version = 1;
      await this.saveConfig();
    }
  }

  async saveConfig() {
    await this.saveData(this.config);
  }
}
```

`loadData()` returns `null` on first run — `Object.assign` onto defaults handles this cleanly.

### Step 2: Reading and Writing Vault Files

```typescript
import { TFile, TFolder, normalizePath } from 'obsidian';

// Read a markdown file
async readNote(path: string): Promise<string | null> {
  const file = this.app.vault.getAbstractFileByPath(normalizePath(path));
  if (file instanceof TFile) {
    return await this.app.vault.read(file);
  }
  return null;
}

// Write or create a markdown file
async writeNote(path: string, content: string): Promise<TFile> {
  const normalized = normalizePath(path);
  const existing = this.app.vault.getAbstractFileByPath(normalized);

  if (existing instanceof TFile) {
    await this.app.vault.modify(existing, content);
    return existing;
  }

  // Ensure parent folder exists
  const dir = normalized.substring(0, normalized.lastIndexOf('/'));
  if (dir && !this.app.vault.getAbstractFileByPath(dir)) {
    await this.app.vault.createFolder(dir);
  }

  return await this.app.vault.create(normalized, content);
}

// Append to a file (e.g., a log or journal)
async appendToNote(path: string, text: string): Promise<void> {
  const file = this.app.vault.getAbstractFileByPath(normalizePath(path));
  if (file instanceof TFile) {
    await this.app.vault.append(file, '\n' + text);
  }
}
```

Use `vault.cachedRead()` instead of `vault.read()` when you don't need the absolute latest content — it avoids hitting disk on every call.

### Step 3: Working with Frontmatter via MetadataCache

Never parse YAML frontmatter manually. Obsidian's `metadataCache` keeps a parsed cache of every file's frontmatter.

```typescript
import { TFile, CachedMetadata } from 'obsidian';

// Read frontmatter from a file
getFrontmatter(file: TFile): Record<string, any> | null {
  const cache: CachedMetadata | null = this.app.metadataCache.getFileCache(file);
  return cache?.frontmatter ?? null;
}

// Update frontmatter using processFrontMatter (Obsidian 1.4+)
async setStatus(file: TFile, status: string): Promise<void> {
  await this.app.fileManager.processFrontMatter(file, (fm) => {
    fm.status = status;
    fm.updated = new Date().toISOString();
  });
}

// Bulk query: find all files with a specific tag
getFilesWithTag(tag: string): TFile[] {
  const files: TFile[] = [];
  for (const file of this.app.vault.getMarkdownFiles()) {
    const cache = this.app.metadataCache.getFileCache(file);
    const tags = cache?.tags?.map(t => t.tag) ?? [];
    const fmTags = cache?.frontmatter?.tags ?? [];
    if (tags.includes(tag) || fmTags.includes(tag.replace('#', ''))) {
      files.push(file);
    }
  }
  return files;
}
```

`processFrontMatter` handles YAML serialization correctly — it preserves comments and formatting, and is the only safe way to update frontmatter programmatically.

### Step 4: Handling File Renames and Deletes

Plugins that index file paths must update their state when files move or disappear.

```typescript
async onload() {
  // Track renames to update internal references
  this.registerEvent(
    this.app.vault.on('rename', (file, oldPath) => {
      if (file instanceof TFile) {
        this.onFileRenamed(file, oldPath);
      }
    })
  );

  // Clean up when files are deleted
  this.registerEvent(
    this.app.vault.on('delete', (file) => {
      if (file instanceof TFile) {
        this.onFileDeleted(file.path);
      }
    })
  );
}

private onFileRenamed(file: TFile, oldPath: string) {
  // Update any stored path references
  if (this.config.pinnedFiles?.includes(oldPath)) {
    const idx = this.config.pinnedFiles.indexOf(oldPath);
    this.config.pinnedFiles[idx] = file.path;
    this.saveConfig();
  }
}

private onFileDeleted(path: string) {
  // Remove from any indexes
  if (this.config.pinnedFiles?.includes(path)) {
    this.config.pinnedFiles = this.config.pinnedFiles.filter(p => p !== path);
    this.saveConfig();
  }
}
```

Always use `registerEvent` — it automatically cleans up the listener when the plugin unloads.

### Step 5: Cross-Device Sync Considerations

Obsidian vaults synced via iCloud, Dropbox, or Obsidian Sync introduce eventual consistency issues.

```typescript
// Problem: two devices modify data.json simultaneously
// Solution: merge-friendly data structures

interface SyncSafeConfig {
  // Use a map keyed by unique IDs instead of arrays
  // Maps merge better than arrays across sync conflicts
  items: Record<string, { value: string; updatedAt: number }>;
}

// Timestamp-based last-write-wins merge
mergeConfigs(local: SyncSafeConfig, remote: SyncSafeConfig): SyncSafeConfig {
  const merged: SyncSafeConfig = { items: {} };
  const allKeys = new Set([
    ...Object.keys(local.items),
    ...Object.keys(remote.items),
  ]);

  for (const key of allKeys) {
    const l = local.items[key];
    const r = remote.items[key];
    if (!l) merged.items[key] = r;
    else if (!r) merged.items[key] = l;
    else merged.items[key] = l.updatedAt >= r.updatedAt ? l : r;
  }
  return merged;
}
```

Guidelines for sync-friendly plugins:
- Avoid storing file paths in `data.json` — they differ across devices with different vault locations
- Use file content hashes or frontmatter IDs for identity instead of paths
- Keep `data.json` small — large files cause sync conflicts and slow sync

### Step 6: IndexedDB Fallback for Large Datasets

When plugin data exceeds what's practical for `data.json` (more than ~1MB), use IndexedDB.

```typescript
class PluginDatabase {
  private db: IDBDatabase | null = null;
  private dbName: string;

  constructor(pluginId: string) {
    this.dbName = `obsidian-${pluginId}`;
  }

  async open(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, 1);

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        if (!db.objectStoreNames.contains('cache')) {
          db.createObjectStore('cache', { keyPath: 'id' });
        }
      };

      request.onsuccess = (event) => {
        this.db = (event.target as IDBOpenDBRequest).result;
        resolve();
      };

      request.onerror = () => reject(request.error);
    });
  }

  async put(id: string, data: any): Promise<void> {
    if (!this.db) throw new Error('Database not open');
    return new Promise((resolve, reject) => {
      const tx = this.db!.transaction('cache', 'readwrite');
      tx.objectStore('cache').put({ id, data, updatedAt: Date.now() });
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  }

  async get(id: string): Promise<any | null> {
    if (!this.db) throw new Error('Database not open');
    return new Promise((resolve, reject) => {
      const tx = this.db!.transaction('cache', 'readonly');
      const request = tx.objectStore('cache').get(id);
      request.onsuccess = () => resolve(request.result?.data ?? null);
      request.onerror = () => reject(request.error);
    });
  }

  close() {
    this.db?.close();
    this.db = null;
  }
}

// Usage in plugin
async onload() {
  this.db = new PluginDatabase(this.manifest.id);
  await this.db.open();
}

onunload() {
  this.db?.close();
}
```

IndexedDB is per-device and does not sync across devices. Use it for caches and derived data that can be rebuilt, not for primary user data.

## Output
- Plugin config loading with version migration
- Safe vault file read/write/append operations
- Frontmatter access via metadataCache
- Rename and delete event handlers
- Sync-friendly data structures
- IndexedDB storage for large datasets

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `loadData()` returns null | First run, no data.json yet | `Object.assign` onto defaults |
| Frontmatter returns undefined | File not yet indexed by cache | Listen for `metadataCache.on('resolved')` |
| File write fails | Parent folder doesn't exist | Create folder with `vault.createFolder()` first |
| Settings lost after sync | Concurrent writes from two devices | Use merge-friendly data structures with timestamps |
| data.json too large / slow | Storing too much data | Move large data to IndexedDB |
| stale cache after modify | `cachedRead` returns old content | Use `vault.read()` when freshness matters |

## Examples

### Export All Notes with Tag to JSON
```typescript
async exportTaggedNotes(tag: string): Promise<string> {
  const files = this.getFilesWithTag(tag);
  const notes = await Promise.all(
    files.map(async (f) => ({
      path: f.path,
      content: await this.app.vault.read(f),
      frontmatter: this.getFrontmatter(f),
    }))
  );
  return JSON.stringify(notes, null, 2);
}
```

### Atomic Config Update
```typescript
async updateConfig<K extends keyof PluginConfig>(
  key: K,
  value: PluginConfig[K]
): Promise<void> {
  this.config[key] = value;
  await this.saveConfig();
}
```

## Resources
- [Obsidian Vault API](https://docs.obsidian.md/Reference/TypeScript+API/Vault)
- [Obsidian FileManager API](https://docs.obsidian.md/Reference/TypeScript+API/FileManager)
- [MetadataCache API](https://docs.obsidian.md/Reference/TypeScript+API/MetadataCache)
- [Obsidian Sync](https://help.obsidian.md/Obsidian+Sync)

## Next Steps
For team access control patterns, see `obsidian-enterprise-rbac`. For performance with large vaults, see `obsidian-rate-limits`.
