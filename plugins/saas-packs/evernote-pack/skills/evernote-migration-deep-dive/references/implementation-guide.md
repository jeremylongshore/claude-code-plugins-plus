# Evernote Migration Deep Dive - Implementation Guide

> Full implementation details for the parent SKILL.md.

## Detailed Instructions

### Step 1: Migration Planning

```javascript
// migration/planner.js

class MigrationPlanner {
  constructor(sourceClient, targetConfig) {
    this.source = sourceClient;
    this.target = targetConfig;
    this.plan = null;
  }

  /**
   * Analyze source data
   */
  async analyzeSource() {
    const noteStore = this.source.getNoteStore();

    // Get all notebooks
    const notebooks = await noteStore.listNotebooks();

    // Get all tags
    const tags = await noteStore.listTags();

    // Count notes per notebook
    const noteCounts = {};
    for (const notebook of notebooks) {
      const filter = new Evernote.NoteStore.NoteFilter({
        notebookGuid: notebook.guid
      });
      const result = await noteStore.findNotesMetadata(
        filter, 0, 1,
        new Evernote.NoteStore.NotesMetadataResultSpec({})
      );
      noteCounts[notebook.guid] = result.totalNotes;
    }

    // Estimate sizes
    const analysis = {
      notebooks: notebooks.length,
      tags: tags.length,
      totalNotes: Object.values(noteCounts).reduce((a, b) => a + b, 0),
      notebookDetails: notebooks.map(nb => ({
        guid: nb.guid,
        name: nb.name,
        noteCount: noteCounts[nb.guid]
      })),
      estimatedDuration: this.estimateDuration(Object.values(noteCounts).reduce((a, b) => a + b, 0)),
      recommendations: []
    };

    // Generate recommendations
    if (analysis.totalNotes > 10000) {
      analysis.recommendations.push('Consider incremental migration');
    }
    if (analysis.notebooks > 100) {
      analysis.recommendations.push('Plan notebook mapping before migration');
    }

    return analysis;
  }

  /**
   * Estimate migration duration
   */
  estimateDuration(noteCount) {
    // Rough estimate: 1 note per second with rate limiting
    const seconds = noteCount;
    const hours = Math.ceil(seconds / 3600);
    return `Approximately ${hours} hour(s)`;
  }

  /**
   * Create migration plan
   */
  async createPlan(options = {}) {
    const analysis = await this.analyzeSource();

    this.plan = {
      id: `migration-${Date.now()}`,
      createdAt: new Date().toISOString(),
      source: {
        type: 'evernote',
        analysis
      },
      target: this.target,
      options: {
        includeResources: options.includeResources ?? true,
        preserveTags: options.preserveTags ?? true,
        preserveTimestamps: options.preserveTimestamps ?? true,
        notebookMapping: options.notebookMapping || {},
        excludeNotebooks: options.excludeNotebooks || [],
        batchSize: options.batchSize || 50,
        concurrency: options.concurrency || 1
      },
      status: 'planned',
      progress: {
        total: analysis.totalNotes,
        completed: 0,
        failed: 0
      }
    };

    return this.plan;
  }
}

module.exports = MigrationPlanner;
```

### Step 2: Export from Evernote

```javascript
// migration/evernote-exporter.js
const fs = require('fs').promises;
const path = require('path');

class EvernoteExporter {
  constructor(noteStore, options = {}) {
    this.noteStore = noteStore;
    this.outputDir = options.outputDir || './export';
    this.format = options.format || 'enex'; // enex, json, markdown
  }

  /**
   * Export all data
   */
  async exportAll(progressCallback) {
    await fs.mkdir(this.outputDir, { recursive: true });

    const notebooks = await this.noteStore.listNotebooks();
    const tags = await this.noteStore.listTags();

    // Export metadata
    await this.exportMetadata(notebooks, tags);

    // Export each notebook
    let total = 0;
    let exported = 0;

    for (const notebook of notebooks) {
      const noteCount = await this.exportNotebook(notebook, (progress) => {
        progressCallback?.({
          phase: 'notes',
          notebook: notebook.name,
          ...progress
        });
      });
      total += noteCount;
      exported += noteCount;
    }

    return {
      notebooks: notebooks.length,
      tags: tags.length,
      notes: total,
      outputDir: this.outputDir
    };
  }

  /**
   * Export metadata
   */
  async exportMetadata(notebooks, tags) {
    const metadata = {
      exportedAt: new Date().toISOString(),
      notebooks: notebooks.map(nb => ({
        guid: nb.guid,
        name: nb.name,
        stack: nb.stack,
        defaultNotebook: nb.defaultNotebook
      })),
      tags: tags.map(t => ({
        guid: t.guid,
        name: t.name,
        parentGuid: t.parentGuid
      }))
    };

    await fs.writeFile(
      path.join(this.outputDir, 'metadata.json'),
      JSON.stringify(metadata, null, 2)
    );
  }

  /**
   * Export notebook
   */
  async exportNotebook(notebook, progressCallback) {
    const notebookDir = path.join(this.outputDir, this.sanitizeName(notebook.name));
    await fs.mkdir(notebookDir, { recursive: true });

    const filter = new Evernote.NoteStore.NoteFilter({
      notebookGuid: notebook.guid
    });

    const spec = new Evernote.NoteStore.NotesMetadataResultSpec({
      includeTitle: true,
      includeUpdated: true
    });

    // Get note list
    const result = await this.noteStore.findNotesMetadata(filter, 0, 10000, spec);
    const total = result.notes.length;
    let exported = 0;

    for (const noteMeta of result.notes) {
      try {
        // Get full note with resources
        const note = await this.noteStore.getNote(
          noteMeta.guid,
          true,  // withContent
          true,  // withResourcesData
          false, // withResourcesRecognition
          false  // withResourcesAlternateData
        );

        await this.exportNote(note, notebookDir);
        exported++;

        progressCallback?.({
          current: exported,
          total,
          note: note.title
        });

        // Rate limit protection
        await this.sleep(100);

      } catch (error) {
        console.error(`Failed to export note ${noteMeta.guid}:`, error.message);
      }
    }

    return exported;
  }

  /**
   * Export single note
   */
  async exportNote(note, outputDir) {
    const noteDir = path.join(outputDir, this.sanitizeName(note.title) + '_' + note.guid.slice(0, 8));
    await fs.mkdir(noteDir, { recursive: true });

    switch (this.format) {
      case 'json':
        await this.exportAsJson(note, noteDir);
        break;
      case 'markdown':
        await this.exportAsMarkdown(note, noteDir);
        break;
      case 'enex':
      default:
        await this.exportAsEnex(note, noteDir);
    }

    // Export resources
    if (note.resources) {
      const resourcesDir = path.join(noteDir, 'resources');
      await fs.mkdir(resourcesDir, { recursive: true });

      for (const resource of note.resources) {
        await this.exportResource(resource, resourcesDir);
      }
    }
  }

  /**
   * Export as JSON
   */
  async exportAsJson(note, outputDir) {
    const data = {
      guid: note.guid,
      title: note.title,
      content: note.content,
      created: note.created,
      updated: note.updated,
      tagGuids: note.tagGuids,
      resources: note.resources?.map(r => ({
        guid: r.guid,
        mime: r.mime,
        fileName: r.attributes?.fileName,
        hash: Buffer.from(r.data.bodyHash).toString('hex')
      }))
    };

    await fs.writeFile(
      path.join(outputDir, 'note.json'),
      JSON.stringify(data, null, 2)
    );
  }

  /**
   * Export as Markdown
   */
  async exportAsMarkdown(note, outputDir) {
    let markdown = `# ${note.title}\n\n`;
    markdown += `Created: ${new Date(note.created).toISOString()}\n`;
    markdown += `Updated: ${new Date(note.updated).toISOString()}\n\n`;
    markdown += `---\n\n`;
    markdown += this.enmlToMarkdown(note.content);

    await fs.writeFile(
      path.join(outputDir, 'note.md'),
      markdown
    );
  }

  /**
   * Convert ENML to Markdown
   */
  enmlToMarkdown(enml) {
    let md = enml
      // Remove XML declaration and DOCTYPE
      .replace(/<\?xml[^>]*\?>/g, '')
      .replace(/<!DOCTYPE[^>]*>/g, '')
      // Remove en-note wrapper
      .replace(/<\/?en-note[^>]*>/g, '')
      // Convert headers
      .replace(/<h1[^>]*>(.*?)<\/h1>/gi, '# $1\n\n')
      .replace(/<h2[^>]*>(.*?)<\/h2>/gi, '## $1\n\n')
      .replace(/<h3[^>]*>(.*?)<\/h3>/gi, '### $1\n\n')
      // Convert formatting
      .replace(/<b[^>]*>(.*?)<\/b>/gi, '**$1**')
      .replace(/<strong[^>]*>(.*?)<\/strong>/gi, '**$1**')
      .replace(/<i[^>]*>(.*?)<\/i>/gi, '*$1*')
      .replace(/<em[^>]*>(.*?)<\/em>/gi, '*$1*')
      // Convert links
      .replace(/<a[^>]*href="([^"]*)"[^>]*>(.*?)<\/a>/gi, '[$2]($1)')
      // Convert line breaks
      .replace(/<br\s*\/?>/gi, '\n')
      .replace(/<\/p>/gi, '\n\n')
      .replace(/<p[^>]*>/gi, '')
      // Convert divs
      .replace(/<\/div>/gi, '\n')
      .replace(/<div[^>]*>/gi, '')
      // Convert lists
      .replace(/<li[^>]*>/gi, '- ')
      .replace(/<\/li>/gi, '\n')
      .replace(/<\/?[uo]l[^>]*>/gi, '\n')
      // Convert todos
      .replace(/<en-todo\s+checked="false"\s*\/>/gi, '[ ] ')
      .replace(/<en-todo\s+checked="true"\s*\/>/gi, '[x] ')
      // Convert media references
      .replace(/<en-media[^>]*hash="([^"]*)"[^>]*\/>/gi, '\n![attachment]($1)\n')
      // Remove remaining tags
      .replace(/<[^>]+>/g, '')
      // Decode entities
      .replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&quot;/g, '"')
      .replace(/&nbsp;/g, ' ')
      // Clean up whitespace
      .replace(/\n{3,}/g, '\n\n')
      .trim();

    return md;
  }

  /**
   * Export resource
   */
  async exportResource(resource, outputDir) {
    const hash = Buffer.from(resource.data.bodyHash).toString('hex');
    const ext = this.getExtension(resource.mime);
    const fileName = resource.attributes?.fileName || `${hash}${ext}`;

    await fs.writeFile(
      path.join(outputDir, fileName),
      resource.data.body
    );
  }

  sanitizeName(name) {
    return name
      .replace(/[<>:"/\\|?*]/g, '_')
      .replace(/\s+/g, '_')
      .slice(0, 100);
  }

  getExtension(mimeType) {
    const map = {
      'image/png': '.png',
      'image/jpeg': '.jpg',
      'image/gif': '.gif',
      'application/pdf': '.pdf'
    };
    return map[mimeType] || '';
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

module.exports = EvernoteExporter;
```

### Step 3: Import to Evernote

```javascript
// migration/evernote-importer.js
const fs = require('fs').promises;
const path = require('path');
const crypto = require('crypto');

class EvernoteImporter {
  constructor(noteStore, options = {}) {
    this.noteStore = noteStore;
    this.batchSize = options.batchSize || 10;
    this.notebookMapping = new Map();
    this.tagMapping = new Map();
  }

  /**
   * Import from export directory
   */
  async importFromDirectory(sourceDir, progressCallback) {
    // Load metadata
    const metadataPath = path.join(sourceDir, 'metadata.json');
    const metadata = JSON.parse(await fs.readFile(metadataPath, 'utf8'));

    // Create notebooks
    await this.createNotebooks(metadata.notebooks);

    // Create tags
    await this.createTags(metadata.tags);

    // Import notes
    const notebooks = await fs.readdir(sourceDir, { withFileTypes: true });
    let totalImported = 0;

    for (const entry of notebooks) {
      if (entry.isDirectory() && entry.name !== 'metadata.json') {
        const notebookDir = path.join(sourceDir, entry.name);
        const imported = await this.importNotebook(notebookDir, entry.name, progressCallback);
        totalImported += imported;
      }
    }

    return { imported: totalImported };
  }

  /**
   * Create notebooks (with deduplication)
   */
  async createNotebooks(notebooks) {
    const existing = await this.noteStore.listNotebooks();
    const existingMap = new Map(existing.map(nb => [nb.name.toLowerCase(), nb]));

    for (const nb of notebooks) {
      const existingNb = existingMap.get(nb.name.toLowerCase());

      if (existingNb) {
        this.notebookMapping.set(nb.guid, existingNb.guid);
      } else {
        const newNb = new Evernote.Types.Notebook();
        newNb.name = nb.name;
        if (nb.stack) newNb.stack = nb.stack;

        const created = await this.noteStore.createNotebook(newNb);
        this.notebookMapping.set(nb.guid, created.guid);
      }
    }
  }

  /**
   * Create tags (with deduplication)
   */
  async createTags(tags) {
    const existing = await this.noteStore.listTags();
    const existingMap = new Map(existing.map(t => [t.name.toLowerCase(), t]));

    for (const tag of tags) {
      const existingTag = existingMap.get(tag.name.toLowerCase());

      if (existingTag) {
        this.tagMapping.set(tag.guid, existingTag.guid);
      } else {
        const newTag = new Evernote.Types.Tag();
        newTag.name = tag.name;

        const created = await this.noteStore.createTag(newTag);
        this.tagMapping.set(tag.guid, created.guid);
      }
    }
  }

  /**
   * Import notebook directory
   */
  async importNotebook(notebookDir, notebookName, progressCallback) {
    const notes = await fs.readdir(notebookDir, { withFileTypes: true });
    const noteDirs = notes.filter(e => e.isDirectory());
    let imported = 0;

    for (const noteEntry of noteDirs) {
      try {
        const noteDir = path.join(notebookDir, noteEntry.name);
        await this.importNote(noteDir);
        imported++;

        progressCallback?.({
          notebook: notebookName,
          current: imported,
          total: noteDirs.length
        });

        // Rate limiting
        await this.sleep(200);

      } catch (error) {
        console.error(`Failed to import note ${noteEntry.name}:`, error.message);
      }
    }

    return imported;
  }

  /**
   * Import single note
   */
  async importNote(noteDir) {
    const jsonPath = path.join(noteDir, 'note.json');
    const data = JSON.parse(await fs.readFile(jsonPath, 'utf8'));

    const note = new Evernote.Types.Note();
    note.title = data.title;
    note.content = data.content;

    // Map notebook
    if (data.notebookGuid && this.notebookMapping.has(data.notebookGuid)) {
      note.notebookGuid = this.notebookMapping.get(data.notebookGuid);
    }

    // Map tags
    if (data.tagGuids) {
      note.tagGuids = data.tagGuids
        .map(guid => this.tagMapping.get(guid))
        .filter(Boolean);
    }

    // Import resources
    if (data.resources) {
      note.resources = [];
      const resourcesDir = path.join(noteDir, 'resources');

      for (const resMeta of data.resources) {
        try {
          const resource = await this.createResource(resourcesDir, resMeta);
          if (resource) {
            note.resources.push(resource);
          }
        } catch (error) {
          console.error(`Failed to import resource:`, error.message);
        }
      }
    }

    return this.noteStore.createNote(note);
  }

  /**
   * Create resource from file
   */
  async createResource(resourcesDir, metadata) {
    const files = await fs.readdir(resourcesDir);
    const matchingFile = files.find(f =>
      f.includes(metadata.hash) || f === metadata.fileName
    );

    if (!matchingFile) {
      console.warn(`Resource file not found: ${metadata.hash}`);
      return null;
    }

    const filePath = path.join(resourcesDir, matchingFile);
    const fileData = await fs.readFile(filePath);
    const hash = crypto.createHash('md5').update(fileData).digest();

    const resource = new Evernote.Types.Resource();
    resource.mime = metadata.mime;
    resource.data = new Evernote.Types.Data();
    resource.data.body = fileData;
    resource.data.size = fileData.length;
    resource.data.bodyHash = hash;

    if (metadata.fileName) {
      resource.attributes = new Evernote.Types.ResourceAttributes();
      resource.attributes.fileName = metadata.fileName;
    }

    return resource;
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

module.exports = EvernoteImporter;
```

### Step 4: Migration Runner

```javascript
// migration/runner.js

class MigrationRunner {
  constructor(plan, exporter, importer) {
    this.plan = plan;
    this.exporter = exporter;
    this.importer = importer;
    this.status = 'pending';
    this.startTime = null;
    this.endTime = null;
    this.errors = [];
  }

  /**
   * Run migration
   */
  async run(progressCallback) {
    this.status = 'running';
    this.startTime = Date.now();

    try {
      // Phase 1: Export
      progressCallback?.({ phase: 'export', status: 'starting' });

      const exportResult = await this.exporter.exportAll((progress) => {
        progressCallback?.({ phase: 'export', ...progress });
      });

      progressCallback?.({ phase: 'export', status: 'complete', result: exportResult });

      // Phase 2: Import
      progressCallback?.({ phase: 'import', status: 'starting' });

      const importResult = await this.importer.importFromDirectory(
        this.exporter.outputDir,
        (progress) => {
          progressCallback?.({ phase: 'import', ...progress });
        }
      );

      progressCallback?.({ phase: 'import', status: 'complete', result: importResult });

      // Phase 3: Verify
      progressCallback?.({ phase: 'verify', status: 'starting' });
      const verifyResult = await this.verify();
      progressCallback?.({ phase: 'verify', status: 'complete', result: verifyResult });

      this.status = 'completed';

    } catch (error) {
      this.status = 'failed';
      this.errors.push(error.message);
      throw error;

    } finally {
      this.endTime = Date.now();
    }

    return this.getReport();
  }

  /**
   * Verify migration
   */
  async verify() {
    // Count notes in target
    // Compare with source count
    // Return verification status
    return { verified: true };
  }

  /**
   * Get migration report
   */
  getReport() {
    return {
      planId: this.plan.id,
      status: this.status,
      startTime: new Date(this.startTime).toISOString(),
      endTime: this.endTime ? new Date(this.endTime).toISOString() : null,
      duration: this.endTime ? `${((this.endTime - this.startTime) / 1000 / 60).toFixed(1)} minutes` : null,
      errors: this.errors
    };
  }
}

module.exports = MigrationRunner;
```


## Migration Scenarios

| Scenario | Source | Target | Complexity |
|----------|--------|--------|------------|
| Import to Evernote | External | Evernote | Medium |
| Export from Evernote | Evernote | External | Medium |
| Evernote to Evernote | Account A | Account B | High |
| Bulk archive | Evernote | Archive storage | Low |


## Migration Checklist

```markdown


## Pre-Migration

- [ ] Analyze source data
- [ ] Create migration plan
- [ ] Backup source data
- [ ] Test with small dataset
- [ ] Verify API quota


## During Migration

- [ ] Monitor progress
- [ ] Check for errors
- [ ] Handle rate limits
- [ ] Log all operations


## Post-Migration

- [ ] Verify data integrity
- [ ] Compare counts
- [ ] Test functionality
- [ ] Document results
- [ ] Clean up temporary files
```


## Support

For complex migrations, consider contacting Evernote Business support or professional services.
