---
name: apple-notes-core-workflow-a
description: |
  Build automated note management workflows with Apple Notes JXA scripts.
  Use when batch-creating notes, syncing content from external sources,
  organizing notes into folder hierarchies, or building note templates.
  Trigger: "apple notes workflow", "batch notes", "note templates",
  "organize apple notes", "sync notes".
allowed-tools: Read, Write, Edit, Bash(osascript:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, macos, apple-notes, automation, workflow]
compatible-with: claude-code
---

# Apple Notes Core Workflow A — Note Management Automation

## Overview

Primary workflow: automate Apple Notes management with batch creation, template-based note generation, folder organization, and content sync from external sources (Markdown files, RSS, calendar events).

## Instructions

### Step 1: Batch Note Creator from Markdown Files

```bash
#!/bin/bash
# scripts/markdown-to-notes.sh — Import Markdown files as Apple Notes

FOLDER_NAME="${1:-Imported}"

for md_file in *.md; do
  [ -f "$md_file" ] || continue
  title=$(head -1 "$md_file" | sed 's/^#\s*//')
  # Convert Markdown to basic HTML
  body=$(cat "$md_file" | sed 's/^# /<h1>/;s/$/<\/h1>/' | sed 's/^## /<h2>/;s/$/<\/h2>/' | sed 's/^- /<li>/;s/$/<\/li>/' | sed 's/^$/<br>/')

  osascript -l JavaScript -e "
    const Notes = Application('Notes');
    const account = Notes.defaultAccount;
    let folder = account.folders().find(f => f.name() === '$FOLDER_NAME');
    if (!folder) {
      folder = Notes.Folder({ name: '$FOLDER_NAME' });
      account.folders.push(folder);
    }
    const note = Notes.Note({ name: '$title', body: \`$body\` });
    folder.notes.push(note);
    'Created: $title';
  "
  echo "Imported: $md_file → $title"
done
```

### Step 2: Note Template Engine (JXA)

```javascript
// scripts/note-template.js — Run with: osascript -l JavaScript scripts/note-template.js
const Notes = Application('Notes');

const TEMPLATES = {
  meeting: (data) => `
    <h1>${data.title || 'Meeting Notes'}</h1>
    <p><strong>Date:</strong> ${new Date().toLocaleDateString()}</p>
    <p><strong>Attendees:</strong> ${data.attendees || 'TBD'}</p>
    <h2>Agenda</h2><ul><li></li></ul>
    <h2>Action Items</h2><ul><li></li></ul>
    <h2>Notes</h2><p></p>
  `,
  daily: (data) => `
    <h1>Daily Log — ${new Date().toLocaleDateString()}</h1>
    <h2>Tasks</h2><ul><li></li></ul>
    <h2>Accomplishments</h2><ul><li></li></ul>
    <h2>Blockers</h2><ul><li></li></ul>
  `,
  project: (data) => `
    <h1>${data.title || 'Project'}</h1>
    <p><strong>Status:</strong> ${data.status || 'Active'}</p>
    <h2>Overview</h2><p></p>
    <h2>Requirements</h2><ul><li></li></ul>
    <h2>Timeline</h2><ul><li></li></ul>
  `,
};

function createFromTemplate(templateName, data, folderName) {
  const template = TEMPLATES[templateName];
  if (!template) throw new Error(`Unknown template: ${templateName}`);

  const account = Notes.defaultAccount;
  let folder = account.folders().find(f => f.name() === folderName);
  if (!folder) {
    folder = Notes.Folder({ name: folderName });
    account.folders.push(folder);
  }

  const body = template(data);
  const note = Notes.Note({ name: data.title || templateName, body });
  folder.notes.push(note);
  return note.id();
}

// Usage: create meeting notes
createFromTemplate('meeting', {
  title: 'Sprint Planning',
  attendees: 'Team Alpha',
}, 'Meetings');
```

### Step 3: Folder Organization Script

```bash
# Organize notes into folders based on naming conventions
osascript -l JavaScript -e '
  const Notes = Application("Notes");
  const account = Notes.defaultAccount;
  const allNotes = account.notes();

  const rules = [
    { pattern: /^Meeting:/i, folder: "Meetings" },
    { pattern: /^Project:/i, folder: "Projects" },
    { pattern: /^Daily/i, folder: "Daily Logs" },
    { pattern: /^TODO/i, folder: "Tasks" },
  ];

  let moved = 0;
  for (const note of allNotes) {
    const name = note.name();
    for (const rule of rules) {
      if (rule.pattern.test(name)) {
        let folder = account.folders().find(f => f.name() === rule.folder);
        if (!folder) {
          folder = Notes.Folder({ name: rule.folder });
          account.folders.push(folder);
        }
        Notes.move(note, { to: folder });
        moved++;
        break;
      }
    }
  }
  `Organized ${moved} notes into folders`;
'
```

## Output

- Batch Markdown file → Apple Notes importer
- Template engine with meeting/daily/project templates
- Rule-based folder organization
- Folder creation on-demand

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Can't move note` | Note is locked | Unlock note in Notes.app first |
| HTML rendering issues | Invalid HTML tags | Use basic tags: h1, h2, p, ul, li, strong |
| Slow batch import | iCloud sync throttling | Add 1s delay between note creates |
| Duplicate notes | Script run twice | Check for existing note by name before creating |

## Resources

- [AppleScript Notes Guide](https://www.macosxautomation.com/applescript/notes/)
- [JXA Examples](https://jxa-examples.akjems.com/)

## Next Steps

For exporting and converting notes, see `apple-notes-core-workflow-b`.
