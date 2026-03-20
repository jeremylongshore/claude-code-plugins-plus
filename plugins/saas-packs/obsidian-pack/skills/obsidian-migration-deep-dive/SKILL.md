---
name: obsidian-migration-deep-dive
description: |
  Execute major Obsidian plugin rewrites and migration strategies.
  Use when migrating to or from Obsidian, performing major plugin rewrites,
  or re-platforming existing note systems to Obsidian.
  Trigger with phrases like "migrate to obsidian", "obsidian migration",
  "convert notes to obsidian", "obsidian replatform".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Obsidian Migration Deep Dive

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`ls *.enex *.json *.zip 2>/dev/null | head -10 || echo 'No export files in cwd'`
## Overview
Migrate notes from Notion, Evernote, Roam Research, Bear, and Apple Notes into Obsidian -- handling attachment relocation, internal link conversion to `[[wikilinks]]`, tag migration, and frontmatter generation.

## Prerequisites
- Exported data from the source application (see each section for format)
- A target Obsidian vault created and opened at least once
- Node.js 18+ for running migration scripts
- Backup of source data before starting

## Instructions

### Step 1: Pre-Migration Assessment

```bash
#!/bin/bash
# assess-migration.sh <export-directory>
EXPORT_DIR="${1:-.}"
echo "=== Migration Assessment: $EXPORT_DIR ==="
echo "File counts:"
for ext in md html enex json csv pdf png jpg gif zip; do
  count=$(find "$EXPORT_DIR" -name "*.$ext" 2>/dev/null | wc -l)
  [ "$count" -gt 0 ] && echo "  .$ext: $count"
done
echo "Total size: $(du -sh "$EXPORT_DIR" 2>/dev/null | cut -f1)"
echo "Max directory depth: $(find "$EXPORT_DIR" -type d | awk -F/ '{print NF-1}' | sort -n | tail -1)"
echo "Sample filenames:"
find "$EXPORT_DIR" -type f | head -5
```

### Step 2: Notion Export Migration

Notion exports as a zip containing markdown files, CSV databases, and attachments. The markdown uses Notion-style links and has UUIDs appended to filenames.

```javascript
// notion-to-obsidian.mjs
import { readdir, readFile, writeFile, mkdir, copyFile } from 'fs/promises';
import { join, basename, extname, dirname } from 'path';

const NOTION_EXPORT = process.argv[2]; // Unzipped Notion export
const VAULT_DIR = process.argv[3];     // Target Obsidian vault

if (!NOTION_EXPORT || !VAULT_DIR) {
  console.error('Usage: node notion-to-obsidian.mjs <notion-export-dir> <vault-dir>');
  process.exit(1);
}

// Step 1: Build a filename map (strip Notion UUIDs from names)
// Notion appends " abc123def456" to every filename
function cleanNotionName(filename) {
  return filename.replace(/\s+[a-f0-9]{32}(?=\.\w+$|$)/, '');
}

async function* walkDir(dir) {
  const entries = await readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = join(dir, entry.name);
    if (entry.isDirectory()) yield* walkDir(fullPath);
    else yield fullPath;
  }
}

async function migrate() {
  const fileMap = new Map(); // original path -> clean path
  const attachments = [];
  const notes = [];

  // Categorize files
  for await (const filePath of walkDir(NOTION_EXPORT)) {
    const ext = extname(filePath).toLowerCase();
    const relPath = filePath.slice(NOTION_EXPORT.length + 1);
    const cleanPath = relPath.split('/').map(cleanNotionName).join('/');

    fileMap.set(relPath, cleanPath);

    if (ext === '.md') notes.push({ src: filePath, dest: cleanPath });
    else if (ext === '.csv') notes.push({ src: filePath, dest: cleanPath.replace('.csv', '.md'), isCSV: true });
    else attachments.push({ src: filePath, dest: join('attachments', basename(cleanPath)) });
  }

  // Process markdown notes
  for (const note of notes) {
    let content;
    if (note.isCSV) {
      content = await convertCSVToMarkdown(note.src);
    } else {
      content = await readFile(note.src, 'utf-8');
    }

    // Convert Notion links to Obsidian wikilinks
    // Notion: [Page Title](Page%20Title%20abc123def456.md)
    // Obsidian: [[Page Title]]
    content = content.replace(
      /\[([^\]]+)\]\(([^)]+\.md)\)/g,
      (match, text, href) => {
        const decoded = decodeURIComponent(href);
        const clean = cleanNotionName(basename(decoded, '.md'));
        return `[[${clean}]]`;
      }
    );

    // Convert Notion image references to Obsidian
    // Notion: ![description](Image%20Name%20abc123.png)
    // Obsidian: ![[image-name.png]]
    content = content.replace(
      /!\[([^\]]*)\]\(([^)]+)\)/g,
      (match, alt, src) => {
        const decoded = decodeURIComponent(src);
        if (decoded.startsWith('http')) return match; // Keep external URLs
        const clean = cleanNotionName(basename(decoded));
        return `![[${clean}]]`;
      }
    );

    // Add frontmatter
    const title = basename(note.dest, extname(note.dest));
    content = `---\ntitle: "${title}"\nsource: notion\nmigrated: ${new Date().toISOString().split('T')[0]}\n---\n\n${content}`;

    const destPath = join(VAULT_DIR, note.dest);
    await mkdir(dirname(destPath), { recursive: true });
    await writeFile(destPath, content);
  }

  // Copy attachments
  await mkdir(join(VAULT_DIR, 'attachments'), { recursive: true });
  for (const att of attachments) {
    await copyFile(att.src, join(VAULT_DIR, att.dest));
  }

  console.log(`Migrated ${notes.length} notes, ${attachments.length} attachments`);
}

async function convertCSVToMarkdown(csvPath) {
  const raw = await readFile(csvPath, 'utf-8');
  const lines = raw.trim().split('\n');
  if (lines.length === 0) return '';

  const headers = lines[0].split(',').map(h => h.replace(/^"|"$/g, ''));
  const rows = lines.slice(1).map(line =>
    line.split(',').map(c => c.replace(/^"|"$/g, ''))
  );

  let md = `| ${headers.join(' | ')} |\n`;
  md += `| ${headers.map(() => '---').join(' | ')} |\n`;
  for (const row of rows) {
    md += `| ${row.join(' | ')} |\n`;
  }
  return md;
}

migrate().catch(console.error);
```

Run it:
```bash
unzip Notion-Export-*.zip -d notion-export
node notion-to-obsidian.mjs notion-export ~/my-vault
```

### Step 3: Evernote ENEX Migration

ENEX files are XML containing notes with HTML content and embedded attachments (base64).

```javascript
// evernote-to-obsidian.mjs
import { readFile, writeFile, mkdir } from 'fs/promises';
import { join } from 'path';
import { parseString } from 'xml2js'; // npm install xml2js
import TurndownService from 'turndown';  // npm install turndown

const ENEX_FILE = process.argv[2];
const VAULT_DIR = process.argv[3];

const turndown = new TurndownService({ headingStyle: 'atx', codeBlockStyle: 'fenced' });

function parseENEX(xml) {
  return new Promise((resolve, reject) => {
    parseString(xml, (err, result) => {
      if (err) reject(err);
      else resolve(result['en-export']?.note || []);
    });
  });
}

function sanitizeFilename(name) {
  return name.replace(/[<>:"/\\|?*]/g, '-').replace(/\s+/g, ' ').trim();
}

async function migrate() {
  const xml = await readFile(ENEX_FILE, 'utf-8');
  const notes = await parseENEX(xml);

  await mkdir(join(VAULT_DIR, 'attachments'), { recursive: true });

  let count = 0;
  for (const note of notes) {
    const title = sanitizeFilename(note.title?.[0] || `Untitled-${count}`);
    const html = note.content?.[0] || '';
    const created = note.created?.[0] || '';
    const tags = note.tag || [];

    // Convert HTML to Markdown
    // Strip ENEX wrapper: <en-note>...</en-note>
    const bodyHtml = html.replace(/<\/?en-note[^>]*>/g, '');
    let markdown = turndown.turndown(bodyHtml);

    // Build frontmatter
    const fm = [
      '---',
      `title: "${title}"`,
      `source: evernote`,
      `created: ${formatEvernoteDate(created)}`,
      `migrated: ${new Date().toISOString().split('T')[0]}`,
    ];
    if (tags.length > 0) {
      fm.push(`tags: [${tags.map(t => `"${t}"`).join(', ')}]`);
    }
    fm.push('---', '');

    // Extract attachments (base64 resources)
    const resources = note.resource || [];
    for (const res of resources) {
      const mime = res.mime?.[0] || 'application/octet-stream';
      const data = res.data?.[0]?._ || res.data?.[0] || '';
      const filename = res['resource-attributes']?.[0]?.['file-name']?.[0]
        || `attachment-${count}-${resources.indexOf(res)}.${mime.split('/')[1] || 'bin'}`;

      const attPath = join(VAULT_DIR, 'attachments', sanitizeFilename(filename));
      await writeFile(attPath, Buffer.from(data, 'base64'));

      // Replace en-media tags in markdown with Obsidian embeds
      markdown = markdown.replace(
        new RegExp(`\\[.*?\\]\\(.*?${escapeRegex(filename)}.*?\\)`, 'g'),
        `![[${sanitizeFilename(filename)}]]`
      );
    }

    const content = fm.join('\n') + '\n' + markdown;
    await writeFile(join(VAULT_DIR, `${title}.md`), content);
    count++;
  }

  console.log(`Migrated ${count} notes from Evernote`);
}

function formatEvernoteDate(d) {
  // ENEX: 20231015T120000Z -> 2023-10-15
  if (!d) return '';
  return `${d.slice(0,4)}-${d.slice(4,6)}-${d.slice(6,8)}`;
}

function escapeRegex(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

migrate().catch(console.error);
```

Run it:
```bash
npm install xml2js turndown
node evernote-to-obsidian.mjs My-Notes.enex ~/my-vault
```

### Step 4: Roam Research JSON Migration

Roam exports as JSON with a flat array of pages containing `children` blocks.

```javascript
// roam-to-obsidian.mjs
import { readFile, writeFile, mkdir } from 'fs/promises';
import { join } from 'path';

const ROAM_JSON = process.argv[2];
const VAULT_DIR = process.argv[3];

function convertBlock(block, depth = 0) {
  let md = '';
  const indent = '  '.repeat(depth);
  const text = convertRoamSyntax(block.string || '');

  if (depth === 0) md += text + '\n\n';
  else md += `${indent}- ${text}\n`;

  for (const child of block.children || []) {
    md += convertBlock(child, depth + 1);
  }
  return md;
}

function convertRoamSyntax(text) {
  // ((block-refs)) -> just the text (can't resolve without full graph)
  text = text.replace(/\(\(([^)]+)\)\)/g, '$1');
  // {{[[TODO]]}} -> - [ ]
  text = text.replace(/\{\{(\[\[)?TODO(\]\])?\}\}/g, '- [ ]');
  // {{[[DONE]]}} -> - [x]
  text = text.replace(/\{\{(\[\[)?DONE(\]\])?\}\}/g, '- [x]');
  // [[page links]] -> [[page links]] (already wikilink format)
  // #[[tag]] -> #tag
  text = text.replace(/#\[\[([^\]]+)\]\]/g, '#$1');
  // ^^highlight^^ -> ==highlight==
  text = text.replace(/\^\^(.+?)\^\^/g, '==$1==');
  return text;
}

async function migrate() {
  const raw = await readFile(ROAM_JSON, 'utf-8');
  const pages = JSON.parse(raw);

  await mkdir(VAULT_DIR, { recursive: true });

  let count = 0;
  for (const page of pages) {
    const title = (page.title || `Untitled-${count}`).replace(/[<>:"/\\|?*]/g, '-');
    const editTime = page['edit-time'] ? new Date(page['edit-time']).toISOString().split('T')[0] : '';

    let content = '---\n';
    content += `title: "${title}"\n`;
    content += `source: roam\n`;
    if (editTime) content += `modified: ${editTime}\n`;
    content += `migrated: ${new Date().toISOString().split('T')[0]}\n`;
    content += '---\n\n';
    content += `# ${title}\n\n`;

    for (const child of page.children || []) {
      content += convertBlock(child);
    }

    await writeFile(join(VAULT_DIR, `${title}.md`), content);
    count++;
  }

  console.log(`Migrated ${count} pages from Roam Research`);
}

migrate().catch(console.error);
```

### Step 5: Bear Notes Migration

Bear exports markdown with Bear-specific tags (`#tag/subtag#`) and image references that need conversion.

```bash
#!/bin/bash
# bear-to-obsidian.sh <bear-export-dir> <vault-dir>
BEAR_DIR="$1"
VAULT_DIR="$2"
ATTACH_DIR="$VAULT_DIR/attachments"
mkdir -p "$ATTACH_DIR"

count=0
for note in "$BEAR_DIR"/*.md; do
  [ -f "$note" ] || continue
  filename=$(basename "$note")

  # Fix Bear nested tags: #project/active# -> #project/active
  # Fix Bear tag spacing: #tag1 #tag2 (already compatible)
  content=$(sed -E 's/#([a-zA-Z0-9/_-]+)#/#\1/g' "$note")

  # Convert Bear image syntax: [image:UUID/filename.png]
  content=$(echo "$content" | sed -E 's/\[image:([^]]+\/)?([^]]+)\]/![[\2]]/g')

  # Add frontmatter if missing
  if ! echo "$content" | head -1 | grep -q '^---'; then
    title=$(echo "$filename" | sed 's/\.md$//')
    content="---
title: \"$title\"
source: bear
migrated: $(date +%Y-%m-%d)
---

$content"
  fi

  echo "$content" > "$VAULT_DIR/$filename"
  count=$((count + 1))
done

# Copy Bear attachments (usually in a parallel directory)
if [ -d "$BEAR_DIR/assets" ]; then
  cp -r "$BEAR_DIR/assets/"* "$ATTACH_DIR/" 2>/dev/null
fi

echo "Migrated $count notes from Bear"
```

### Step 6: Apple Notes Migration

Apple Notes has no native export. Use [apple-notes-liberator](https://github.com/HamburgChimworking/apple-notes-liberator) or export via AppleScript (macOS only):

```bash
# Export Apple Notes to HTML, then convert to Markdown
osascript -e '
tell application "Notes"
  repeat with n in every note
    set fp to (POSIX path of (path to desktop)) & name of n & ".html"
    set f to open for access fp with write permission
    write body of n to f as «class utf8»
    close access f
  end repeat
end tell
'

# Convert exported HTML files to Markdown with frontmatter
npm install turndown
for f in ~/Desktop/*.html; do
  node -e "
    const td = new (require('turndown'))({headingStyle:'atx'});
    const html = require('fs').readFileSync('$f','utf-8');
    const title = require('path').basename('$f','.html');
    const md = '---\ntitle: \"'+title+'\"\nsource: apple-notes\nmigrated: ${new Date().toISOString().split('T')[0]}\n---\n\n'+td.turndown(html);
    require('fs').writeFileSync('$1/'+title+'.md', md);
  " ~/my-vault
done
```

### Step 7: Post-Migration Validation

After any migration, run a validation pass:

```bash
#!/bin/bash
# validate-migration.sh <vault-dir>
VAULT="$1"
echo "=== Migration Validation ==="

# Broken wikilinks (link targets that don't exist as files)
echo "Broken wikilinks:"
grep -roh '\[\[[^]|]*\]\]' "$VAULT"/*.md 2>/dev/null | \
  sed 's/\[\[//;s/\]\]//' | sort -u | while read link; do
    find "$VAULT" -name "${link}.md" -print -quit 2>/dev/null | grep -q . || echo "  MISSING: [[$link]]"
  done

# Orphaned attachments
echo "Orphaned attachments:"
[ -d "$VAULT/attachments" ] && for att in "$VAULT/attachments"/*; do
  attname=$(basename "$att")
  grep -rl "$attname" "$VAULT"/*.md 2>/dev/null | grep -q . || echo "  ORPHAN: $attname"
done

# Encoding issues
echo "Encoding issues:"
find "$VAULT" -name '*.md' -exec file {} \; | grep -v 'UTF-8\|ASCII\|empty' | head -10

# Summary
echo "=== Summary ==="
echo "Notes: $(find "$VAULT" -name '*.md' -not -path '*/.obsidian/*' | wc -l)"
echo "Attachments: $(find "$VAULT/attachments" -type f 2>/dev/null | wc -l)"
echo "Unique tags: $(grep -roh '#[a-zA-Z][a-zA-Z0-9/_-]*' "$VAULT"/*.md 2>/dev/null | sort -u | wc -l)"
```

## Output
- Markdown notes with `[[wikilink]]` syntax and frontmatter (`title`, `source`, `migrated`, tags)
- Attachments relocated to `attachments/` with `![[embed]]` references
- Validation report listing broken links, orphaned attachments, and encoding issues

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Encoding errors (`\ufffd` characters) | Source notes not UTF-8 | Detect encoding with `file` command, convert with `iconv -f LATIN1 -t UTF-8` |
| Broken wikilinks after migration | File renamed or in subfolder | Run validation script; fix with search-and-replace |
| Missing attachments | Source export didn't include them | Re-export from source app with "include attachments" option |
| Duplicate filenames | Same title in different notebooks/folders | Prefix with source folder name: `Notebook - Title.md` |
| ENEX parse failure | Malformed XML (common with large exports) | Split ENEX into smaller chunks; export one notebook at a time |
| Notion CSV issues | Commas or quotes in cell values | Use csv-parse instead of string splitting |

## Examples

**Notion (500 notes)**: Unzip export, run `notion-to-obsidian.mjs`, then `validate-migration.sh`. Typical issues: CSV databases need manual review, nested page hierarchies may need folder restructuring.

**Evernote (2000 notes)**: Export one notebook at a time as ENEX to avoid XML parsing issues. Tags map directly to Obsidian frontmatter tags. Embedded images are extracted as attachments.

**Roam Research**: Wikilinks are already compatible. Main work is converting block references `(())` and `{{TODO}}`/`{{DONE}}` syntax to Obsidian checkboxes.

## Resources
- [Obsidian Importer Plugin](https://help.obsidian.md/import) -- official import tool
- [Notion Export](https://www.notion.so/help/export-your-content)
- [Evernote ENEX Format](https://evernote.com/blog/how-evernotes-xml-export-format-works)
- [Roam Export Guide](https://roamresearch.com/#/app/help/page/export)

## Next Steps
Fix broken links from the validation report. For ongoing sync, see `obsidian-data-handling`.
