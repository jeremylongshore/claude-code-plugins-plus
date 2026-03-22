---
name: canva-core-workflow-b
description: |
  Execute Canva asset management, brand template autofill, and folder organization.
  Use when uploading assets, autofilling brand templates with dynamic data,
  or organizing designs into folders via the Connect API.
  Trigger with phrases like "canva assets", "canva brand template",
  "canva autofill", "canva folders", "canva upload image".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, canva]
compatible-with: claude-code
---

# Canva Core Workflow B — Assets, Autofill & Folders

## Overview

Secondary workflow: upload assets to Canva, autofill brand templates with dynamic data (text, images, charts), and organize content with folders. Autofill requires a Canva Enterprise organization.

## Prerequisites

- Completed `canva-install-auth` with valid access token
- Scopes: `asset:read`, `asset:write`, `brandtemplate:meta:read`, `brandtemplate:content:read`, `design:content:write`, `folder:read`, `folder:write`

## Asset Management

### Upload an Asset (Binary)

```typescript
// POST https://api.canva.com/rest/v1/asset-uploads
// Rate limit: 30 req/min per user
// Scope: asset:write
// Content-Type: application/octet-stream

import { readFileSync } from 'fs';

async function uploadAsset(
  filePath: string,
  name: string,
  token: string
): Promise<{ id: string; status: string }> {
  // Asset name must be Base64-encoded, max 50 chars unencoded
  const nameBase64 = Buffer.from(name).toString('base64');
  const fileData = readFileSync(filePath);

  const res = await fetch('https://api.canva.com/rest/v1/asset-uploads', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/octet-stream',
      'Asset-Upload-Metadata': JSON.stringify({ name_base64: nameBase64 }),
    },
    body: fileData,
  });

  if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
  return res.json();
}

// Upload returns a job — poll for asset ID
const uploadJob = await uploadAsset('./hero-banner.png', 'Hero Banner Q1', token);
```

### Upload an Asset via URL

```typescript
// POST https://api.canva.com/rest/v1/url-asset-uploads
// Rate limit: 30 req/min per user

const { job } = await canvaAPI('/url-asset-uploads', token, {
  method: 'POST',
  body: JSON.stringify({
    name: 'Product Photo',
    url: 'https://example.com/images/product-shot.jpg',
  }),
});
// Poll GET /v1/url-asset-uploads/{jobId} for completion
```

### Get, Update, Delete Assets

```typescript
// GET /v1/assets/{assetId} — scope: asset:read
const asset = await canvaAPI(`/assets/${assetId}`, token);

// PATCH /v1/assets/{assetId} — scope: asset:write
await canvaAPI(`/assets/${assetId}`, token, {
  method: 'PATCH',
  body: JSON.stringify({ name: 'Updated Name', tags: ['brand', 'q1'] }),
});

// DELETE /v1/assets/{assetId} — scope: asset:write
await canvaAPI(`/assets/${assetId}`, token, { method: 'DELETE' });
```

## Brand Template Autofill

### Step 1: List Available Brand Templates

```typescript
// GET https://api.canva.com/rest/v1/brand-templates
// Rate limit: 100 req/min per user
// Scope: brandtemplate:meta:read
// Requires: Canva Enterprise organization

const templates = await canvaAPI('/brand-templates', token);

for (const tmpl of templates.items) {
  console.log(`${tmpl.title} — ID: ${tmpl.id}`);
}
```

### Step 2: Get Template Dataset (Autofillable Fields)

```typescript
// GET https://api.canva.com/rest/v1/brand-templates/{templateId}/dataset
// Scope: brandtemplate:content:read

const { dataset } = await canvaAPI(
  `/brand-templates/${templateId}/dataset`, token
);

// dataset is a map of field_name → { type: 'text' | 'image' }
for (const [field, config] of Object.entries(dataset)) {
  console.log(`Field: ${field}, Type: ${config.type}`);
}
// Example output:
// Field: headline, Type: text
// Field: hero_image, Type: image
// Field: price, Type: text
```

### Step 3: Create Design from Template via Autofill

```typescript
// POST https://api.canva.com/rest/v1/autofills
// Rate limit: 60 req/min per user
// Scope: design:content:write

const { job } = await canvaAPI('/autofills', token, {
  method: 'POST',
  body: JSON.stringify({
    brand_template_id: templateId,
    title: 'March Newsletter — Generated',
    data: {
      headline: {
        type: 'text',
        text: 'Spring Collection Is Here',
      },
      hero_image: {
        type: 'image',
        asset_id: uploadedAssetId,  // From asset upload step
      },
      price: {
        type: 'text',
        text: '$29.99',
      },
    },
  }),
});

// Poll for completion — GET /v1/autofills/{jobId}
let autofillJob = job;
while (autofillJob.status === 'in_progress') {
  await new Promise(r => setTimeout(r, 2000));
  const poll = await canvaAPI(`/autofills/${autofillJob.id}`, token);
  autofillJob = poll.job;
}

if (autofillJob.status === 'success') {
  const newDesign = autofillJob.result.design;
  console.log(`Autofilled design: ${newDesign.id}`);
  console.log(`Edit: ${newDesign.urls.edit_url}`);
}
```

### Autofill with Chart Data

```typescript
const { job } = await canvaAPI('/autofills', token, {
  method: 'POST',
  body: JSON.stringify({
    brand_template_id: templateId,
    title: 'Q1 Report',
    data: {
      sales_chart: {
        type: 'chart',
        chart_data: {
          rows: [
            { cells: [{ type: 'string', value: 'Jan' }, { type: 'number', value: 45000 }] },
            { cells: [{ type: 'string', value: 'Feb' }, { type: 'number', value: 52000 }] },
            { cells: [{ type: 'string', value: 'Mar' }, { type: 'number', value: 61000 }] },
          ],
        },
      },
    },
  }),
});
// Chart data: max 100 rows, 20 columns per row
```

## Folder Management

```typescript
// Create a folder — POST /v1/folders, scope: folder:write, 20 req/min
const { folder } = await canvaAPI('/folders', token, {
  method: 'POST',
  body: JSON.stringify({
    name: 'Q1 Campaign Assets',     // 1-255 chars
    parent_folder_id: 'root',       // "root" | "uploads" | folder ID
  }),
});
console.log(`Folder created: ${folder.id}`);

// List folder contents — GET /v1/folders/{folderId}/items, scope: folder:read
const items = await canvaAPI(`/folders/${folder.id}/items`, token);

// Move item to folder — PATCH /v1/folders/move, scope: folder:write
await canvaAPI('/folders/move', token, {
  method: 'PATCH',
  body: JSON.stringify({
    item_id: designId,
    to_folder_id: folder.id,
  }),
});
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| 400 `Design title invalid` | Title empty or > 255 chars | Validate input |
| 403 Forbidden | Not Enterprise org (autofill) | Requires Canva Enterprise |
| 404 Not Found | Template ID doesn't exist | Verify template ID |
| `file_too_big` | Asset exceeds size limit | Compress or resize |
| `import_failed` | Unsupported file format | Check supported formats |
| `autofill_error` | Field name mismatch | Check dataset first |

## Resources

- [Assets API](https://www.canva.dev/docs/connect/api-reference/assets/)
- [Brand Templates API](https://www.canva.dev/docs/connect/api-reference/brand-templates/)
- [Autofill Guide](https://www.canva.dev/docs/connect/autofill-guide/)
- [Folders API](https://www.canva.dev/docs/connect/api-reference/folders/)

## Next Steps

For common errors, see `canva-common-errors`.
