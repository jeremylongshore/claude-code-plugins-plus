---
name: figma-hello-world
description: |
  Make your first Figma REST API call to fetch a file and inspect its node tree.
  Use when starting a new Figma integration, testing API connectivity,
  or learning the Figma document structure.
  Trigger with phrases like "figma hello world", "figma first call",
  "figma quick start", "fetch figma file".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(node:*), Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, figma]
compatible-with: claude-code
---

# Figma Hello World

## Overview
Make your first Figma REST API call. Fetch a file's metadata and document tree, then inspect the node structure that represents every layer and object in a Figma design.

## Prerequisites
- Completed `figma-install-auth` setup
- A Figma file key (from the URL: `figma.com/design/<FILE_KEY>/...`)
- `FIGMA_PAT` environment variable set

## Instructions

### Step 1: Fetch a File
```bash
# Get the full document JSON for a file
curl -s -H "X-Figma-Token: ${FIGMA_PAT}" \
  "https://api.figma.com/v1/files/${FIGMA_FILE_KEY}" | jq '{
    name: .name,
    lastModified: .lastModified,
    version: .version,
    pages: [.document.children[] | .name]
  }'
```

Expected output:
```json
{
  "name": "My Design File",
  "lastModified": "2025-03-15T10:30:00Z",
  "version": "1234567890",
  "pages": ["Page 1", "Components", "Tokens"]
}
```

### Step 2: Understand the Node Tree
Every Figma file is a tree of typed nodes:

```
DOCUMENT (root)
├── CANVAS (page)
│   ├── FRAME (container / auto-layout)
│   │   ├── TEXT
│   │   ├── RECTANGLE
│   │   └── INSTANCE (component instance)
│   ├── GROUP
│   │   └── VECTOR
│   ├── COMPONENT (reusable master)
│   └── SECTION
```

Key node types: `DOCUMENT`, `CANVAS`, `FRAME`, `GROUP`, `RECTANGLE`, `ELLIPSE`, `TEXT`, `VECTOR`, `COMPONENT`, `COMPONENT_SET`, `INSTANCE`, `LINE`, `SECTION`, `BOOLEAN_OPERATION`.

### Step 3: TypeScript Hello World
```typescript
// hello-figma.ts
const PAT = process.env.FIGMA_PAT!;
const FILE_KEY = process.env.FIGMA_FILE_KEY!;

interface FigmaNode {
  id: string;
  name: string;
  type: string;
  children?: FigmaNode[];
}

interface FigmaFileResponse {
  name: string;
  lastModified: string;
  version: string;
  document: FigmaNode;
  components: Record<string, { key: string; name: string; description: string }>;
  styles: Record<string, { key: string; name: string; style_type: string }>;
}

async function main() {
  const res = await fetch(
    `https://api.figma.com/v1/files/${FILE_KEY}`,
    { headers: { 'X-Figma-Token': PAT } }
  );

  if (!res.ok) {
    throw new Error(`Figma API error: ${res.status} ${res.statusText}`);
  }

  const file: FigmaFileResponse = await res.json();

  console.log(`File: ${file.name}`);
  console.log(`Last modified: ${file.lastModified}`);
  console.log(`Components: ${Object.keys(file.components).length}`);
  console.log(`Styles: ${Object.keys(file.styles).length}`);

  // Walk the first page and list top-level frames
  const firstPage = file.document.children?.[0];
  if (firstPage) {
    console.log(`\nPage: ${firstPage.name}`);
    for (const child of firstPage.children ?? []) {
      console.log(`  ${child.type}: ${child.name} (${child.id})`);
    }
  }
}

main().catch(console.error);
```

### Step 4: Fetch Specific Nodes
```typescript
// Fetch only specific nodes by ID (faster for large files)
async function fetchNodes(fileKey: string, nodeIds: string[]) {
  const ids = nodeIds.join(',');
  const res = await fetch(
    `https://api.figma.com/v1/files/${fileKey}/nodes?ids=${ids}`,
    { headers: { 'X-Figma-Token': PAT } }
  );
  const data = await res.json();
  // data.nodes is a map: { "nodeId": { document: {...}, components: {...} } }
  return data.nodes;
}

// Node IDs use the format "pageId:frameId" (e.g., "0:1", "123:456")
const nodes = await fetchNodes(FILE_KEY, ['0:1', '2:3']);
```

## Output
- File metadata (name, version, last modified)
- Page names listed from the document tree
- Top-level frames with node IDs and types
- Component and style counts

## Error Handling
| Error | Status | Cause | Solution |
|-------|--------|-------|----------|
| `Not found` | 404 | Invalid file key | Verify the key from the Figma URL |
| `Forbidden` | 403 | No access to file | Check token scopes and file permissions |
| `Rate limited` | 429 | Too many requests | Honor `Retry-After` header |
| Empty `document` | 200 | File has no pages | Check if file was recently created |

## Examples

### Quick Node Counter
```bash
# Count total nodes in a file
curl -s -H "X-Figma-Token: ${FIGMA_PAT}" \
  "https://api.figma.com/v1/files/${FIGMA_FILE_KEY}" \
  | jq '[.. | .id? // empty] | length'
```

### Get File Thumbnail
```bash
curl -s -H "X-Figma-Token: ${FIGMA_PAT}" \
  "https://api.figma.com/v1/files/${FIGMA_FILE_KEY}" \
  | jq -r '.thumbnailUrl'
```

## Resources
- [Figma REST API Introduction](https://developers.figma.com/docs/rest-api/)
- [File Endpoints Reference](https://developers.figma.com/docs/rest-api/file-endpoints/)
- [Node Types Reference](https://developers.figma.com/docs/plugins/api/nodes/)

## Next Steps
Proceed to `figma-local-dev-loop` for setting up a development workflow.
