# Evernote Core Workflow B: Search & Retrieval - Implementation Guide

> Full implementation details for the parent SKILL.md.

## Detailed Instructions

### Step 1: Search Service Foundation

```javascript
// services/search-service.js
const Evernote = require('evernote');

class SearchService {
  constructor(noteStore) {
    this.noteStore = noteStore;
  }

  /**
   * Basic text search across all notes
   */
  async search(query, options = {}) {
    const {
      maxResults = 50,
      offset = 0,
      sortOrder = 'UPDATED',
      ascending = false
    } = options;

    const filter = new Evernote.NoteStore.NoteFilter({
      words: query,
      ascending,
      order: Evernote.Types.NoteSortOrder[sortOrder]
    });

    const spec = new Evernote.NoteStore.NotesMetadataResultSpec({
      includeTitle: true,
      includeContentLength: true,
      includeCreated: true,
      includeUpdated: true,
      includeTagGuids: true,
      includeNotebookGuid: true,
      includeAttributes: true
    });

    const result = await this.noteStore.findNotesMetadata(
      filter,
      offset,
      maxResults,
      spec
    );

    return {
      notes: result.notes,
      totalNotes: result.totalNotes,
      hasMore: offset + result.notes.length < result.totalNotes
    };
  }

  /**
   * Search within a specific notebook
   */
  async searchInNotebook(notebookGuid, query, maxResults = 50) {
    const filter = new Evernote.NoteStore.NoteFilter({
      notebookGuid,
      words: query
    });

    const spec = this.getDefaultResultSpec();
    return this.noteStore.findNotesMetadata(filter, 0, maxResults, spec);
  }

  /**
   * Search by tags (AND logic)
   */
  async searchByTags(tagGuids, maxResults = 50) {
    const filter = new Evernote.NoteStore.NoteFilter({
      tagGuids,
      ascending: false,
      order: Evernote.Types.NoteSortOrder.UPDATED
    });

    const spec = this.getDefaultResultSpec();
    return this.noteStore.findNotesMetadata(filter, 0, maxResults, spec);
  }

  getDefaultResultSpec() {
    return new Evernote.NoteStore.NotesMetadataResultSpec({
      includeTitle: true,
      includeCreated: true,
      includeUpdated: true,
      includeTagGuids: true,
      includeNotebookGuid: true
    });
  }
}

module.exports = SearchService;
```

### Step 2: Advanced Search Grammar Builder

```javascript
class QueryBuilder {
  constructor() {
    this.parts = [];
  }

  /**
   * Search in specific notebook
   */
  notebook(name) {
    this.parts.push(`notebook:"${name}"`);
    return this;
  }

  /**
   * Search for notes with tag
   */
  tag(name) {
    this.parts.push(`tag:"${name}"`);
    return this;
  }

  /**
   * Exclude notes with tag
   */
  excludeTag(name) {
    this.parts.push(`-tag:"${name}"`);
    return this;
  }

  /**
   * Search in note title
   */
  intitle(text) {
    this.parts.push(`intitle:"${text}"`);
    return this;
  }

  /**
   * Created on or after date
   */
  createdAfter(date) {
    this.parts.push(`created:${this.formatDate(date)}`);
    return this;
  }

  /**
   * Created before date
   */
  createdBefore(date) {
    this.parts.push(`-created:${this.formatDate(date)}`);
    return this;
  }

  /**
   * Updated on or after date
   */
  updatedAfter(date) {
    this.parts.push(`updated:${this.formatDate(date)}`);
    return this;
  }

  /**
   * Notes with uncompleted todos
   */
  hasUncompletedTodos() {
    this.parts.push('todo:false');
    return this;
  }

  /**
   * Notes with completed todos
   */
  hasCompletedTodos() {
    this.parts.push('todo:true');
    return this;
  }

  /**
   * Notes with any todos
   */
  hasTodos() {
    this.parts.push('todo:*');
    return this;
  }

  /**
   * Notes with attachments
   */
  hasAttachments() {
    this.parts.push('resource:*');
    return this;
  }

  /**
   * Notes with images
   */
  hasImages() {
    this.parts.push('resource:image/*');
    return this;
  }

  /**
   * Notes with PDFs
   */
  hasPDFs() {
    this.parts.push('resource:application/pdf');
    return this;
  }

  /**
   * Notes with encryption
   */
  hasEncryption() {
    this.parts.push('encryption:');
    return this;
  }

  /**
   * Author filter
   */
  author(name) {
    this.parts.push(`author:"${name}"`);
    return this;
  }

  /**
   * Source filter (web clip, email, etc.)
   */
  source(type) {
    this.parts.push(`source:${type}`);
    return this;
  }

  /**
   * Free text search
   */
  text(query) {
    this.parts.push(query);
    return this;
  }

  /**
   * Exact phrase search
   */
  phrase(text) {
    this.parts.push(`"${text}"`);
    return this;
  }

  /**
   * Wildcard search (suffix only)
   */
  wildcard(prefix) {
    this.parts.push(`${prefix}*`);
    return this;
  }

  /**
   * Negate next condition
   */
  not() {
    this._negate = true;
    return this;
  }

  /**
   * Match ANY condition (default is ALL)
   */
  any() {
    this._any = true;
    return this;
  }

  /**
   * Relative date helpers
   */
  today() {
    return this.createdAfter('day');
  }

  thisWeek() {
    return this.createdAfter('week');
  }

  thisMonth() {
    return this.createdAfter('month');
  }

  lastNDays(n) {
    this.parts.push(`created:day-${n}`);
    return this;
  }

  formatDate(input) {
    if (typeof input === 'string') {
      // Relative dates like 'day', 'week', 'month', 'year'
      return input;
    }
    // Absolute date: YYYYMMDD
    return input.toISOString().slice(0, 10).replace(/-/g, '');
  }

  /**
   * Build final query string
   */
  build() {
    let query = this.parts.join(' ');
    if (this._any) {
      query = 'any: ' + query;
    }
    return query;
  }

  /**
   * Reset builder
   */
  reset() {
    this.parts = [];
    this._any = false;
    this._negate = false;
    return this;
  }
}

module.exports = QueryBuilder;
```

### Step 3: Paginated Search Results

```javascript
class SearchService {
  // ... previous methods ...

  /**
   * Paginated search with cursor-based iteration
   */
  async *paginatedSearch(query, pageSize = 50) {
    const filter = new Evernote.NoteStore.NoteFilter({
      words: query,
      ascending: false,
      order: Evernote.Types.NoteSortOrder.UPDATED
    });

    const spec = this.getDefaultResultSpec();
    let offset = 0;
    let hasMore = true;

    while (hasMore) {
      const result = await this.noteStore.findNotesMetadata(
        filter,
        offset,
        pageSize,
        spec
      );

      for (const note of result.notes) {
        yield note;
      }

      offset += result.notes.length;
      hasMore = offset < result.totalNotes;
    }
  }

  /**
   * Get all matching notes (careful with large result sets)
   */
  async getAllMatching(query, maxTotal = 1000) {
    const allNotes = [];
    const pageSize = 100;

    for await (const note of this.paginatedSearch(query, pageSize)) {
      allNotes.push(note);
      if (allNotes.length >= maxTotal) break;
    }

    return allNotes;
  }

  /**
   * Search with full note content (slower, use sparingly)
   */
  async searchWithContent(query, maxResults = 20) {
    const metadata = await this.search(query, { maxResults });

    const notesWithContent = await Promise.all(
      metadata.notes.map(async note => {
        const fullNote = await this.noteStore.getNote(
          note.guid,
          true,  // withContent
          false, // withResourcesData
          false, // withResourcesRecognition
          false  // withResourcesAlternateData
        );
        return fullNote;
      })
    );

    return notesWithContent;
  }
}
```

### Step 4: Related Notes Discovery

```javascript
class SearchService {
  // ... previous methods ...

  /**
   * Find notes related to a given note
   */
  async findRelatedNotes(noteGuid) {
    const relatedResult = await this.noteStore.findRelated(
      new Evernote.NoteStore.RelatedQuery({
        noteGuid
      }),
      new Evernote.NoteStore.RelatedResultSpec({
        maxNotes: 10,
        maxNotebooks: 3,
        maxTags: 10
      })
    );

    return {
      notes: relatedResult.notes || [],
      notebooks: relatedResult.notebooks || [],
      tags: relatedResult.tags || []
    };
  }

  /**
   * Find notes related to text content
   */
  async findRelatedToText(text) {
    const relatedResult = await this.noteStore.findRelated(
      new Evernote.NoteStore.RelatedQuery({
        plainText: text
      }),
      new Evernote.NoteStore.RelatedResultSpec({
        maxNotes: 10
      })
    );

    return relatedResult.notes || [];
  }

  /**
   * Get notes in same notebook
   */
  async getNotebookNotes(notebookGuid, maxResults = 50) {
    const filter = new Evernote.NoteStore.NoteFilter({
      notebookGuid,
      ascending: false,
      order: Evernote.Types.NoteSortOrder.UPDATED
    });

    const spec = this.getDefaultResultSpec();
    return this.noteStore.findNotesMetadata(filter, 0, maxResults, spec);
  }

  /**
   * Get recent notes
   */
  async getRecentNotes(limit = 20) {
    const filter = new Evernote.NoteStore.NoteFilter({
      ascending: false,
      order: Evernote.Types.NoteSortOrder.UPDATED
    });

    const spec = this.getDefaultResultSpec();
    return this.noteStore.findNotesMetadata(filter, 0, limit, spec);
  }
}
```

### Step 5: Search Result Enrichment

```javascript
class SearchService {
  // ... previous methods ...

  /**
   * Enrich search results with notebook and tag names
   */
  async enrichResults(searchResult) {
    // Cache lookups
    if (!this._notebookCache) {
      const notebooks = await this.noteStore.listNotebooks();
      this._notebookCache = new Map(
        notebooks.map(nb => [nb.guid, nb])
      );
    }

    if (!this._tagCache) {
      const tags = await this.noteStore.listTags();
      this._tagCache = new Map(
        tags.map(t => [t.guid, t])
      );
    }

    return searchResult.notes.map(note => ({
      guid: note.guid,
      title: note.title,
      created: new Date(note.created),
      updated: new Date(note.updated),
      notebookName: this._notebookCache.get(note.notebookGuid)?.name,
      tags: (note.tagGuids || []).map(
        guid => this._tagCache.get(guid)?.name
      ).filter(Boolean),
      contentLength: note.contentLength
    }));
  }

  /**
   * Search with enriched results
   */
  async searchEnriched(query, options = {}) {
    const result = await this.search(query, options);
    const enrichedNotes = await this.enrichResults(result);

    return {
      notes: enrichedNotes,
      totalNotes: result.totalNotes,
      hasMore: result.hasMore
    };
  }
}
```

### Step 6: Complete Search Workflow Example

```javascript
// example-search-workflow.js
const Evernote = require('evernote');
const SearchService = require('./services/search-service');
const QueryBuilder = require('./utils/query-builder');

async function searchWorkflow(accessToken) {
  const client = new Evernote.Client({
    token: accessToken,
    sandbox: true
  });

  const noteStore = client.getNoteStore();
  const search = new SearchService(noteStore);
  const qb = new QueryBuilder();

  // Example 1: Find uncompleted todos from this week
  const todoQuery = qb
    .thisWeek()
    .hasUncompletedTodos()
    .build();

  console.log('Query:', todoQuery);
  const todos = await search.searchEnriched(todoQuery);
  console.log(`Found ${todos.totalNotes} notes with uncompleted todos`);

  // Example 2: Find meeting notes in Work notebook
  qb.reset();
  const meetingQuery = qb
    .notebook('Work')
    .intitle('meeting')
    .lastNDays(30)
    .build();

  const meetings = await search.searchEnriched(meetingQuery);
  console.log(`Found ${meetings.totalNotes} meeting notes`);

  // Example 3: Find notes with attachments
  qb.reset();
  const attachmentQuery = qb
    .hasAttachments()
    .updatedAfter('month')
    .build();

  const withAttachments = await search.search(attachmentQuery);
  console.log(`Found ${withAttachments.totalNotes} notes with attachments`);

  // Example 4: Complex query - urgent tasks not in Archive
  qb.reset();
  const urgentQuery = qb
    .tag('urgent')
    .excludeTag('archived')
    .hasUncompletedTodos()
    .build();

  const urgent = await search.searchEnriched(urgentQuery);
  console.log('Urgent tasks:');
  urgent.notes.forEach(note => {
    console.log(`  - ${note.title} (${note.notebookName})`);
  });

  // Example 5: Find related notes
  if (urgent.notes.length > 0) {
    const related = await search.findRelatedNotes(urgent.notes[0].guid);
    console.log(`Related notes to "${urgent.notes[0].title}":`);
    related.notes.forEach(note => {
      console.log(`  - ${note.title}`);
    });
  }

  return {
    todos,
    meetings,
    withAttachments,
    urgent
  };
}

module.exports = searchWorkflow;
```


## Search Grammar Quick Reference

| Operator | Example | Description |
|----------|---------|-------------|
| `notebook:` | `notebook:"Work"` | Restrict to notebook |
| `tag:` | `tag:urgent` | Has tag |
| `-tag:` | `-tag:archived` | Exclude tag |
| `intitle:` | `intitle:meeting` | Word in title |
| `created:` | `created:day-7` | Created after |
| `updated:` | `updated:week` | Updated after |
| `todo:` | `todo:false` | Has uncompleted todos |
| `resource:` | `resource:image/*` | Has attachment type |
| `any:` | `any: term1 term2` | Match ANY term |
| `"phrase"` | `"exact match"` | Exact phrase |
| `prefix*` | `meet*` | Wildcard suffix |
