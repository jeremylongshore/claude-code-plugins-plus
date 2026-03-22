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
Apple Notes stores content as HTML internally. Understanding the data format is essential for import/export operations.

## Note Body HTML Format
```html
<!-- Apple Notes uses a subset of HTML -->
<div><h1>Title</h1></div>
<div><br></div>
<div>Paragraph text here.</div>
<div><br></div>
<div><b>Bold text</b> and <i>italic text</i></div>
<div><br></div>
<div><ul><li>List item 1</li><li>List item 2</li></ul></div>

<!-- Checklists use a custom attribute -->
<div><ul class="com-apple-note-checklist">
  <li class="done">Completed item</li>
  <li>Incomplete item</li>
</ul></div>
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
    .replace(/<li>(.*?)<\/li>/g, "- $1")
    .replace(/<br\s*\/?>/g, "\n")
    .replace(/<div>/g, "").replace(/<\/div>/g, "\n")
    .replace(/<[^>]*>/g, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function markdownToNotesHtml(md: string): string {
  return md
    .replace(/^# (.+)$/gm, "<h1>$1</h1>")
    .replace(/^## (.+)$/gm, "<h2>$1</h2>")
    .replace(/\*\*(.+?)\*\*/g, "<b>$1</b>")
    .replace(/\*(.+?)\*/g, "<i>$1</i>")
    .replace(/^- \[x\] (.+)$/gm, "<li class=\"done\">$1</li>")
    .replace(/^- (.+)$/gm, "<li>$1</li>")
    .replace(/\n/g, "<br>");
}
```

## Attachment Handling
```bash
# List notes with attachments
osascript -l JavaScript -e "
  const Notes = Application(\"Notes\");
  Notes.defaultAccount.notes()
    .filter(n => n.attachments().length > 0)
    .map(n => \`\${n.name()}: \${n.attachments().length} attachments\`)
    .join(\"\\n\");
"
```

## Resources

- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- [JXA Examples](https://jxa-examples.akjems.com/)
