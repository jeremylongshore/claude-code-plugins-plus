# Evernote Data Handling - Implementation Guide

> Full implementation details for the parent SKILL.md.

## Detailed Instructions

### Step 1: Data Schema Design

```sql
-- PostgreSQL schema for Evernote data

-- Users
CREATE TABLE evernote_users (
  id SERIAL PRIMARY KEY,
  evernote_user_id BIGINT UNIQUE NOT NULL,
  username VARCHAR(255),
  email VARCHAR(255),
  privilege INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Notebooks
CREATE TABLE notebooks (
  guid UUID PRIMARY KEY,
  user_id INTEGER REFERENCES evernote_users(id),
  name VARCHAR(255) NOT NULL,
  stack VARCHAR(255),
  default_notebook BOOLEAN DEFAULT FALSE,
  created_at BIGINT,
  updated_at BIGINT,
  synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  INDEX idx_notebooks_user (user_id),
  INDEX idx_notebooks_stack (stack)
);

-- Tags
CREATE TABLE tags (
  guid UUID PRIMARY KEY,
  user_id INTEGER REFERENCES evernote_users(id),
  name VARCHAR(255) NOT NULL,
  parent_guid UUID REFERENCES tags(guid),
  update_sequence_num INTEGER,
  synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  INDEX idx_tags_user (user_id),
  INDEX idx_tags_parent (parent_guid),
  UNIQUE(user_id, name)
);

-- Notes
CREATE TABLE notes (
  guid UUID PRIMARY KEY,
  user_id INTEGER REFERENCES evernote_users(id),
  notebook_guid UUID REFERENCES notebooks(guid),
  title VARCHAR(255) NOT NULL,
  content TEXT, -- ENML content
  content_hash BYTEA,
  content_length INTEGER,
  created_at BIGINT,
  updated_at BIGINT,
  deleted_at BIGINT,
  active BOOLEAN DEFAULT TRUE,
  update_sequence_num INTEGER,
  synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  INDEX idx_notes_user (user_id),
  INDEX idx_notes_notebook (notebook_guid),
  INDEX idx_notes_updated (updated_at),
  INDEX idx_notes_active (active)
);

-- Note-Tag relationship
CREATE TABLE note_tags (
  note_guid UUID REFERENCES notes(guid),
  tag_guid UUID REFERENCES tags(guid),
  PRIMARY KEY (note_guid, tag_guid)
);

-- Resources (attachments)
CREATE TABLE resources (
  guid UUID PRIMARY KEY,
  note_guid UUID REFERENCES notes(guid),
  mime_type VARCHAR(100) NOT NULL,
  width INTEGER,
  height INTEGER,
  duration INTEGER,
  data_hash BYTEA NOT NULL,
  data_size INTEGER NOT NULL,
  file_name VARCHAR(255),
  source_url TEXT,
  storage_path VARCHAR(500), -- Path to stored file
  synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  INDEX idx_resources_note (note_guid),
  INDEX idx_resources_hash (data_hash)
);

-- Sync state
CREATE TABLE sync_state (
  user_id INTEGER PRIMARY KEY REFERENCES evernote_users(id),
  last_update_count INTEGER DEFAULT 0,
  last_sync_time BIGINT,
  full_sync_required BOOLEAN DEFAULT TRUE
);
```

### Step 2: ENML Content Processing

```javascript
// services/enml-processor.js
const cheerio = require('cheerio');
const crypto = require('crypto');

class ENMLProcessor {
  /**
   * Parse ENML content
   */
  parse(enml) {
    const $ = cheerio.load(enml, {
      xmlMode: true,
      decodeEntities: true
    });

    return {
      $,
      title: $('title').text(),
      text: this.extractText($),
      todos: this.extractTodos($),
      links: this.extractLinks($),
      media: this.extractMedia($),
      checksum: this.computeChecksum(enml)
    };
  }

  /**
   * Extract plain text from ENML
   */
  extractText($) {
    // Remove en-media and en-crypt elements
    $('en-media, en-crypt').remove();

    // Get text content
    return $('en-note')
      .text()
      .replace(/\s+/g, ' ')
      .trim();
  }

  /**
   * Extract todos
   */
  extractTodos($) {
    const todos = [];

    $('en-todo').each((i, el) => {
      const checked = $(el).attr('checked') === 'true';
      // Get text after the todo element
      const text = $(el).next().text().trim() ||
                   $(el).parent().text().trim();

      todos.push({
        index: i,
        checked,
        text: text.slice(0, 200) // Limit length
      });
    });

    return todos;
  }

  /**
   * Extract links
   */
  extractLinks($) {
    const links = [];

    $('a[href]').each((i, el) => {
      const href = $(el).attr('href');
      const text = $(el).text();

      // Skip javascript: and mailto: links
      if (href && !href.startsWith('javascript:') && !href.startsWith('mailto:')) {
        links.push({ href, text });
      }
    });

    return links;
  }

  /**
   * Extract media references
   */
  extractMedia($) {
    const media = [];

    $('en-media').each((i, el) => {
      media.push({
        type: $(el).attr('type'),
        hash: $(el).attr('hash'),
        width: parseInt($(el).attr('width')) || null,
        height: parseInt($(el).attr('height')) || null
      });
    });

    return media;
  }

  /**
   * Compute content checksum
   */
  computeChecksum(content) {
    return crypto.createHash('md5').update(content).digest('hex');
  }

  /**
   * Validate ENML structure
   */
  validate(enml) {
    const errors = [];

    if (!enml.includes('<?xml version="1.0"')) {
      errors.push('Missing XML declaration');
    }

    if (!enml.includes('<!DOCTYPE en-note')) {
      errors.push('Missing DOCTYPE');
    }

    if (!enml.includes('<en-note>') || !enml.includes('</en-note>')) {
      errors.push('Missing en-note root element');
    }

    return { valid: errors.length === 0, errors };
  }

  /**
   * Sanitize content for storage
   */
  sanitize(enml) {
    const $ = cheerio.load(enml, { xmlMode: true });

    // Remove potentially sensitive data
    $('en-crypt').each((i, el) => {
      $(el).replaceWith('[Encrypted content]');
    });

    return $.html();
  }
}

module.exports = ENMLProcessor;
```

### Step 3: Resource (Attachment) Handling

```javascript
// services/resource-handler.js
const fs = require('fs').promises;
const path = require('path');
const crypto = require('crypto');

class ResourceHandler {
  constructor(options) {
    this.storageRoot = options.storageRoot || './storage/resources';
    this.maxSizeBytes = options.maxSizeBytes || 100 * 1024 * 1024; // 100MB
  }

  /**
   * Store resource from Evernote
   */
  async storeResource(resource, userId) {
    const hash = Buffer.from(resource.data.bodyHash).toString('hex');
    const storagePath = this.getStoragePath(userId, hash, resource.mime);

    // Ensure directory exists
    await fs.mkdir(path.dirname(storagePath), { recursive: true });

    // Write file
    await fs.writeFile(storagePath, resource.data.body);

    return {
      storagePath,
      hash,
      size: resource.data.size,
      mime: resource.mime
    };
  }

  /**
   * Get storage path for resource
   */
  getStoragePath(userId, hash, mimeType) {
    const ext = this.getExtension(mimeType);
    // Shard by first 2 chars of hash for performance
    const shard = hash.substring(0, 2);
    return path.join(this.storageRoot, userId.toString(), shard, `${hash}${ext}`);
  }

  /**
   * Get file extension from MIME type
   */
  getExtension(mimeType) {
    const map = {
      'image/png': '.png',
      'image/jpeg': '.jpg',
      'image/gif': '.gif',
      'application/pdf': '.pdf',
      'audio/wav': '.wav',
      'audio/mpeg': '.mp3'
    };
    return map[mimeType] || '';
  }

  /**
   * Retrieve stored resource
   */
  async getResource(storagePath) {
    try {
      const data = await fs.readFile(storagePath);
      return { data, exists: true };
    } catch (error) {
      if (error.code === 'ENOENT') {
        return { data: null, exists: false };
      }
      throw error;
    }
  }

  /**
   * Delete resource
   */
  async deleteResource(storagePath) {
    try {
      await fs.unlink(storagePath);
      return { deleted: true };
    } catch (error) {
      if (error.code === 'ENOENT') {
        return { deleted: false, reason: 'not_found' };
      }
      throw error;
    }
  }

  /**
   * Calculate storage usage for user
   */
  async getUserStorageUsage(userId) {
    const userDir = path.join(this.storageRoot, userId.toString());
    let totalSize = 0;
    let fileCount = 0;

    async function walkDir(dir) {
      try {
        const entries = await fs.readdir(dir, { withFileTypes: true });
        for (const entry of entries) {
          const fullPath = path.join(dir, entry.name);
          if (entry.isDirectory()) {
            await walkDir(fullPath);
          } else {
            const stat = await fs.stat(fullPath);
            totalSize += stat.size;
            fileCount++;
          }
        }
      } catch (error) {
        if (error.code !== 'ENOENT') throw error;
      }
    }

    await walkDir(userDir);

    return {
      totalBytes: totalSize,
      totalMB: (totalSize / (1024 * 1024)).toFixed(2),
      fileCount
    };
  }
}

module.exports = ResourceHandler;
```

### Step 4: Sync Data Manager

```javascript
// services/sync-manager.js

class SyncManager {
  constructor(db, noteStore) {
    this.db = db;
    this.noteStore = noteStore;
  }

  /**
   * Process sync chunk and update local data
   */
  async processSyncChunk(userId, chunk) {
    const results = {
      notes: { created: 0, updated: 0, deleted: 0 },
      notebooks: { created: 0, updated: 0, deleted: 0 },
      tags: { created: 0, updated: 0, deleted: 0 }
    };

    // Process notebooks
    if (chunk.notebooks) {
      for (const notebook of chunk.notebooks) {
        await this.upsertNotebook(userId, notebook);
        results.notebooks.updated++;
      }
    }

    // Process expunged notebooks
    if (chunk.expungedNotebooks) {
      for (const guid of chunk.expungedNotebooks) {
        await this.deleteNotebook(guid);
        results.notebooks.deleted++;
      }
    }

    // Process tags
    if (chunk.tags) {
      for (const tag of chunk.tags) {
        await this.upsertTag(userId, tag);
        results.tags.updated++;
      }
    }

    // Process expunged tags
    if (chunk.expungedTags) {
      for (const guid of chunk.expungedTags) {
        await this.deleteTag(guid);
        results.tags.deleted++;
      }
    }

    // Process notes
    if (chunk.notes) {
      for (const note of chunk.notes) {
        const isNew = await this.upsertNote(userId, note);
        if (isNew) results.notes.created++;
        else results.notes.updated++;
      }
    }

    // Process expunged notes
    if (chunk.expungedNotes) {
      for (const guid of chunk.expungedNotes) {
        await this.deleteNote(guid);
        results.notes.deleted++;
      }
    }

    return results;
  }

  /**
   * Upsert notebook
   */
  async upsertNotebook(userId, notebook) {
    return this.db.query(`
      INSERT INTO notebooks (guid, user_id, name, stack, default_notebook, created_at, updated_at, synced_at)
      VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
      ON CONFLICT (guid) DO UPDATE SET
        name = EXCLUDED.name,
        stack = EXCLUDED.stack,
        default_notebook = EXCLUDED.default_notebook,
        updated_at = EXCLUDED.updated_at,
        synced_at = NOW()
    `, [notebook.guid, userId, notebook.name, notebook.stack, notebook.defaultNotebook,
        notebook.serviceCreated, notebook.serviceUpdated]);
  }

  /**
   * Upsert note (without content)
   */
  async upsertNote(userId, note) {
    const existing = await this.db.query(
      'SELECT guid FROM notes WHERE guid = $1',
      [note.guid]
    );

    await this.db.query(`
      INSERT INTO notes (guid, user_id, notebook_guid, title, content_hash, content_length,
                         created_at, updated_at, active, update_sequence_num, synced_at)
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW())
      ON CONFLICT (guid) DO UPDATE SET
        notebook_guid = EXCLUDED.notebook_guid,
        title = EXCLUDED.title,
        content_hash = EXCLUDED.content_hash,
        content_length = EXCLUDED.content_length,
        updated_at = EXCLUDED.updated_at,
        active = EXCLUDED.active,
        update_sequence_num = EXCLUDED.update_sequence_num,
        synced_at = NOW()
    `, [note.guid, userId, note.notebookGuid, note.title,
        note.contentHash, note.contentLength, note.created,
        note.updated, note.active !== false, note.updateSequenceNum]);

    // Update tags
    if (note.tagGuids) {
      await this.updateNoteTags(note.guid, note.tagGuids);
    }

    return existing.rows.length === 0; // Return true if new
  }

  /**
   * Update note tags
   */
  async updateNoteTags(noteGuid, tagGuids) {
    await this.db.query('DELETE FROM note_tags WHERE note_guid = $1', [noteGuid]);

    if (tagGuids.length > 0) {
      const values = tagGuids.map((tagGuid, i) =>
        `($1, $${i + 2})`
      ).join(', ');

      await this.db.query(
        `INSERT INTO note_tags (note_guid, tag_guid) VALUES ${values}`,
        [noteGuid, ...tagGuids]
      );
    }
  }

  /**
   * Delete note (soft delete)
   */
  async deleteNote(guid) {
    return this.db.query(
      'UPDATE notes SET active = FALSE, deleted_at = $1, synced_at = NOW() WHERE guid = $2',
      [Date.now(), guid]
    );
  }

  /**
   * Update sync state
   */
  async updateSyncState(userId, updateCount) {
    return this.db.query(`
      INSERT INTO sync_state (user_id, last_update_count, last_sync_time, full_sync_required)
      VALUES ($1, $2, $3, FALSE)
      ON CONFLICT (user_id) DO UPDATE SET
        last_update_count = EXCLUDED.last_update_count,
        last_sync_time = EXCLUDED.last_sync_time,
        full_sync_required = FALSE
    `, [userId, updateCount, Date.now()]);
  }
}

module.exports = SyncManager;
```

### Step 5: Data Export

```javascript
// services/data-export.js
const archiver = require('archiver');

class DataExporter {
  constructor(db, resourceHandler) {
    this.db = db;
    this.resourceHandler = resourceHandler;
  }

  /**
   * Export all user data
   */
  async exportUserData(userId, outputStream) {
    const archive = archiver('zip', { zlib: { level: 9 } });
    archive.pipe(outputStream);

    // Export notes
    const notes = await this.db.query(
      'SELECT * FROM notes WHERE user_id = $1 AND active = TRUE',
      [userId]
    );

    // Add notes as JSON
    archive.append(JSON.stringify(notes.rows, null, 2), {
      name: 'notes.json'
    });

    // Export notebooks
    const notebooks = await this.db.query(
      'SELECT * FROM notebooks WHERE user_id = $1',
      [userId]
    );
    archive.append(JSON.stringify(notebooks.rows, null, 2), {
      name: 'notebooks.json'
    });

    // Export tags
    const tags = await this.db.query(
      'SELECT * FROM tags WHERE user_id = $1',
      [userId]
    );
    archive.append(JSON.stringify(tags.rows, null, 2), {
      name: 'tags.json'
    });

    // Export resources
    const resources = await this.db.query(`
      SELECT r.* FROM resources r
      JOIN notes n ON r.note_guid = n.guid
      WHERE n.user_id = $1
    `, [userId]);

    for (const resource of resources.rows) {
      if (resource.storage_path) {
        const { data, exists } = await this.resourceHandler.getResource(
          resource.storage_path
        );
        if (exists) {
          archive.append(data, {
            name: `resources/${resource.guid}${path.extname(resource.storage_path)}`
          });
        }
      }
    }

    await archive.finalize();
  }

  /**
   * Delete all user data (GDPR right to erasure)
   */
  async deleteUserData(userId) {
    // Delete in order of dependencies
    await this.db.query('DELETE FROM note_tags WHERE note_guid IN (SELECT guid FROM notes WHERE user_id = $1)', [userId]);
    await this.db.query('DELETE FROM resources WHERE note_guid IN (SELECT guid FROM notes WHERE user_id = $1)', [userId]);
    await this.db.query('DELETE FROM notes WHERE user_id = $1', [userId]);
    await this.db.query('DELETE FROM tags WHERE user_id = $1', [userId]);
    await this.db.query('DELETE FROM notebooks WHERE user_id = $1', [userId]);
    await this.db.query('DELETE FROM sync_state WHERE user_id = $1', [userId]);
    await this.db.query('DELETE FROM evernote_users WHERE id = $1', [userId]);

    // Delete stored resources
    const userStoragePath = path.join(this.resourceHandler.storageRoot, userId.toString());
    await fs.rm(userStoragePath, { recursive: true, force: true });

    return { deleted: true };
  }
}

module.exports = DataExporter;
```


## Evernote Data Model

```
User
├── Notebooks (max 250-1000)
│   └── Notes (max 100,000)
│       ├── Content (ENML format)
│       ├── Resources (attachments)
│       ├── Tags (many-to-many)
│       └── Attributes (metadata)
├── Tags (max 100,000)
└── Saved Searches (max 100)
```


## Data Handling Checklist

```markdown
- [ ] Database schema created with proper indexes
- [ ] ENML content validation implemented
- [ ] Resource storage configured
- [ ] Sync state management implemented
- [ ] Data export capability
- [ ] Data deletion capability (GDPR)
- [ ] Backup procedures documented
```
