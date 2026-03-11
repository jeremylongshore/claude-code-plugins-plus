# Evernote Core Workflow A: Note Creation & Management - Implementation Guide

> Full implementation details for the parent SKILL.md.

## Detailed Instructions

### Step 1: Note Creation Service

```javascript
// services/note-service.js
const Evernote = require('evernote');

class NoteService {
  constructor(noteStore) {
    this.noteStore = noteStore;
  }

  /**
   * Create a new note with proper ENML formatting
   */
  async createNote({ title, content, notebookGuid, tagNames = [] }) {
    const note = new Evernote.Types.Note();
    note.title = this.sanitizeTitle(title);
    note.content = this.wrapInENML(content);

    if (notebookGuid) {
      note.notebookGuid = notebookGuid;
    }

    if (tagNames.length > 0) {
      note.tagNames = tagNames;
    }

    return this.noteStore.createNote(note);
  }

  /**
   * Create note from plain text
   */
  async createTextNote(title, text, notebookGuid = null) {
    const content = this.textToENML(text);
    return this.createNote({ title, content, notebookGuid });
  }

  /**
   * Create note from HTML (converted to ENML)
   */
  async createHtmlNote(title, html, notebookGuid = null) {
    const content = this.htmlToENML(html);
    return this.createNote({ title, content, notebookGuid });
  }

  /**
   * Create a checklist note
   */
  async createChecklistNote(title, items, notebookGuid = null) {
    const checklistHtml = items.map(item => {
      if (typeof item === 'string') {
        return `<div><en-todo checked="false"/> ${this.escapeHtml(item)}</div>`;
      }
      return `<div><en-todo checked="${item.checked}"/> ${this.escapeHtml(item.text)}</div>`;
    }).join('\n');

    return this.createNote({
      title,
      content: checklistHtml,
      notebookGuid
    });
  }

  // Helper methods
  wrapInENML(content) {
    return `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note>
${content}
</en-note>`;
  }

  textToENML(text) {
    const escaped = this.escapeHtml(text).replace(/\n/g, '<br/>');
    return this.wrapInENML(`<div>${escaped}</div>`);
  }

  htmlToENML(html) {
    // Remove forbidden elements and attributes
    let clean = html
      .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '')
      .replace(/<form[^>]*>[\s\S]*?<\/form>/gi, '')
      .replace(/<iframe[^>]*>[\s\S]*?<\/iframe>/gi, '')
      .replace(/\s(class|id|onclick|onload)="[^"]*"/gi, '');

    return this.wrapInENML(clean);
  }

  sanitizeTitle(title) {
    // Max 255 chars, no newlines
    return title.replace(/[\r\n]/g, ' ').slice(0, 255);
  }

  escapeHtml(text) {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }
}

module.exports = NoteService;
```

### Step 2: Note Retrieval and Reading

```javascript
class NoteService {
  // ... previous methods ...

  /**
   * Get note with content
   */
  async getNote(noteGuid) {
    return this.noteStore.getNote(noteGuid, true, false, false, false);
  }

  /**
   * Get note with all resources (attachments)
   */
  async getNoteWithResources(noteGuid) {
    return this.noteStore.getNote(noteGuid, true, true, true, false);
  }

  /**
   * Get note metadata only (faster)
   */
  async getNoteMetadata(noteGuid) {
    return this.noteStore.getNote(noteGuid, false, false, false, false);
  }

  /**
   * Extract plain text from ENML content
   */
  extractText(enmlContent) {
    return enmlContent
      // Remove XML declaration and DOCTYPE
      .replace(/<\?xml[^>]*\?>/g, '')
      .replace(/<!DOCTYPE[^>]*>/g, '')
      // Remove all HTML tags
      .replace(/<[^>]+>/g, ' ')
      // Decode entities
      .replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&quot;/g, '"')
      // Clean whitespace
      .replace(/\s+/g, ' ')
      .trim();
  }

  /**
   * Check if note has uncompleted todos
   */
  hasUncompletedTodos(enmlContent) {
    return /<en-todo\s+checked="false"/.test(enmlContent);
  }
}
```

### Step 3: Note Updates

```javascript
class NoteService {
  // ... previous methods ...

  /**
   * Update note title
   */
  async updateTitle(noteGuid, newTitle) {
    const note = await this.getNoteMetadata(noteGuid);
    note.title = this.sanitizeTitle(newTitle);
    return this.noteStore.updateNote(note);
  }

  /**
   * Update note content
   */
  async updateContent(noteGuid, newContent) {
    const note = await this.getNoteMetadata(noteGuid);
    note.content = this.wrapInENML(newContent);
    return this.noteStore.updateNote(note);
  }

  /**
   * Append content to existing note
   */
  async appendToNote(noteGuid, additionalContent) {
    const note = await this.getNote(noteGuid);
    const currentContent = note.content;

    // Insert before closing </en-note>
    const newContent = currentContent.replace(
      '</en-note>',
      `<hr/>${additionalContent}</en-note>`
    );

    note.content = newContent;
    return this.noteStore.updateNote(note);
  }

  /**
   * Add tags to note
   */
  async addTags(noteGuid, tagNames) {
    const note = await this.getNoteMetadata(noteGuid);
    const existingTags = note.tagNames || [];
    note.tagNames = [...new Set([...existingTags, ...tagNames])];
    return this.noteStore.updateNote(note);
  }

  /**
   * Move note to different notebook
   */
  async moveToNotebook(noteGuid, notebookGuid) {
    const note = await this.getNoteMetadata(noteGuid);
    note.notebookGuid = notebookGuid;
    return this.noteStore.updateNote(note);
  }

  /**
   * Toggle todo completion
   */
  async toggleTodo(noteGuid, todoIndex) {
    const note = await this.getNote(noteGuid);
    let content = note.content;
    let count = 0;

    content = content.replace(/<en-todo\s+checked="(true|false)"\s*\/>/g, (match, checked) => {
      if (count === todoIndex) {
        const newChecked = checked === 'true' ? 'false' : 'true';
        count++;
        return `<en-todo checked="${newChecked}"/>`;
      }
      count++;
      return match;
    });

    note.content = content;
    return this.noteStore.updateNote(note);
  }
}
```

### Step 4: Note Organization

```javascript
class NotebookService {
  constructor(noteStore) {
    this.noteStore = noteStore;
  }

  /**
   * List all notebooks
   */
  async listNotebooks() {
    return this.noteStore.listNotebooks();
  }

  /**
   * Get default notebook
   */
  async getDefaultNotebook() {
    return this.noteStore.getDefaultNotebook();
  }

  /**
   * Create notebook
   */
  async createNotebook(name, stack = null) {
    const notebook = new Evernote.Types.Notebook();
    notebook.name = name;
    if (stack) {
      notebook.stack = stack;
    }
    return this.noteStore.createNotebook(notebook);
  }

  /**
   * Find or create notebook
   */
  async ensureNotebook(name, stack = null) {
    const notebooks = await this.listNotebooks();
    const existing = notebooks.find(n =>
      n.name.toLowerCase() === name.toLowerCase()
    );
    return existing || this.createNotebook(name, stack);
  }

  /**
   * Get notebook by name
   */
  async getNotebookByName(name) {
    const notebooks = await this.listNotebooks();
    return notebooks.find(n =>
      n.name.toLowerCase() === name.toLowerCase()
    );
  }

  /**
   * Organize notebooks into stacks
   */
  async groupByStack() {
    const notebooks = await this.listNotebooks();
    const groups = {};

    notebooks.forEach(nb => {
      const stack = nb.stack || '(No Stack)';
      if (!groups[stack]) {
        groups[stack] = [];
      }
      groups[stack].push(nb);
    });

    return groups;
  }
}
```

### Step 5: Complete Workflow Example

```javascript
// example-workflow.js
const Evernote = require('evernote');
const NoteService = require('./services/note-service');
const NotebookService = require('./services/notebook-service');

async function noteManagementWorkflow(accessToken) {
  const client = new Evernote.Client({
    token: accessToken,
    sandbox: true
  });

  const noteStore = client.getNoteStore();
  const noteService = new NoteService(noteStore);
  const notebookService = new NotebookService(noteStore);

  // 1. Ensure workspace notebook exists
  const workNotebook = await notebookService.ensureNotebook('Work', 'Projects');
  console.log('Using notebook:', workNotebook.name);

  // 2. Create a meeting note
  const meetingNote = await noteService.createNote({
    title: 'Team Standup - ' + new Date().toLocaleDateString(),
    content: `
      <h2>Attendees</h2>
      <p>Alice, Bob, Charlie</p>

      <h2>Discussion Points</h2>
      <ul>
        <li>Sprint progress review</li>
        <li>Blockers and dependencies</li>
        <li>Action items</li>
      </ul>

      <h2>Action Items</h2>
      <div><en-todo checked="false"/> Review PR #123 - Alice</div>
      <div><en-todo checked="false"/> Update documentation - Bob</div>
      <div><en-todo checked="false"/> Schedule follow-up - Charlie</div>
    `,
    notebookGuid: workNotebook.guid,
    tagNames: ['meeting', 'standup', 'team']
  });
  console.log('Created meeting note:', meetingNote.guid);

  // 3. Create a quick task note
  const taskNote = await noteService.createChecklistNote(
    'Today\'s Tasks',
    [
      { text: 'Review emails', checked: true },
      { text: 'Code review', checked: false },
      { text: 'Update sprint board', checked: false },
      { text: 'Team sync', checked: false }
    ],
    workNotebook.guid
  );
  console.log('Created task note:', taskNote.guid);

  // 4. Append late addition to meeting note
  await noteService.appendToNote(meetingNote.guid, `
    <h2>Late Addition</h2>
    <p>Added after the meeting: Remember to follow up on budget approval.</p>
  `);
  console.log('Appended content to meeting note');

  // 5. Mark first task as done
  await noteService.toggleTodo(taskNote.guid, 1); // Toggle "Code review"
  console.log('Toggled todo completion');

  return {
    meetingNote,
    taskNote,
    notebook: workNotebook
  };
}

module.exports = noteManagementWorkflow;
```


## Best Practices

1. **Always validate ENML** before sending to API
2. **Use tagNames** (strings) not tagGuids for simplicity
3. **Batch read-then-update** operations to avoid conflicts
4. **Handle rate limits** with exponential backoff
5. **Keep note titles under 255 characters**
