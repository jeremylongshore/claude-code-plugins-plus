---
name: canva-core-workflow-a
description: |
  Execute the Canva design creation and export pipeline via the Connect API.
  Use when building design creation workflows, exporting designs programmatically,
  or integrating Canva's design tools into your application.
  Trigger with phrases like "canva create design", "canva export",
  "canva design pipeline", "canva generate content".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, canva]
compatible-with: claude-code
---

# Canva Core Workflow A — Design Creation & Export

## Overview

The primary Canva integration workflow: create designs via the REST API, let users edit them in Canva's editor, then export finished designs as PDF/PNG/JPG for downstream use (email campaigns, social posts, print orders).

## Prerequisites

- Completed `canva-install-auth` setup with valid access token
- Scopes: `design:content:write`, `design:content:read`, `design:meta:read`

## Instructions

### Step 1: Create a Design

```typescript
// POST https://api.canva.com/rest/v1/designs
// Rate limit: 20 req/min per user
// Scope: design:content:write

interface CreateDesignRequest {
  design_type:
    | { type: 'preset'; name: 'doc' | 'whiteboard' | 'presentation' }
    | { type: 'custom'; width: number; height: number }; // 40-8000 px
  title?: string;     // 1-255 characters
  asset_id?: string;  // Image asset to insert
}

// Create a social media post (custom dimensions)
const { design } = await canvaAPI('/designs', token, {
  method: 'POST',
  body: JSON.stringify({
    design_type: { type: 'custom', width: 1080, height: 1080 },
    title: 'Instagram Post — Q1 Campaign',
  }),
});

// design.id — unique identifier for all future operations
// design.urls.edit_url — redirect user here to edit (expires 30 days)
// design.urls.view_url — read-only link (expires 30 days)
// design.thumbnail.url — preview image (expires 15 minutes)
```

**Note:** Blank designs are auto-deleted after 7 days if never edited.

### Step 2: Redirect User to Edit

```typescript
// Redirect the user to Canva's editor
// The edit_url is user-specific and expires after 30 days
res.redirect(design.urls.edit_url);
```

### Step 3: Get Design Metadata

```typescript
// GET https://api.canva.com/rest/v1/designs/{designId}
// Rate limit: 100 req/min per user
// Scope: design:meta:read

const { design: meta } = await canvaAPI(`/designs/${designId}`, token);

console.log(`Title: ${meta.title}`);
console.log(`Pages: ${meta.page_count}`);
console.log(`Created: ${new Date(meta.created_at * 1000).toISOString()}`);
console.log(`Updated: ${new Date(meta.updated_at * 1000).toISOString()}`);
console.log(`Owner: user=${meta.owner.user_id}, team=${meta.owner.team_id}`);
```

### Step 4: Export the Finished Design

```typescript
// POST https://api.canva.com/rest/v1/exports
// Rate limits:
//   Per user: 75 exports/5min, 500/24hr
//   Per integration: 750 exports/5min, 5000/24hr
//   Per document: 75 exports/5min
// Scope: design:content:read

// Export as high-quality PDF
const { job } = await canvaAPI('/exports', token, {
  method: 'POST',
  body: JSON.stringify({
    design_id: designId,
    format: {
      type: 'pdf',
      size: 'a4',          // a4 | a3 | letter | legal (Docs only)
      export_quality: 'pro', // regular | pro
    },
  }),
});

// Export as PNG with transparent background
const { job: pngJob } = await canvaAPI('/exports', token, {
  method: 'POST',
  body: JSON.stringify({
    design_id: designId,
    format: {
      type: 'png',
      width: 1200,                // 40-25000 px
      transparent_background: true,
      lossless: true,
      as_single_image: false,     // true = merge all pages into one image
    },
  }),
});

// Export specific pages as JPG
const { job: jpgJob } = await canvaAPI('/exports', token, {
  method: 'POST',
  body: JSON.stringify({
    design_id: designId,
    format: {
      type: 'jpg',
      quality: 85,               // 1-100
      pages: [1, 2],             // specific page numbers
    },
  }),
});
```

### Step 5: Poll for Export Completion

```typescript
// GET https://api.canva.com/rest/v1/exports/{exportId}
async function waitForExport(
  exportId: string,
  token: string,
  maxWaitMs = 60000
): Promise<string[]> {
  const start = Date.now();

  while (Date.now() - start < maxWaitMs) {
    const { job } = await canvaAPI(`/exports/${exportId}`, token);

    if (job.status === 'success') {
      return job.urls; // Array of download URLs, valid 24 hours
    }

    if (job.status === 'failed') {
      // Error codes: license_required | approval_required | internal_failure
      throw new Error(`Export failed: ${job.error.code} — ${job.error.message}`);
    }

    await new Promise(r => setTimeout(r, 2000)); // Poll every 2 seconds
  }

  throw new Error('Export timed out');
}

const downloadUrls = await waitForExport(job.id, token);
```

## Supported Export Formats

| Format | Type | Key Options |
|--------|------|-------------|
| PDF | `pdf` | `size`, `export_quality`, `pages` |
| PNG | `png` | `width`, `height`, `transparent_background`, `lossless`, `as_single_image` |
| JPG | `jpg` | `quality` (1-100), `width`, `height` |
| PPTX | `pptx` | `pages` |
| GIF | `gif` | `width`, `height`, `export_quality` |
| MP4 | `mp4` | `quality` (horizontal_480p, 720p, 1080p, 4k) |

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| 400 Bad Request | Invalid dimensions or format | Check min/max values |
| 401 Unauthorized | Token expired | Refresh via OAuth |
| 403 Forbidden | Missing scope | Enable `design:content:write` |
| 404 Not Found | Design deleted or not owned | Verify design ID |
| 429 Rate Limited | Too many exports | Respect `Retry-After` header |
| `license_required` | Design uses premium elements | User needs Canva Pro |

## Resources

- [Create Design API](https://www.canva.dev/docs/connect/api-reference/designs/create-design/)
- [Export API](https://www.canva.dev/docs/connect/api-reference/exports/create-design-export-job/)
- [Design Types](https://www.canva.dev/docs/connect/api-reference/designs/)

## Next Steps

For asset management and brand template autofill, see `canva-core-workflow-b`.
