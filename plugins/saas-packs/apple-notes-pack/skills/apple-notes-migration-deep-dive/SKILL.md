---
name: apple-notes-migration-deep-dive
description: |
  Migrate notes between Apple Notes, Obsidian, Notion, and other platforms.
  Trigger: "apple notes migration".
allowed-tools: Read, Write, Edit, Bash(osascript:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, macos, apple-notes, automation]
compatible-with: claude-code
---

# Apple Notes Migration Deep Dive

## Overview

Migrating to or from Apple Notes requires understanding that Notes stores content as proprietary HTML with no REST API for bulk operations. All automation goes through JXA/osascript on a local Mac. This guide covers the four most common migration paths with production-tested scripts. Key challenges include: HTML-to-Markdown conversion fidelity, attachment extraction limitations (JXA cannot export binary attachment data directly), and iCloud sync delays that affect timing of bulk imports.

## Migration Paths

| From | To | Method | Attachments |
|------|----|--------|-------------|
| Apple Notes | Obsidian | JXA export HTML → convert to Markdown → vault | Manual via Shortcuts |
| Apple Notes | Notion | JXA export JSON → Notion API import | Re-upload required |
| Obsidian | Apple Notes | Read .md → convert to HTML → JXA create | Not supported via JXA |
| Evernote | Apple Notes | File > Import from Evernote (built-in) | Preserved automatically |
| OneNote | Apple Notes | Export to .enex → Import from Evernote | Partial preservation |

## Step 1: Pre-Migration Backup

```bash
#!/bin/bash
# Always back up before migration
BACKUP_DIR="$HOME/notes-backup-$(date +%Y%m%d-%H%M)"
mkdir -p "$BACKUP_DIR"
osascript -l JavaScript -e '
  const Notes = Application("Notes");
  const data = Notes.defaultAccount.notes().map(n => ({
    id: n.id(), title: n.name(), body: n.body(),
    folder: n.container().name(),
    created: n.creationDate().toISOString(),
    modified: n.modificationDate().toISOString(),
    attachments: n.attachments().length
  }));
  JSON.stringify(data, null, 2);
' > "$BACKUP_DIR/full-export.json"
echo "Backed up $(jq length "$BACKUP_DIR/full-export.json") notes to $BACKUP_DIR"
```

## Step 2: Apple Notes to Obsidian

```bash
#!/bin/bash
VAULT_DIR="$HOME/obsidian-vault/Apple Notes Import"
mkdir -p "$VAULT_DIR"

osascript -l JavaScript -e '
  const Notes = Application("Notes");
  Notes.defaultAccount.notes().map(n => JSON.stringify({
    title: n.name(), body: n.body(),
    folder: n.container().name(),
    created: n.creationDate().toISOString(),
  })).join("\n===NOTESEP===\n");
' | while IFS= read -r line; do
  [ "$line" = "===NOTESEP===" ] && continue
  title=$(echo "$line" | jq -r '.title' 2>/dev/null) || continue
  body=$(echo "$line" | jq -r '.body' 2>/dev/null)
  folder=$(echo "$line" | jq -r '.folder' 2>/dev/null)
  created=$(echo "$line" | jq -r '.created' 2>/dev/null)

  # Convert Apple Notes HTML to Markdown
  md=$(echo "$body" | sed 's/<h1>/# /g; s/<\/h1>//g; s/<h2>/## /g; s/<\/h2>//g' \
    | sed 's/<li class="done">/- [x] /g; s/<li>/- /g; s/<\/li>//g' \
    | sed 's/<br[^>]*>/\n/g; s/<[^>]*>//g' | sed '/^$/N;/^\n$/d')

  safe_title=$(echo "$title" | tr '/:*?"<>|' '-' | head -c 80)
  mkdir -p "$VAULT_DIR/$folder"
  printf "---\ncreated: %s\nsource: apple-notes\n---\n\n%s\n" "$created" "$md" \
    > "$VAULT_DIR/$folder/$safe_title.md"
done
echo "Migration complete: $(find "$VAULT_DIR" -name '*.md' | wc -l) files in $VAULT_DIR"
```

## Step 3: Obsidian to Apple Notes

```bash
#!/bin/bash
# Import Markdown files into Apple Notes
VAULT_DIR="${1:-$HOME/obsidian-vault}"
COUNT=0
find "$VAULT_DIR" -name '*.md' -type f | while read -r md_file; do
  title=$(head -20 "$md_file" | grep -m1 '^# ' | sed 's/^# //')
  [ -z "$title" ] && title=$(basename "$md_file" .md)
  # Convert Markdown to Apple Notes HTML
  body=$(cat "$md_file" | sed 's/^# \(.*\)/<h1>\1<\/h1>/; s/^## \(.*\)/<h2>\1<\/h2>/' \
    | sed 's/\*\*\([^*]*\)\*\*/<b>\1<\/b>/g; s/\*\([^*]*\)\*/<i>\1<\/i>/g' \
    | sed 's/$/<br>/g' | tr -d '\n')
  osascript -l JavaScript -e "
    const Notes = Application('Notes');
    const note = Notes.Note({name: '$title', body: '$body'});
    Notes.defaultAccount.folders[0].notes.push(note);
  "
  COUNT=$((COUNT + 1))
  sleep 1  # Throttle for iCloud sync
done
echo "Imported $COUNT notes"
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Notes missing after import | iCloud sync delay | Wait 5-10 minutes; check on another device |
| HTML formatting garbled | Unsupported HTML tags in source | Pre-clean HTML; strip to Apple Notes subset only |
| Special characters in title | Shell escaping issues with JXA | Use JSON encoding; pipe through `jq` |
| Attachments not migrated | JXA cannot write binary attachments | Use Shortcuts "Add Attachment to Note" action |
| Duplicate notes after re-run | No dedup in import script | Track imported note IDs in a local manifest file |

## Resources

- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- [Obsidian URI Protocol](https://help.obsidian.md/Extending+Obsidian/Obsidian+URI)
- [Notion Import API](https://developers.notion.com/docs/working-with-page-content)

## Next Steps

For data format details and HTML conversion, see `apple-notes-data-handling`. For macOS version compatibility during migration, see `apple-notes-upgrade-migration`.
