# Obsidian Data Handling - Implementation Guide

> Full implementation details for the parent SKILL.md.

## Detailed Instructions

### Step 1: Data Export Service
```typescript
// src/services/export-service.ts
import { App, TFile, TFolder, Notice } from 'obsidian';

export interface ExportOptions {
  includeAttachments: boolean;
  includeMetadata: boolean;
  format: 'json' | 'markdown' | 'zip';
  folder?: string;
}

export interface ExportedNote {
  path: string;
  content: string;
  metadata?: Record<string, any>;
  created: number;
  modified: number;
}

export class ExportService {
  constructor(private app: App) {}

  async exportNotes(options: ExportOptions): Promise<ExportedNote[]> {
    const files = this.app.vault.getMarkdownFiles();
    const filteredFiles = options.folder
      ? files.filter(f => f.path.startsWith(options.folder!))
      : files;

    const exportedNotes: ExportedNote[] = [];

    for (const file of filteredFiles) {
      const content = await this.app.vault.read(file);
      const metadata = options.includeMetadata
        ? this.app.metadataCache.getFileCache(file)?.frontmatter
        : undefined;

      exportedNotes.push({
        path: file.path,
        content,
        metadata,
        created: file.stat.ctime,
        modified: file.stat.mtime,
      });
    }

    return exportedNotes;
  }

  async exportToJson(options: ExportOptions): Promise<string> {
    const notes = await this.exportNotes(options);
    const exportData = {
      exported: new Date().toISOString(),
      vault: this.app.vault.getName(),
      noteCount: notes.length,
      notes,
    };
    return JSON.stringify(exportData, null, 2);
  }

  async downloadExport(options: ExportOptions, filename: string): Promise<void> {
    const json = await this.exportToJson(options);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();

    URL.revokeObjectURL(url);
    new Notice(`Exported ${options.folder || 'all notes'}`);
  }
}
```

### Step 2: Data Import Service
```typescript
// src/services/import-service.ts
import { App, TFile, Notice } from 'obsidian';

export interface ImportOptions {
  overwrite: boolean;
  targetFolder?: string;
  dryRun: boolean;
}

export interface ImportResult {
  created: string[];
  updated: string[];
  skipped: string[];
  errors: { path: string; error: string }[];
}

export class ImportService {
  constructor(private app: App) {}

  async importFromJson(
    jsonContent: string,
    options: ImportOptions
  ): Promise<ImportResult> {
    const result: ImportResult = {
      created: [],
      updated: [],
      skipped: [],
      errors: [],
    };

    try {
      const data = JSON.parse(jsonContent);
      const notes = data.notes || [];

      for (const note of notes) {
        try {
          const targetPath = options.targetFolder
            ? `${options.targetFolder}/${note.path}`
            : note.path;

          const existing = this.app.vault.getAbstractFileByPath(targetPath);

          if (existing instanceof TFile) {
            if (options.overwrite) {
              if (!options.dryRun) {
                await this.app.vault.modify(existing, note.content);
              }
              result.updated.push(targetPath);
            } else {
              result.skipped.push(targetPath);
            }
          } else {
            if (!options.dryRun) {
              await this.ensureFolder(targetPath);
              await this.app.vault.create(targetPath, note.content);
            }
            result.created.push(targetPath);
          }
        } catch (error) {
          result.errors.push({
            path: note.path,
            error: (error as Error).message,
          });
        }
      }
    } catch (error) {
      result.errors.push({
        path: 'root',
        error: `Failed to parse JSON: ${(error as Error).message}`,
      });
    }

    return result;
  }

  private async ensureFolder(filePath: string): Promise<void> {
    const folderPath = filePath.substring(0, filePath.lastIndexOf('/'));
    if (!folderPath) return;

    const folder = this.app.vault.getAbstractFileByPath(folderPath);
    if (!folder) {
      await this.app.vault.createFolder(folderPath);
    }
  }

  async importFromFile(
    file: File,
    options: ImportOptions
  ): Promise<ImportResult> {
    const content = await file.text();
    return this.importFromJson(content, options);
  }
}
```

### Step 3: Backup Service
```typescript
// src/services/backup-service.ts
import { App, TFile, Notice } from 'obsidian';

export interface BackupConfig {
  autoBackup: boolean;
  intervalMinutes: number;
  maxBackups: number;
  backupFolder: string;
  includePluginData: boolean;
}

export interface BackupManifest {
  id: string;
  timestamp: string;
  vault: string;
  noteCount: number;
  size: number;
  checksum: string;
}

export class BackupService {
  private config: BackupConfig;
  private intervalId: number | null = null;

  constructor(private app: App, config: BackupConfig) {
    this.config = config;
  }

  async createBackup(): Promise<BackupManifest> {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const backupId = `backup-${timestamp}`;
    const backupFolder = `${this.config.backupFolder}/${backupId}`;

    // Create backup folder
    await this.app.vault.createFolder(backupFolder);

    // Get all markdown files
    const files = this.app.vault.getMarkdownFiles();
    let totalSize = 0;

    // Copy files
    for (const file of files) {
      const content = await this.app.vault.read(file);
      const targetPath = `${backupFolder}/${file.path}`;

      await this.ensureFolder(targetPath);
      await this.app.vault.create(targetPath, content);
      totalSize += content.length;
    }

    // Calculate checksum
    const checksum = await this.calculateVaultChecksum(files);

    // Create manifest
    const manifest: BackupManifest = {
      id: backupId,
      timestamp: new Date().toISOString(),
      vault: this.app.vault.getName(),
      noteCount: files.length,
      size: totalSize,
      checksum,
    };

    // Save manifest
    await this.app.vault.create(
      `${backupFolder}/manifest.json`,
      JSON.stringify(manifest, null, 2)
    );

    // Clean old backups
    await this.cleanOldBackups();

    new Notice(`Backup created: ${backupId}`);
    return manifest;
  }

  private async calculateVaultChecksum(files: TFile[]): Promise<string> {
    const encoder = new TextEncoder();
    let combinedContent = '';

    for (const file of files.sort((a, b) => a.path.localeCompare(b.path))) {
      const content = await this.app.vault.read(file);
      combinedContent += `${file.path}:${content.length}:`;
    }

    const data = encoder.encode(combinedContent);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('').substring(0, 16);
  }

  async listBackups(): Promise<BackupManifest[]> {
    const backups: BackupManifest[] = [];
    const backupFolder = this.app.vault.getAbstractFileByPath(this.config.backupFolder);

    if (!backupFolder) return backups;

    const children = (backupFolder as any).children || [];
    for (const child of children) {
      const manifestPath = `${child.path}/manifest.json`;
      const manifestFile = this.app.vault.getAbstractFileByPath(manifestPath);

      if (manifestFile instanceof TFile) {
        const content = await this.app.vault.read(manifestFile);
        backups.push(JSON.parse(content));
      }
    }

    return backups.sort((a, b) =>
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );
  }

  async restoreBackup(backupId: string, options: { dryRun: boolean }): Promise<void> {
    const backupFolder = `${this.config.backupFolder}/${backupId}`;
    const folder = this.app.vault.getAbstractFileByPath(backupFolder);

    if (!folder) {
      throw new Error(`Backup not found: ${backupId}`);
    }

    // Read manifest
    const manifestFile = this.app.vault.getAbstractFileByPath(
      `${backupFolder}/manifest.json`
    );
    if (!(manifestFile instanceof TFile)) {
      throw new Error('Invalid backup: manifest.json not found');
    }

    const manifest: BackupManifest = JSON.parse(
      await this.app.vault.read(manifestFile)
    );

    if (options.dryRun) {
      new Notice(`Would restore ${manifest.noteCount} notes from ${manifest.timestamp}`);
      return;
    }

    // Restore files
    const importService = new ImportService(this.app);
    const files = this.app.vault.getMarkdownFiles()
      .filter(f => f.path.startsWith(backupFolder + '/'))
      .filter(f => f.name !== 'manifest.json');

    for (const file of files) {
      const content = await this.app.vault.read(file);
      const targetPath = file.path.replace(backupFolder + '/', '');

      await this.ensureFolder(targetPath);
      const existing = this.app.vault.getAbstractFileByPath(targetPath);

      if (existing instanceof TFile) {
        await this.app.vault.modify(existing, content);
      } else {
        await this.app.vault.create(targetPath, content);
      }
    }

    new Notice(`Restored backup: ${manifest.noteCount} notes`);
  }

  private async cleanOldBackups(): Promise<void> {
    const backups = await this.listBackups();

    if (backups.length > this.config.maxBackups) {
      const toDelete = backups.slice(this.config.maxBackups);

      for (const backup of toDelete) {
        const folder = this.app.vault.getAbstractFileByPath(
          `${this.config.backupFolder}/${backup.id}`
        );
        if (folder) {
          await this.app.vault.delete(folder, true);
        }
      }
    }
  }

  private async ensureFolder(filePath: string): Promise<void> {
    const folderPath = filePath.substring(0, filePath.lastIndexOf('/'));
    if (!folderPath) return;

    const folder = this.app.vault.getAbstractFileByPath(folderPath);
    if (!folder) {
      await this.app.vault.createFolder(folderPath);
    }
  }

  startAutoBackup(): void {
    if (!this.config.autoBackup) return;

    this.intervalId = window.setInterval(
      () => this.createBackup(),
      this.config.intervalMinutes * 60 * 1000
    );
  }

  stopAutoBackup(): void {
    if (this.intervalId) {
      window.clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }
}
```

### Step 4: Data Validation
```typescript
// src/services/validation-service.ts
import { App, TFile } from 'obsidian';

export interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
}

interface ValidationError {
  file: string;
  type: 'frontmatter' | 'link' | 'syntax' | 'encoding';
  message: string;
}

interface ValidationWarning {
  file: string;
  type: string;
  message: string;
}

export class ValidationService {
  constructor(private app: App) {}

  async validateVault(): Promise<ValidationResult> {
    const result: ValidationResult = {
      valid: true,
      errors: [],
      warnings: [],
    };

    const files = this.app.vault.getMarkdownFiles();

    for (const file of files) {
      await this.validateFile(file, result);
    }

    result.valid = result.errors.length === 0;
    return result;
  }

  private async validateFile(file: TFile, result: ValidationResult): Promise<void> {
    try {
      const content = await this.app.vault.read(file);

      // Validate frontmatter
      this.validateFrontmatter(file, content, result);

      // Validate links
      this.validateLinks(file, result);

      // Check for binary content
      if (this.containsBinaryContent(content)) {
        result.warnings.push({
          file: file.path,
          type: 'encoding',
          message: 'File may contain binary content',
        });
      }
    } catch (error) {
      result.errors.push({
        file: file.path,
        type: 'syntax',
        message: `Failed to read file: ${(error as Error).message}`,
      });
    }
  }

  private validateFrontmatter(
    file: TFile,
    content: string,
    result: ValidationResult
  ): void {
    const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);

    if (frontmatterMatch) {
      try {
        // Check for common YAML issues
        const yaml = frontmatterMatch[1];

        // Check for tabs (YAML prefers spaces)
        if (yaml.includes('\t')) {
          result.warnings.push({
            file: file.path,
            type: 'frontmatter',
            message: 'Frontmatter contains tabs (use spaces)',
          });
        }

        // Check for unquoted special characters
        if (/:\s*[@#!]/.test(yaml)) {
          result.warnings.push({
            file: file.path,
            type: 'frontmatter',
            message: 'Frontmatter values may need quoting',
          });
        }
      } catch (error) {
        result.errors.push({
          file: file.path,
          type: 'frontmatter',
          message: `Invalid frontmatter: ${(error as Error).message}`,
        });
      }
    }
  }

  private validateLinks(file: TFile, result: ValidationResult): void {
    const cache = this.app.metadataCache.getFileCache(file);
    if (!cache?.links) return;

    for (const link of cache.links) {
      const linkedFile = this.app.metadataCache.getFirstLinkpathDest(
        link.link,
        file.path
      );

      if (!linkedFile) {
        result.warnings.push({
          file: file.path,
          type: 'link',
          message: `Broken link: [[${link.link}]]`,
        });
      }
    }
  }

  private containsBinaryContent(content: string): boolean {
    // Check for null bytes or high concentration of non-printable chars
    const nullByteCount = (content.match(/\0/g) || []).length;
    return nullByteCount > 0;
  }
}
```

### Step 5: Data Sync Patterns
```typescript
// src/services/sync-service.ts
import { App, TFile } from 'obsidian';

export interface SyncStatus {
  lastSync: string | null;
  pendingChanges: number;
  conflicts: SyncConflict[];
}

export interface SyncConflict {
  path: string;
  localModified: number;
  remoteModified: number;
  resolution: 'local' | 'remote' | 'manual' | null;
}

export class SyncService {
  private syncHashes = new Map<string, string>();
  private pendingChanges = new Set<string>();

  constructor(private app: App) {}

  async trackChange(file: TFile): Promise<void> {
    const hash = await this.hashFile(file);
    const previousHash = this.syncHashes.get(file.path);

    if (previousHash && previousHash !== hash) {
      this.pendingChanges.add(file.path);
    }

    this.syncHashes.set(file.path, hash);
  }

  async getChangedFiles(): Promise<TFile[]> {
    const changedFiles: TFile[] = [];

    for (const path of this.pendingChanges) {
      const file = this.app.vault.getAbstractFileByPath(path);
      if (file instanceof TFile) {
        changedFiles.push(file);
      }
    }

    return changedFiles;
  }

  markSynced(path: string): void {
    this.pendingChanges.delete(path);
  }

  getStatus(): SyncStatus {
    return {
      lastSync: null, // Implement timestamp tracking
      pendingChanges: this.pendingChanges.size,
      conflicts: [],
    };
  }

  private async hashFile(file: TFile): Promise<string> {
    const content = await this.app.vault.read(file);
    const encoder = new TextEncoder();
    const data = encoder.encode(content);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('').substring(0, 16);
  }
}
```


## Complete Examples

### Quick Backup Command
```typescript
this.addCommand({
  id: 'quick-backup',
  name: 'Create Quick Backup',
  callback: async () => {
    const backupService = new BackupService(this.app, {
      autoBackup: false,
      intervalMinutes: 60,
      maxBackups: 5,
      backupFolder: '_backups',
      includePluginData: true,
    });
    await backupService.createBackup();
  },
});
```


## Data Categories

| Data Type | Storage Location | Backup Priority |
|-----------|-----------------|-----------------|
| Notes (md) | Vault root | Critical |
| Attachments | Vault/attachments | Critical |
| Plugin settings | .obsidian/plugins/*/data.json | High |
| Plugin cache | .obsidian/plugins/*/cache/ | Low |
| Vault config | .obsidian/*.json | Medium |
