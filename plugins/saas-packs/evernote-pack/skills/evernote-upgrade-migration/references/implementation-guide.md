# Evernote Upgrade & Migration - Implementation Guide

> Full implementation details for the parent SKILL.md.

## Detailed Instructions

### Step 1: Check Current Version

```bash
npm list evernote

npm view evernote versions

npm outdated evernote
```

### Step 2: Review Breaking Changes

```javascript
// SDK 1.x -> 2.x Breaking Changes

// 1. Client initialization changed
// OLD (1.x):
var Evernote = require('evernote').Evernote;
var client = new Evernote.Client({
  consumerKey: 'key',
  consumerSecret: 'secret',
  sandbox: true
});

// NEW (2.x):
const Evernote = require('evernote');
const client = new Evernote.Client({
  consumerKey: 'key',
  consumerSecret: 'secret',
  sandbox: true
});

// 2. API calls return Promises (not callbacks)
// OLD (1.x):
noteStore.listNotebooks(function(err, notebooks) {
  if (err) console.error(err);
  else console.log(notebooks);
});

// NEW (2.x):
noteStore.listNotebooks()
  .then(notebooks => console.log(notebooks))
  .catch(err => console.error(err));

// Or with async/await:
const notebooks = await noteStore.listNotebooks();

// 3. Type constructors
// OLD (1.x):
var note = new Evernote.Note();

// NEW (2.x):
const note = new Evernote.Types.Note();
```

### Step 3: Migration Script

```javascript
// scripts/migrate-to-v2.js
const fs = require('fs');
const path = require('path');
const glob = require('glob');

const migrations = [
  // Client import
  {
    pattern: /require\(['"]evernote['"]\)\.Evernote/g,
    replacement: "require('evernote')"
  },

  // Type constructors
  {
    pattern: /new Evernote\.Note\(\)/g,
    replacement: 'new Evernote.Types.Note()'
  },
  {
    pattern: /new Evernote\.Notebook\(\)/g,
    replacement: 'new Evernote.Types.Notebook()'
  },
  {
    pattern: /new Evernote\.Tag\(\)/g,
    replacement: 'new Evernote.Types.Tag()'
  },
  {
    pattern: /new Evernote\.Resource\(\)/g,
    replacement: 'new Evernote.Types.Resource()'
  },

  // NoteFilter
  {
    pattern: /new Evernote\.NoteFilter\(\)/g,
    replacement: 'new Evernote.NoteStore.NoteFilter()'
  },

  // NotesMetadataResultSpec
  {
    pattern: /new Evernote\.NotesMetadataResultSpec\(\)/g,
    replacement: 'new Evernote.NoteStore.NotesMetadataResultSpec()'
  }
];

function migrateFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  let modified = false;

  for (const { pattern, replacement } of migrations) {
    if (pattern.test(content)) {
      content = content.replace(pattern, replacement);
      modified = true;
    }
  }

  if (modified) {
    // Create backup
    fs.writeFileSync(`${filePath}.bak`, fs.readFileSync(filePath));
    // Write migrated file
    fs.writeFileSync(filePath, content);
    console.log(`Migrated: ${filePath}`);
    return true;
  }

  return false;
}

// Run migration
const files = glob.sync('src/**/*.js');
let migratedCount = 0;

for (const file of files) {
  if (migrateFile(file)) {
    migratedCount++;
  }
}

console.log(`\nMigration complete. ${migratedCount} files modified.`);
console.log('Backup files created with .bak extension');
```

### Step 4: Convert Callbacks to Promises

```javascript
// utils/promisify-legacy.js

/**
 * Wrapper for legacy callback-based code
 */
function promisifyNoteStore(noteStore) {
  const promisified = {};

  // List of methods that need promisification
  const methods = [
    'listNotebooks',
    'getNotebook',
    'createNotebook',
    'updateNotebook',
    'listTags',
    'getTag',
    'createTag',
    'getNote',
    'createNote',
    'updateNote',
    'deleteNote',
    'findNotesMetadata',
    'getNoteContent',
    'getResource'
  ];

  for (const method of methods) {
    promisified[method] = (...args) => {
      return new Promise((resolve, reject) => {
        noteStore[method](...args, (err, result) => {
          if (err) reject(err);
          else resolve(result);
        });
      });
    };
  }

  return promisified;
}

module.exports = { promisifyNoteStore };
```

### Step 5: Upgrade Dependencies

```bash
npm install evernote@latest

npm install @types/evernote@latest --save-dev

npm update
```

### Step 6: Test Suite Updates

```javascript
// tests/migration-tests.js
const assert = require('assert');
const Evernote = require('evernote');

describe('SDK v2 Migration Tests', () => {
  let client;
  let noteStore;

  before(() => {
    client = new Evernote.Client({
      token: process.env.EVERNOTE_ACCESS_TOKEN,
      sandbox: true
    });
    noteStore = client.getNoteStore();
  });

  describe('Type Constructors', () => {
    it('should create Note using Types namespace', () => {
      const note = new Evernote.Types.Note();
      assert(note);
      note.title = 'Test';
      assert.equal(note.title, 'Test');
    });

    it('should create NoteFilter using NoteStore namespace', () => {
      const filter = new Evernote.NoteStore.NoteFilter({
        words: 'test'
      });
      assert(filter);
      assert.equal(filter.words, 'test');
    });
  });

  describe('Promise-based API', () => {
    it('should return Promise from listNotebooks', async () => {
      const result = noteStore.listNotebooks();
      assert(result instanceof Promise);
    });

    it('should resolve notebooks array', async () => {
      const notebooks = await noteStore.listNotebooks();
      assert(Array.isArray(notebooks));
    });
  });

  describe('Error Handling', () => {
    it('should reject with EDAMUserException for invalid data', async () => {
      const note = new Evernote.Types.Note();
      // Missing required fields

      try {
        await noteStore.createNote(note);
        assert.fail('Should have thrown');
      } catch (error) {
        assert(error.errorCode !== undefined);
      }
    });
  });
});
```

### Step 7: Compatibility Layer

```javascript
// utils/compatibility.js

/**
 * Compatibility layer for gradual migration
 * Supports both callback and Promise patterns
 */
class CompatibleNoteStore {
  constructor(noteStore) {
    this.store = noteStore;
  }

  listNotebooks(callback) {
    const promise = this.store.listNotebooks();

    if (callback) {
      // Legacy callback support
      promise
        .then(result => callback(null, result))
        .catch(error => callback(error, null));
      return;
    }

    return promise;
  }

  getNote(guid, withContent, withResources, withRecognition, withAlternate, callback) {
    const promise = this.store.getNote(
      guid,
      withContent,
      withResources,
      withRecognition,
      withAlternate
    );

    if (callback) {
      promise
        .then(result => callback(null, result))
        .catch(error => callback(error, null));
      return;
    }

    return promise;
  }

  createNote(note, callback) {
    const promise = this.store.createNote(note);

    if (callback) {
      promise
        .then(result => callback(null, result))
        .catch(error => callback(error, null));
      return;
    }

    return promise;
  }

  // Add more methods as needed
}

module.exports = CompatibleNoteStore;
```

### Step 8: Deprecation Warnings

```javascript
// utils/deprecation-warnings.js

const deprecations = new Set();

function warnOnce(message) {
  if (!deprecations.has(message)) {
    deprecations.add(message);
    console.warn(`[DEPRECATION WARNING] ${message}`);
  }
}

// Proxy to add deprecation warnings
function wrapWithDeprecationWarnings(noteStore) {
  return new Proxy(noteStore, {
    get(target, prop) {
      // Warn about deprecated patterns
      if (prop === 'getNote') {
        return (...args) => {
          if (args.length === 6 && typeof args[5] === 'function') {
            warnOnce(
              'Callback pattern is deprecated. ' +
              'Use Promise: noteStore.getNote(...).then(note => ...)'
            );
          }
          return target[prop](...args);
        };
      }

      return target[prop];
    }
  });
}

module.exports = { wrapWithDeprecationWarnings };
```


## SDK Version History

| Version | Node.js | Key Changes |
|---------|---------|-------------|
| 2.0.x | 10+ | Promise-based API, ES6 modules |
| 1.25.x | 8+ | Legacy callback pattern |
| 1.x | 6+ | Original SDK |


## Migration Checklist

```markdown


## SDK v2 Migration Checklist

### Pre-Migration
- [ ] Backup current codebase
- [ ] Document current SDK version
- [ ] Review breaking changes
- [ ] Set up test environment

### Code Changes
- [ ] Update import statements
- [ ] Update type constructors (Types namespace)
- [ ] Update filter constructors (NoteStore namespace)
- [ ] Convert callbacks to Promises/async-await
- [ ] Update error handling for Promise rejections

### Testing
- [ ] Run migration script on test branch
- [ ] Execute full test suite
- [ ] Test OAuth flow end-to-end
- [ ] Test note CRUD operations
- [ ] Test search functionality
- [ ] Verify error handling

### Deployment
- [ ] Deploy to staging
- [ ] Run integration tests
- [ ] Monitor for errors
- [ ] Deploy to production
- [ ] Monitor metrics

### Cleanup
- [ ] Remove compatibility layers (after validation period)
- [ ] Remove backup files
- [ ] Update documentation
- [ ] Archive migration scripts
```
