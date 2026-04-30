---
name: onenote-hello-world
description: 'Create your first OneNote notebook, section, and page with correct XHTML
  content.

  Use when starting a new OneNote integration or testing Graph API connectivity.

  Trigger with "onenote hello world", "first onenote page", "create onenote notebook".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- onenote
- microsoft
compatibility: Designed for Claude Code
---
# OneNote Hello World

## Overview

Create your first OneNote notebook, section, and page through the Graph API. The critical pitfall this skill addresses: OneNote pages require strict XHTML (not regular HTML). Missing closing tags, unsupported attributes, or table features like `rowspan`/`colspan` cause silent content corruption where the API returns 200 OK but the page renders incorrectly or with missing content.

This skill walks through the full creation chain — notebook, section, page — with correct XHTML, then reads back the content to demonstrate that output HTML differs from input HTML.

## Prerequisites

- Completed `onenote-install-auth` — you have a working `GraphServiceClient` (Python) or `Client` (TypeScript)
- Azure AD app with `Notes.ReadWrite` permission scope
- Node.js 18+ or Python 3.10+

## Instructions

### Step 1: Create a Notebook

```typescript
// TypeScript — create a new notebook
const notebook = await client.api("/me/onenote/notebooks").post({
  displayName: "Dev Integration Test"
});
console.log(`Notebook created: ${notebook.displayName} (${notebook.id})`);
// Save notebook.id — you need it for creating sections
```

```python
# Python — create a new notebook
from msgraph.generated.models.notebook import Notebook

request_body = Notebook(display_name="Dev Integration Test")
notebook = await client.me.onenote.notebooks.post(request_body)
print(f"Notebook created: {notebook.display_name} ({notebook.id})")
```

**Naming rules:** Notebook names must be unique per user. If a notebook with the same name exists, you get a 400 error with code `20117`. Use a timestamp suffix for test notebooks: `f"Test-{datetime.now().isoformat()}"`.

### Step 2: Create a Section

```typescript
// TypeScript — create a section inside the notebook
const section = await client
  .api(`/me/onenote/notebooks/${notebook.id}/sections`)
  .post({ displayName: "Getting Started" });
console.log(`Section created: ${section.displayName} (${section.id})`);
```

```python
# Python — create a section
from msgraph.generated.models.onenote_section import OnenoteSection

section_body = OnenoteSection(display_name="Getting Started")
section = await client.me.onenote.notebooks.by_notebook_id(
    notebook.id
).sections.post(section_body)
print(f"Section created: {section.display_name} ({section.id})")
```

### Step 3: Create a Page with Correct XHTML

This is where most integrations break. OneNote requires XHTML — every tag must close, the document must be UTF-8, and several HTML features are silently dropped.

**VALID XHTML (this works):**
```html
<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <title>Sprint Planning — March 2026</title>
    <meta name="created" content="2026-03-23T10:00:00-05:00" />
  </head>
  <body>
    <h1>Sprint Planning Notes</h1>
    <p>Attendees: Alice, Bob, Charlie</p>

    <h2>Action Items</h2>
    <ul>
      <li data-tag="to-do">Deploy feature X by Friday</li>
      <li data-tag="to-do">Review PR #488</li>
      <li data-tag="to-do:completed">Set up CI pipeline</li>
    </ul>

    <h2>Decisions</h2>
    <p>Approved migration to delegated auth. Deadline: <strong>April 15</strong>.</p>

    <table>
      <tr>
        <td>Task</td>
        <td>Owner</td>
        <td>Status</td>
      </tr>
      <tr>
        <td>Auth migration</td>
        <td>Alice</td>
        <td>In progress</td>
      </tr>
    </table>

    <br />
    <p><em>Next meeting: March 30, 2026</em></p>
  </body>
</html>
```

**INVALID HTML (common mistakes that cause silent failures):**
```html
<!-- WRONG: unclosed tags — content after <br> may be lost -->
<p>Line one<br>Line two</p>

<!-- CORRECT: self-closing tags -->
<p>Line one<br />Line two</p>

<!-- WRONG: rowspan/colspan — silently dropped, table layout breaks -->
<td rowspan="2">Merged cell</td>

<!-- CORRECT: use separate rows, no merge attributes -->
<td>Row 1</td>

<!-- WRONG: <img> without self-close -->
<img src="https://example.com/chart.png" alt="Chart">

<!-- CORRECT: self-closing img -->
<img src="https://example.com/chart.png" alt="Chart" />

<!-- WRONG: style attributes with unsupported CSS — silently ignored -->
<p style="display: flex; gap: 8px;">Content</p>

<!-- CORRECT: only supported inline styles -->
<p style="color: #333; font-size: 14pt;">Content</p>
```

**Send the page:**
```typescript
// TypeScript — create page with XHTML content
const xhtml = `<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml">
  <head><title>Hello from Graph API</title></head>
  <body>
    <h1>Hello World</h1>
    <p>Created via Microsoft Graph API at ${new Date().toISOString()}</p>
    <ul>
      <li data-tag="to-do">First task</li>
      <li data-tag="to-do">Second task</li>
    </ul>
  </body>
</html>`;

const page = await client
  .api(`/me/onenote/sections/${section.id}/pages`)
  .header("Content-Type", "text/html")
  .post(xhtml);

console.log(`Page created: ${page.title} (${page.id})`);
```

```python
# Python — create page via raw HTTP (SDK page creation uses HTML body)
import httpx

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "text/html",
}
xhtml = """<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml">
  <head><title>Hello from Graph API</title></head>
  <body>
    <h1>Hello World</h1>
    <p>Created via Microsoft Graph API</p>
    <ul>
      <li data-tag="to-do">First task</li>
    </ul>
  </body>
</html>"""

resp = httpx.post(
    f"https://graph.microsoft.com/v1.0/me/onenote/sections/{section.id}/pages",
    headers=headers,
    content=xhtml,
)
resp.raise_for_status()
page = resp.json()
print(f"Page created: {page['title']} ({page['id']})")
```

### Step 4: Read Back Page Content

The HTML you get back from `GET /pages/{id}/content` is NOT the same as what you sent. Graph normalizes the HTML, adds `data-id` attributes, wraps content in `div` elements, and may reorder attributes.

```typescript
// TypeScript — read page content back
// Note: small delay needed — page indexing is async
await new Promise((r) => setTimeout(r, 2000));

const content = await client
  .api(`/me/onenote/pages/${page.id}/content`)
  .get();

// content is an HTML string — not the same as what you sent
// Graph adds: data-id attributes, absolute positioning, div wrappers
console.log("Page HTML (first 500 chars):", content.substring(0, 500));
```

```python
# Python — read page content
import asyncio
await asyncio.sleep(2)  # Page indexing is async

resp = httpx.get(
    f"https://graph.microsoft.com/v1.0/me/onenote/pages/{page['id']}/content",
    headers={"Authorization": f"Bearer {token}"},
)
print("Output HTML (first 500 chars):", resp.text[:500])
# Notice: output HTML has data-id attrs, absolute positions, normalized structure
```

### Valid data-tag Values for Checklists

| data-tag value | Renders as |
|---------------|------------|
| `to-do` | Unchecked checkbox |
| `to-do:completed` | Checked checkbox |
| `important` | Star icon |
| `question` | Question mark icon |
| `critical` | Red exclamation |
| `remember-for-later` | Bookmark icon |
| `definition` | Definition marker |
| `highlight` | Yellow highlight |

## Output

After completing these steps you will have:
- A new OneNote notebook with a section and page
- A page with correctly formatted XHTML content including checklists
- Understanding of input vs output HTML differences
- Knowledge of XHTML rules that prevent silent content corruption

## Error Handling

| Error | Code | Root Cause | Solution |
|-------|------|------------|----------|
| Duplicate notebook name | 400 (`20117`) | Notebook with same `displayName` exists | Append timestamp or check existence first |
| Invalid HTML | 400 | Malformed XHTML — unclosed tags, bad encoding | Validate XHTML before sending; use XML parser |
| Section not found | 404 | Notebook ID or section ID is wrong | Re-fetch notebook, verify ID matches |
| Empty page content | 200 (empty body) | Page created but content >4MB | Check payload size before POST |
| Missing title | 400 | `<title>` tag missing from `<head>` | Always include `<head><title>...</title></head>` |
| Content encoding error | 400 | Non-UTF-8 characters in HTML | Ensure UTF-8 encoding, strip BOM markers |

## Examples

**Minimal valid page (smallest possible):**
```html
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
  <head><title>Minimal Page</title></head>
  <body><p>Content here</p></body>
</html>
```

**Page with image from URL:**
```html
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
  <head><title>Page with Image</title></head>
  <body>
    <h1>Architecture Diagram</h1>
    <img src="https://example.com/diagram.png" alt="System architecture" />
    <p>Figure 1: Current system architecture</p>
  </body>
</html>
```

## Resources

- [OneNote Create Pages](https://learn.microsoft.com/en-us/graph/onenote-create-page)
- [Input/Output HTML Reference](https://learn.microsoft.com/en-us/graph/onenote-input-output-html)
- [Note Tags Reference](https://learn.microsoft.com/en-us/graph/onenote-note-tags)
- [Images and Files in OneNote](https://learn.microsoft.com/en-us/graph/onenote-images-files)
- [Graph Explorer](https://developer.microsoft.com/en-us/graph/graph-explorer)
- [OneNote API Overview](https://learn.microsoft.com/en-us/graph/api/resources/onenote-api-overview)

## Next Steps

- Use `onenote-sdk-patterns` to add retry logic and rate limit handling
- See `onenote-common-errors` when page creation returns unexpected errors
- See `onenote-local-dev-loop` to set up mock responses for rapid iteration
