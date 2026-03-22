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

## Migration Paths

| From | To | Method |
|------|----|--------|
| Apple Notes | Obsidian | Export HTML → convert to Markdown → copy to vault |
| Apple Notes | Notion | Export JSON → Notion API import |
| Obsidian | Apple Notes | Read .md → convert to HTML → JXA create |
| Evernote | Apple Notes | File > Import from Evernote (built-in) |

## Apple Notes → Obsidian Migration
```bash
#!/bin/bash
# Export all Apple Notes to Obsidian vault
VAULT_DIR="$HOME/obsidian-vault/Apple Notes Import"
mkdir -p "$VAULT_DIR"

osascript -l JavaScript -e "
  const Notes = Application(\"Notes\");
  Notes.defaultAccount.notes().map(n => JSON.stringify({
    title: n.name(),
    body: n.body(),
    folder: n.container().name(),
    created: n.creationDate().toISOString(),
  })).join(\"\\n---SEP---\\n\");
" | while IFS= read -r line; do
  [ "$line" = "---SEP---" ] && continue
  title=$(echo "$line" | jq -r ".title" 2>/dev/null || continue)
  body=$(echo "$line" | jq -r ".body" 2>/dev/null)
  folder=$(echo "$line" | jq -r ".folder" 2>/dev/null)
  created=$(echo "$line" | jq -r ".created" 2>/dev/null)

  # Convert HTML to Markdown (basic)
  md=$(echo "$body" | sed "s/<h1>/# /g; s/<\/h1>//g; s/<h2>/## /g; s/<\/h2>//g; s/<br>/\\n/g; s/<[^>]*>//g")

  safe_title=$(echo "$title" | tr "/:*?\"<>|" "-" | head -c 100)
  mkdir -p "$VAULT_DIR/$folder"
  echo -e "---\ncreated: $created\nsource: apple-notes\n---\n\n# $title\n\n$md" > "$VAULT_DIR/$folder/$safe_title.md"
done
echo "Migration complete: $VAULT_DIR"
```

## Obsidian → Apple Notes Import
```bash
#!/bin/bash
for md_file in "$VAULT_DIR"/*.md; do
  title=$(head -1 "$md_file" | sed "s/^#\s*//")
  body=$(cat "$md_file" | sed "s/^# /<h1>/;s/$/<\/h1>/" | sed "s/\n/<br>/g")
  osascript -l JavaScript -e "
    const Notes = Application(\"Notes\");
    const note = Notes.Note({name: \"$title\", body: \"$body\"});
    Notes.defaultAccount.folders[0].notes.push(note);
  "
  sleep 1
done
```

## Resources

- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- [JXA Examples](https://jxa-examples.akjems.com/)
