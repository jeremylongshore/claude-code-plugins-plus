---
name: onenote-core-workflow-a
description: 'Full CRUD lifecycle for OneNote notebooks, section groups, sections,
  and pages via Graph API.

  Use when building notebook management features, creating page hierarchies, or working
  with XHTML content.

  Trigger with "onenote crud", "onenote page management", "onenote notebook workflow".

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
# OneNote — Full CRUD Lifecycle (Notebooks, Sections, Pages)

## Overview

OneNote's hierarchy — Notebook, Section Group, Section, Page — maps cleanly to Graph API endpoints, but the implementation has sharp edges. Section groups created via API sometimes don't render in the desktop client. Page content must be strict XHTML with self-closing tags, and the HTML you send in differs from the HTML you get back. This skill covers the full create/read/update/delete lifecycle with production-safe patterns for every level of the hierarchy.

Key pain points addressed:
- Page content requires XHTML (all tags must close, UTF-8 encoded, no `rowspan`/`colspan`)
- Section groups support API nesting depths that the desktop app cannot render beyond two levels
- Output HTML from `GET /pages/{id}/content` contains Graph-injected `data-id` attributes and rewritten image URLs that differ from your input HTML
- `PATCH` page updates use a JSON array with `target`/`action`/`content` — not raw HTML

## Prerequisites

- Azure app registration with delegated permissions: `Notes.ReadWrite` or `Notes.ReadWrite.All`
- App-only auth deprecated March 31, 2025 — use delegated auth only (DeviceCodeCredential or InteractiveBrowserCredential)
- Python: `pip install msgraph-sdk azure-identity`
- Node/TypeScript: `npm install @microsoft/microsoft-graph-client @azure/identity @azure/msal-node`

## Instructions

### Step 1 — Authenticate with Delegated Credentials

**TypeScript:**
```typescript
import { Client } from "@microsoft/microsoft-graph-client";
import { TokenCredentialAuthenticationProvider } from "@microsoft/microsoft-graph-client/authProviders/azureTokenCredentials";
import { DeviceCodeCredential } from "@azure/identity";

const credential = new DeviceCodeCredential({
  clientId: process.env.AZURE_CLIENT_ID!,
  tenantId: process.env.AZURE_TENANT_ID!,
});
const scopes = ["Notes.ReadWrite"];
const authProvider = new TokenCredentialAuthenticationProvider(credential, { scopes });
const client = Client.initWithMiddleware({ authProvider });
```

**Python:**
```python
from azure.identity import DeviceCodeCredential
from msgraph import GraphServiceClient

credential = DeviceCodeCredential(
    client_id=os.environ["AZURE_CLIENT_ID"],
    tenant_id=os.environ["AZURE_TENANT_ID"],
)
scopes = ["Notes.ReadWrite"]
client = GraphServiceClient(credentials=credential, scopes=scopes)
```

### Step 2 — Create a Notebook

```typescript
const notebook = await client.api("/me/onenote/notebooks").post({
  displayName: "Project Notes Q2 2026",
});
// notebook.id is the resource identifier for all child operations
console.log(`Created notebook: ${notebook.id}`);
```

Notebook names must be unique per user. Attempting to create a duplicate returns `400 Bad Request` with code `20117`.

### Step 3 — Create Section Groups and Sections

```typescript
// Create a section group (top-level organization)
const group = await client.api(
  `/me/onenote/notebooks/${notebook.id}/sectionGroups`
).post({ displayName: "Engineering" });

// Create a section inside the group
const section = await client.api(
  `/me/onenote/sectionGroups/${group.id}/sections`
).post({ displayName: "Sprint 1" });

// Create a section directly in the notebook (no group)
const standaloneSection = await client.api(
  `/me/onenote/notebooks/${notebook.id}/sections`
).post({ displayName: "Quick Notes" });
```

> **Gotcha:** The API allows nesting section groups three or more levels deep, but the OneNote desktop app only renders two levels. The web app may show deeper nesting inconsistently. Stick to a maximum of two levels for cross-client compatibility.

### Step 4 — Create a Page with XHTML Content

OneNote pages use strict XHTML. Every tag must close. Use `data-tag` attributes for checkboxes and note tags.

```typescript
const htmlContent = `<!DOCTYPE html>
<html lang="en-US">
<head>
  <title>Sprint Planning - March 2026</title>
  <meta name="created" content="2026-03-23T10:00:00-05:00" />
</head>
<body>
  <h1>Sprint Planning</h1>
  <p>Attendees: Alice, Bob, Charlie</p>
  <h2>Action Items</h2>
  <ul>
    <li data-tag="to-do">Deploy feature X by Friday</li>
    <li data-tag="to-do">Review PR #488</li>
    <li data-tag="to-do:completed">Set up staging environment</li>
  </ul>
  <table>
    <tr><td>Task</td><td>Owner</td><td>Due</td></tr>
    <tr><td>API integration</td><td>Alice</td><td>March 28</td></tr>
  </table>
  <p>Next meeting: <time datetime="2026-03-30T10:00:00-05:00">March 30</time></p>
</body>
</html>`;

const page = await client.api(
  `/me/onenote/sections/${section.id}/pages`
).header("Content-Type", "text/html").post(htmlContent);
console.log(`Page created: ${page.id} — "${page.title}"`);
```

**XHTML rules that cause silent failures if violated:**
- All tags must self-close or have closing tags (`<br />`, not `<br>`)
- No `rowspan` or `colspan` on `<td>` — use separate rows instead
- `<img>` tags must include `alt` attribute
- Content must be UTF-8 encoded

### Step 5 — Retrieve Page Content

```typescript
// Metadata (title, timestamps, parent info) — fast, cacheable
const metadata = await client.api(`/me/onenote/pages/${page.id}`).get();

// Full HTML content — separate endpoint, slower
const content = await client.api(`/me/onenote/pages/${page.id}/content`).get();
// content is a ReadableStream — pipe or buffer it
```

> **Important:** The HTML returned by `GET /content` differs from your input. Graph injects `data-id` attributes on every element, rewrites image `src` URLs to Graph resource endpoints, and may restructure your table markup. Never diff input vs output HTML for change detection — compare `lastModifiedDateTime` instead.

### Step 6 — Update Page Content (PATCH)

Updates use a JSON array describing targeted changes, not raw HTML replacement:

```typescript
await client.api(`/me/onenote/pages/${page.id}/content`).patch([
  {
    target: "body",
    action: "append",
    content: "<p>Update: Feature X deployed successfully.</p>",
  },
  {
    target: "#action-items",
    action: "replace",
    content: '<ul><li data-tag="to-do:completed">All items complete</li></ul>',
  },
]);
```

Valid `action` values: `append`, `replace`, `delete`, `insert`, `prepend`. The `target` is a CSS selector matching `data-id` attributes from the output HTML — you must `GET /content` first to obtain valid targets.

### Step 7 — List and Filter Pages with OData

```typescript
const pages = await client.api("/me/onenote/sections/{sectionId}/pages")
  .select("id,title,lastModifiedDateTime,createdDateTime")
  .top(25)
  .orderby("lastModifiedDateTime desc")
  .get();

for (const p of pages.value) {
  console.log(`${p.title} — Last modified: ${p.lastModifiedDateTime}`);
}
```

### Step 8 — Delete a Page

```typescript
await client.api(`/me/onenote/pages/${page.id}`).delete();
// Returns 204 No Content on success
// Deleted pages may still appear in LIST results for up to 30 minutes
```

## Output

Successful CRUD operations return:
- **Create notebook/section/page:** `201 Created` with resource JSON (includes `id`, `self`, `createdDateTime`)
- **Get content:** `200 OK` with XHTML stream
- **Patch:** `204 No Content` on success
- **Delete:** `204 No Content` on success

## Error Handling

| Status | Cause | Fix |
|--------|-------|-----|
| 400 | Invalid XHTML, unclosed tags, duplicate notebook name | Validate HTML before sending; check notebook name uniqueness |
| 403 | Missing `Notes.ReadWrite` permission, wrong tenant | Verify Azure app permissions and consent status |
| 404 | Notebook/section/page deleted or wrong ID | Confirm resource exists with a `GET` before mutation |
| 429 | Rate limit hit (600/min per user) | Read `Retry-After` header, wait that many seconds |
| 507 | Section page limit exceeded | Archive old pages to a new section; see `onenote-performance-tuning` |

## Examples

**Python — Create notebook and page:**
```python
notebook = await client.me.onenote.notebooks.post(
    {"displayName": "Python Notebook"}
)
sections = await client.me.onenote.notebooks.by_notebook_id(
    notebook.id
).sections.post({"displayName": "Notes"})

html = """<!DOCTYPE html>
<html><head><title>Hello from Python</title></head>
<body><p>Created via msgraph-sdk.</p></body></html>"""

page = await client.me.onenote.sections.by_onenote_section_id(
    sections.id
).pages.post(html)
```

**TypeScript — Multipart page with embedded image:**
```typescript
const boundary = "MyPartBoundary";
const body = [
  `--${boundary}`,
  'Content-Disposition: form-data; name="Presentation"',
  "Content-Type: text/html",
  "",
  '<!DOCTYPE html><html><head><title>With Image</title></head>',
  '<body><p>See diagram:</p><img src="name:diagram" alt="Architecture" /></body></html>',
  `--${boundary}`,
  'Content-Disposition: form-data; name="diagram"',
  "Content-Type: image/png",
  "",
  imageBuffer.toString("binary"),
  `--${boundary}--`,
].join("\r\n");

await client.api(`/me/onenote/sections/${sectionId}/pages`)
  .header("Content-Type", `multipart/form-data; boundary=${boundary}`)
  .post(body);
```

## Resources

- [OneNote API Overview](https://learn.microsoft.com/en-us/graph/api/resources/onenote-api-overview)
- [Create Pages](https://learn.microsoft.com/en-us/graph/onenote-create-page)
- [Update Pages](https://learn.microsoft.com/en-us/graph/onenote-update-page)
- [Input/Output HTML](https://learn.microsoft.com/en-us/graph/onenote-input-output-html)
- [Note Tags](https://learn.microsoft.com/en-us/graph/onenote-note-tags)
- [Images & Files](https://learn.microsoft.com/en-us/graph/onenote-images-files)
- [Azure App Registration](https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps)

## Next Steps

- See `onenote-core-workflow-b` for search, pagination, and cross-notebook queries
- See `onenote-performance-tuning` for large notebook optimization and image upload limits
- See `onenote-rate-limits` for throttling patterns when doing bulk page creation
