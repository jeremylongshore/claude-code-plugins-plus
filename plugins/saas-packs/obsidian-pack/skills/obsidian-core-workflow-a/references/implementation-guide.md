# Obsidian Core Workflow A: Vault Operations - Implementation Guide

> Full implementation details for the parent SKILL.md.

## Detailed Instructions

### Step 1: Working with Files (TFile)
```typescript
import { TFile, TFolder, TAbstractFile, Vault } from 'obsidian';

export class FileOperations {
  constructor(private vault: Vault) {}

  // Get all markdown files
  getAllNotes(): TFile[] {
    return this.vault.getMarkdownFiles();
  }

  // Get file by path
  getNote(path: string): TFile | null {
    const file = this.vault.getAbstractFileByPath(path);
    return file instanceof TFile ? file : null;
  }

  // Read file content
  async readNote(file: TFile): Promise<string> {
    return this.vault.read(file);
  }

  // Read file content as cached (faster, may be stale)
  readNoteCached(file: TFile): string | null {
    return this.vault.cachedRead(file);
  }

  // Modify file content
  async writeNote(file: TFile, content: string): Promise<void> {
    await this.vault.modify(file, content);
  }

  // Create new note
  async createNote(path: string, content: string): Promise<TFile> {
    // Ensure parent folder exists
    const folderPath = path.substring(0, path.lastIndexOf('/'));
    if (folderPath) {
      await this.ensureFolder(folderPath);
    }
    return this.vault.create(path, content);
  }

  // Delete note
  async deleteNote(file: TFile, trash: boolean = true): Promise<void> {
    if (trash) {
      await this.vault.trash(file, false); // Move to system trash
    } else {
      await this.vault.delete(file);
    }
  }

  // Rename/move note
  async renameNote(file: TFile, newPath: string): Promise<void> {
    await this.vault.rename(file, newPath);
  }

  // Ensure folder exists
  private async ensureFolder(path: string): Promise<void> {
    const folder = this.vault.getAbstractFileByPath(path);
    if (!folder) {
      await this.vault.createFolder(path);
    }
  }
}
```

### Step 2: Frontmatter Operations
```typescript
import { App, TFile, parseYaml, stringifyYaml } from 'obsidian';

export class FrontmatterService {
  constructor(private app: App) {}

  // Extract frontmatter from note
  getFrontmatter(file: TFile): Record<string, any> | null {
    const cache = this.app.metadataCache.getFileCache(file);
    return cache?.frontmatter || null;
  }

  // Parse frontmatter from content
  parseFrontmatter(content: string): { frontmatter: Record<string, any> | null; body: string } {
    const match = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
    if (!match) {
      return { frontmatter: null, body: content };
    }

    try {
      const frontmatter = parseYaml(match[1]);
      return { frontmatter, body: match[2] };
    } catch {
      return { frontmatter: null, body: content };
    }
  }

  // Update frontmatter in file
  async updateFrontmatter(
    file: TFile,
    updates: Record<string, any>
  ): Promise<void> {
    const content = await this.app.vault.read(file);
    const { frontmatter, body } = this.parseFrontmatter(content);

    const newFrontmatter = { ...frontmatter, ...updates };
    const yamlContent = stringifyYaml(newFrontmatter);
    const newContent = `---\n${yamlContent}---\n${body}`;

    await this.app.vault.modify(file, newContent);
  }

  // Remove frontmatter property
  async removeFrontmatterProperty(file: TFile, key: string): Promise<void> {
    const content = await this.app.vault.read(file);
    const { frontmatter, body } = this.parseFrontmatter(content);

    if (frontmatter && key in frontmatter) {
      delete frontmatter[key];
      const yamlContent = stringifyYaml(frontmatter);
      const newContent = `---\n${yamlContent}---\n${body}`;
      await this.app.vault.modify(file, newContent);
    }
  }

  // Get all files with specific frontmatter property
  getFilesWithProperty(property: string, value?: any): TFile[] {
    return this.app.vault.getMarkdownFiles().filter(file => {
      const fm = this.getFrontmatter(file);
      if (!fm || !(property in fm)) return false;
      if (value !== undefined) return fm[property] === value;
      return true;
    });
  }
}
```

### Step 3: Link and Tag Operations
```typescript
import { App, TFile, CachedMetadata } from 'obsidian';

export class LinkService {
  constructor(private app: App) {}

  // Get all links from a file
  getOutgoingLinks(file: TFile): string[] {
    const cache = this.app.metadataCache.getFileCache(file);
    const links: string[] = [];

    // Wiki-style links [[link]]
    cache?.links?.forEach(link => {
      links.push(link.link);
    });

    // Embeds ![[embed]]
    cache?.embeds?.forEach(embed => {
      links.push(embed.link);
    });

    return [...new Set(links)];
  }

  // Get backlinks (files linking to this file)
  getBacklinks(file: TFile): TFile[] {
    const backlinks: TFile[] = [];
    const resolvedLinks = this.app.metadataCache.resolvedLinks;

    for (const [sourcePath, links] of Object.entries(resolvedLinks)) {
      if (file.path in links) {
        const sourceFile = this.app.vault.getAbstractFileByPath(sourcePath);
        if (sourceFile instanceof TFile) {
          backlinks.push(sourceFile);
        }
      }
    }

    return backlinks;
  }

  // Get all tags from a file
  getTags(file: TFile): string[] {
    const cache = this.app.metadataCache.getFileCache(file);
    const tags: string[] = [];

    // Tags in content
    cache?.tags?.forEach(tag => {
      tags.push(tag.tag);
    });

    // Tags in frontmatter
    const fmTags = cache?.frontmatter?.tags;
    if (Array.isArray(fmTags)) {
      fmTags.forEach(tag => {
        tags.push(tag.startsWith('#') ? tag : `#${tag}`);
      });
    }

    return [...new Set(tags)];
  }

  // Get all files with specific tag
  getFilesWithTag(tag: string): TFile[] {
    const normalizedTag = tag.startsWith('#') ? tag : `#${tag}`;

    return this.app.vault.getMarkdownFiles().filter(file => {
      const tags = this.getTags(file);
      return tags.includes(normalizedTag);
    });
  }

  // Update link in file (when target is renamed)
  async updateLink(
    file: TFile,
    oldLink: string,
    newLink: string
  ): Promise<void> {
    let content = await this.app.vault.read(file);

    // Update wiki links
    content = content.replace(
      new RegExp(`\\[\\[${this.escapeRegex(oldLink)}(\\|[^\\]]*)?\\]\\]`, 'g'),
      (match, alias) => `[[${newLink}${alias || ''}]]`
    );

    await this.app.vault.modify(file, content);
  }

  private escapeRegex(str: string): string {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }
}
```

### Step 4: Search and Query
```typescript
import { App, TFile, prepareFuzzySearch, prepareSimpleSearch } from 'obsidian';

export class SearchService {
  constructor(private app: App) {}

  // Fuzzy search file names
  searchFileNames(query: string): TFile[] {
    const search = prepareFuzzySearch(query);
    const results: { file: TFile; score: number }[] = [];

    for (const file of this.app.vault.getMarkdownFiles()) {
      const match = search(file.basename);
      if (match) {
        results.push({ file, score: match.score });
      }
    }

    return results
      .sort((a, b) => b.score - a.score)
      .map(r => r.file);
  }

  // Simple text search in content
  async searchContent(query: string): Promise<{ file: TFile; matches: number }[]> {
    const search = prepareSimpleSearch(query);
    const results: { file: TFile; matches: number }[] = [];

    for (const file of this.app.vault.getMarkdownFiles()) {
      const content = await this.app.vault.cachedRead(file);
      const match = search(content);
      if (match) {
        results.push({ file, matches: match.matches.length });
      }
    }

    return results.sort((a, b) => b.matches - a.matches);
  }

  // Search by multiple criteria
  async advancedSearch(criteria: {
    folder?: string;
    tags?: string[];
    frontmatter?: Record<string, any>;
    content?: string;
  }): Promise<TFile[]> {
    let files = this.app.vault.getMarkdownFiles();

    // Filter by folder
    if (criteria.folder) {
      files = files.filter(f => f.path.startsWith(criteria.folder!));
    }

    // Filter by tags
    if (criteria.tags?.length) {
      const linkService = new LinkService(this.app);
      files = files.filter(f => {
        const fileTags = linkService.getTags(f);
        return criteria.tags!.every(tag =>
          fileTags.includes(tag.startsWith('#') ? tag : `#${tag}`)
        );
      });
    }

    // Filter by frontmatter
    if (criteria.frontmatter) {
      const fmService = new FrontmatterService(this.app);
      files = files.filter(f => {
        const fm = fmService.getFrontmatter(f);
        if (!fm) return false;
        return Object.entries(criteria.frontmatter!).every(
          ([key, value]) => fm[key] === value
        );
      });
    }

    // Filter by content
    if (criteria.content) {
      const search = prepareSimpleSearch(criteria.content);
      const contentMatches: TFile[] = [];
      for (const file of files) {
        const content = await this.app.vault.cachedRead(file);
        if (search(content)) {
          contentMatches.push(file);
        }
      }
      files = contentMatches;
    }

    return files;
  }
}
```


## Complete Examples

### Complete Note Template
```typescript
async function createNoteFromTemplate(
  app: App,
  templatePath: string,
  newPath: string,
  variables: Record<string, string>
): Promise<TFile> {
  const template = app.vault.getAbstractFileByPath(templatePath);
  if (!(template instanceof TFile)) {
    throw new Error('Template not found');
  }

  let content = await app.vault.read(template);

  // Replace variables
  for (const [key, value] of Object.entries(variables)) {
    content = content.replace(new RegExp(`{{${key}}}`, 'g'), value);
  }

  return app.vault.create(newPath, content);
}
```
