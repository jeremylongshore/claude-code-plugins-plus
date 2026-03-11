# Evernote SDK Patterns - Implementation Guide

> Full implementation details for the parent SKILL.md.


## Core Patterns

### Pattern 1: Search with NoteFilter

```javascript
const Evernote = require('evernote');

async function searchNotes(noteStore, searchQuery, maxResults = 100) {
  // Create filter with search grammar
  const filter = new Evernote.NoteStore.NoteFilter({
    words: searchQuery,
    ascending: false,
    order: Evernote.Types.NoteSortOrder.UPDATED
  });

  // Specify which metadata to return
  const spec = new Evernote.NoteStore.NotesMetadataResultSpec({
    includeTitle: true,
    includeContentLength: true,
    includeCreated: true,
    includeUpdated: true,
    includeTagGuids: true,
    includeNotebookGuid: true
  });

  // Find notes (offset, maxNotes)
  const result = await noteStore.findNotesMetadata(filter, 0, maxResults, spec);

  console.log(`Found ${result.totalNotes} notes (returned ${result.notes.length})`);
  return result;
}

// Usage examples:
// searchNotes(noteStore, 'tag:important notebook:Work');
// searchNotes(noteStore, 'intitle:meeting created:day-7');
// searchNotes(noteStore, 'todo:false'); // Unchecked todos
```

### Pattern 2: Search Grammar Queries

```javascript
// Build complex search queries
function buildSearchQuery(options = {}) {
  const parts = [];

  if (options.notebook) {
    parts.push(`notebook:"${options.notebook}"`);
  }

  if (options.tags && options.tags.length) {
    options.tags.forEach(tag => parts.push(`tag:"${tag}"`));
  }

  if (options.excludeTags && options.excludeTags.length) {
    options.excludeTags.forEach(tag => parts.push(`-tag:"${tag}"`));
  }

  if (options.createdAfter) {
    parts.push(`created:${formatDateForSearch(options.createdAfter)}`);
  }

  if (options.updatedAfter) {
    parts.push(`updated:${formatDateForSearch(options.updatedAfter)}`);
  }

  if (options.inTitle) {
    parts.push(`intitle:"${options.inTitle}"`);
  }

  if (options.hasAttachments) {
    parts.push('resource:*');
  }

  if (options.hasTodos !== undefined) {
    parts.push(`todo:${options.hasTodos}`);
  }

  if (options.text) {
    parts.push(options.text);
  }

  // Use 'any:' for OR logic, default is AND
  if (options.matchAny) {
    return 'any: ' + parts.join(' ');
  }

  return parts.join(' ');
}

function formatDateForSearch(date) {
  // Format: YYYYMMDD
  return date.toISOString().slice(0, 10).replace(/-/g, '');
}

// Example: Find notes tagged "urgent" in "Work" notebook from last week
const query = buildSearchQuery({
  notebook: 'Work',
  tags: ['urgent'],
  createdAfter: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
});
// Result: 'notebook:"Work" tag:"urgent" created:20240115'
```

### Pattern 3: Paginated Note Retrieval

```javascript
async function* getAllNotesMetadata(noteStore, filter, spec, pageSize = 100) {
  let offset = 0;
  let hasMore = true;

  while (hasMore) {
    const result = await noteStore.findNotesMetadata(filter, offset, pageSize, spec);

    for (const note of result.notes) {
      yield note;
    }

    offset += result.notes.length;
    hasMore = offset < result.totalNotes;

    console.log(`Progress: ${offset}/${result.totalNotes}`);
  }
}

// Usage with async iteration
async function processAllNotes(noteStore) {
  const filter = new Evernote.NoteStore.NoteFilter({ words: 'tag:process' });
  const spec = new Evernote.NoteStore.NotesMetadataResultSpec({
    includeTitle: true,
    includeUpdated: true
  });

  for await (const note of getAllNotesMetadata(noteStore, filter, spec)) {
    console.log(`Processing: ${note.title}`);
    // Process each note
  }
}
```

### Pattern 4: Efficient Note Content Retrieval

```javascript
async function getNoteWithOptions(noteStore, noteGuid, options = {}) {
  const {
    withContent = true,
    withResources = false,
    withRecognition = false,
    withAlternateData = false
  } = options;

  return noteStore.getNote(
    noteGuid,
    withContent,
    withResources,        // Include binary resource data
    withRecognition,      // Include OCR data
    withAlternateData     // Include alternate representations
  );
}

// Only get content (most common)
const note = await getNoteWithOptions(noteStore, guid);

// Get note with all attachments
const noteWithFiles = await getNoteWithOptions(noteStore, guid, {
  withResources: true
});
```

### Pattern 5: Creating Notes with Attachments

```javascript
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

async function createNoteWithAttachment(noteStore, title, content, filePath) {
  const Evernote = require('evernote');

  // Read file and compute hash
  const fileBuffer = fs.readFileSync(filePath);
  const hash = crypto.createHash('md5').update(fileBuffer).digest('hex');
  const mimeType = getMimeType(filePath);

  // Create resource (attachment)
  const resource = new Evernote.Types.Resource();
  resource.data = new Evernote.Types.Data();
  resource.data.body = fileBuffer;
  resource.data.size = fileBuffer.length;
  resource.data.bodyHash = Buffer.from(hash, 'hex');
  resource.mime = mimeType;

  // Set file attributes
  resource.attributes = new Evernote.Types.ResourceAttributes();
  resource.attributes.fileName = path.basename(filePath);

  // Create ENML with embedded resource
  const enml = `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note>
  ${content}
  <en-media type="${mimeType}" hash="${hash}"/>
</en-note>`;

  // Create note
  const note = new Evernote.Types.Note();
  note.title = title;
  note.content = enml;
  note.resources = [resource];

  return noteStore.createNote(note);
}

function getMimeType(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  const mimeTypes = {
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.pdf': 'application/pdf',
    '.txt': 'text/plain',
    '.doc': 'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  };
  return mimeTypes[ext] || 'application/octet-stream';
}
```

### Pattern 6: Working with Tags

```javascript
async function getOrCreateTag(noteStore, tagName) {
  // Try to find existing tag
  const tags = await noteStore.listTags();
  const existing = tags.find(t =>
    t.name.toLowerCase() === tagName.toLowerCase()
  );

  if (existing) {
    return existing;
  }

  // Create new tag
  const tag = new Evernote.Types.Tag();
  tag.name = tagName;
  return noteStore.createTag(tag);
}

async function addTagsToNote(noteStore, noteGuid, tagNames) {
  // Get current note
  const note = await noteStore.getNote(noteGuid, false, false, false, false);

  // Resolve tag names to GUIDs
  const tagGuids = await Promise.all(
    tagNames.map(async name => {
      const tag = await getOrCreateTag(noteStore, name);
      return tag.guid;
    })
  );

  // Merge with existing tags
  const existingTags = note.tagGuids || [];
  const allTags = [...new Set([...existingTags, ...tagGuids])];

  // Update note
  note.tagGuids = allTags;
  return noteStore.updateNote(note);
}
```

### Pattern 7: Notebook Operations

```javascript
async function getOrCreateNotebook(noteStore, notebookName, stack = null) {
  const notebooks = await noteStore.listNotebooks();
  const existing = notebooks.find(n =>
    n.name.toLowerCase() === notebookName.toLowerCase()
  );

  if (existing) {
    return existing;
  }

  const notebook = new Evernote.Types.Notebook();
  notebook.name = notebookName;
  if (stack) {
    notebook.stack = stack;
  }

  return noteStore.createNotebook(notebook);
}

async function moveNoteToNotebook(noteStore, noteGuid, notebookName) {
  const notebook = await getOrCreateNotebook(noteStore, notebookName);
  const note = await noteStore.getNote(noteGuid, false, false, false, false);

  note.notebookGuid = notebook.guid;
  return noteStore.updateNote(note);
}
```

### Pattern 8: Error Handling Wrapper

```javascript
class EvernoteError extends Error {
  constructor(originalError) {
    super(originalError.message || 'Evernote API error');
    this.name = 'EvernoteError';
    this.code = originalError.errorCode;
    this.parameter = originalError.parameter;
    this.rateLimitDuration = originalError.rateLimitDuration;
    this.original = originalError;
  }

  get isRateLimit() {
    return this.code === Evernote.Errors.EDAMErrorCode.RATE_LIMIT_REACHED;
  }

  get isNotFound() {
    return this.code === Evernote.Errors.EDAMErrorCode.UNKNOWN;
  }

  get isInvalidData() {
    return this.code === Evernote.Errors.EDAMErrorCode.BAD_DATA_FORMAT;
  }
}

async function withErrorHandling(operation) {
  try {
    return await operation();
  } catch (error) {
    if (error.errorCode !== undefined) {
      throw new EvernoteError(error);
    }
    throw error;
  }
}

// Usage
try {
  const note = await withErrorHandling(() =>
    noteStore.getNote(guid, true, false, false, false)
  );
} catch (error) {
  if (error instanceof EvernoteError && error.isRateLimit) {
    console.log(`Rate limited. Retry in ${error.rateLimitDuration}s`);
  }
}
```

### Pattern 9: Batch Operations with Rate Limit Handling

```javascript
async function batchProcess(items, operation, options = {}) {
  const {
    concurrency = 1,  // Keep at 1 to avoid rate limits
    delayMs = 100,
    onProgress = () => {}
  } = options;

  const results = [];
  let processed = 0;

  for (const item of items) {
    try {
      const result = await operation(item);
      results.push({ success: true, item, result });
    } catch (error) {
      if (error.rateLimitDuration) {
        // Wait for rate limit to clear
        console.log(`Rate limited, waiting ${error.rateLimitDuration}s...`);
        await sleep(error.rateLimitDuration * 1000);
        // Retry
        const result = await operation(item);
        results.push({ success: true, item, result });
      } else {
        results.push({ success: false, item, error });
      }
    }

    processed++;
    onProgress(processed, items.length);

    // Add delay between operations
    if (processed < items.length) {
      await sleep(delayMs);
    }
  }

  return results;
}

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

// Usage
const notes = await searchNotes(noteStore, 'tag:archive');
const results = await batchProcess(
  notes.notes,
  note => noteStore.deleteNote(note.guid),
  {
    delayMs: 200,
    onProgress: (done, total) => console.log(`${done}/${total}`)
  }
);
```
