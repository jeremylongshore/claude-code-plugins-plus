---
name: apple-notes-data-handling
description: |
  Handle Apple Notes data formats: HTML body, attachments, and rich content.
  Trigger: "apple notes data handling".
allowed-tools: Read, Write, Edit, Bash(osascript:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, macos, apple-notes, automation]
compatible-with: claude-code
---

# Apple Notes Data Handling

## Overview

Apple Notes stores note content as a restricted subset of HTML internally. The `body()` property in JXA returns this HTML, which includes `<div>`, `<h1>`-`<h3>`, `<b>`, `<i>`, `<ul>`, `<li>`, and Apple-specific classes for checklists and tables. Attachments (images, PDFs, sketches, scans) are embedded as `<img>` or object references but cannot be directly extracted via JXA — they require the `attachments()` property. Understanding these data formats is essential for building reliable import, export, and backup pipelines.

## Note Body HTML Format

```html
<!-- Apple Notes uses a subset of HTML wrapped in <div> blocks -->
<div><h1>Title</h1></div>
<div><br></div>
<div>Paragraph text here.</div>
<div><b>Bold text</b> and <i>italic text</i></div>
<div><br></div>
<div><ul><li>List item 1</li><li>List item 2</li></ul></div>

<!-- Checklists use Apple's custom class -->
<div><ul class="com-apple-note-checklist">
  <li class="done">Completed item</li>
  <li>Incomplete item</li>
</ul></div>

<!-- Tables (macOS Ventura+) use standard HTML tables -->
<div><table><tr><td>Cell 1</td><td>Cell 2</td></tr></table></div>

<!-- Tags (macOS Sonoma+) are stored as hashtags in body text -->
<div>#project #important</div>
```

## Export All Notes to JSON

```bash
#!/bin/bash
# Full export with metadata — useful for backups and migration
osascript -l JavaScript -e '
  const Notes = Application("Notes");
  const results = Notes.defaultAccount.notes().map(n => ({
    id: n.id(),
    title: n.name(),
    body: n.body(),
    plaintext: n.plaintext(),
    folder: n.container().name(),
    created: n.creationDate().toISOString(),
    modified: n.modificationDate().toISOString(),
    attachmentCount: n.attachments().length,
  }));
  JSON.stringify(results, null, 2);
' > "$HOME/notes-export-$(date +%Y%m%d).json"
```

## HTML to Markdown Converter

```typescript
// src/data/html-to-markdown.ts
function notesHtmlToMarkdown(html: string): string {
  return html
    .replace(/<h1>(.*?)<\/h1>/g, "# $1")
    .replace(/<h2>(.*?)<\/h2>/g, "## $1")
    .replace(/<h3>(.*?)<\/h3>/g, "### $1")
    .replace(/<b>(.*?)<\/b>/g, "**$1**")
    .replace(/<strong>(.*?)<\/strong>/g, "**$1**")
    .replace(/<i>(.*?)<\/i>/g, "*$1*")
    .replace(/<em>(.*?)<\/em>/g, "*$1*")
    .replace(/<li class="done">(.*?)<\/li>/g, "- [x] $1")
    .replace(/<li>(.*?)<\/li>/g, "- [ ] $1")
    .replace(/<br\s*\/?>/g, "\n")
    .replace(/<div>/g, "").replace(/<\/div>/g, "\n")
    .replace(/<[^>]*>/g, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}
```

## Attachment Handling

```bash
# List all notes with attachments and their counts
osascript -l JavaScript -e '
  const Notes = Application("Notes");
  Notes.defaultAccount.notes()
    .filter(n => n.attachments().length > 0)
    .map(n => n.name() + ": " + n.attachments().length + " attachments (" +
      n.attachments().map(a => a.name()).join(", ") + ")")
    .join("\n");
'

# Note: JXA cannot directly save attachment binary data.
# For full attachment export, use Shortcuts:
# shortcuts run "Export Note Attachments" --input-type text --input "Note Title"
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `body()` returns empty string | Note contains only attachments (no text) | Check `attachments().length`; use `plaintext()` as fallback |
| HTML contains unexpected tags | Note created on iOS with unsupported formatting | Strip unknown tags; keep only known Apple Notes subset |
| `plaintext()` truncated | Very large note body | Export via `body()` HTML instead; convert after |
| Checklist state lost in export | Custom class not preserved in conversion | Map `class="done"` to `[x]` before stripping HTML |
| Attachment names are generic | Auto-generated names like `Image.png` | Use note title + index for meaningful filenames |

## Resources

- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- [JXA Cookbook](https://github.com/JXA-Cookbook/JXA-Cookbook)
- [Apple Notes File Format (reverse-engineered)](https://ciofecaforensics.com/2020/08/05/apple-notes-format/)

## Next Steps

For migrating between note platforms, see `apple-notes-migration-deep-dive`. For backup automation, see `apple-notes-deploy-integration`.
