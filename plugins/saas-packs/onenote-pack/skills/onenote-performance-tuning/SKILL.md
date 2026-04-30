---
name: onenote-performance-tuning
description: 'Optimize OneNote Graph API performance for large notebooks, image handling,
  and batch operations.

  Use when dealing with slow API responses, large notebooks, image uploads, or HTTP
  507 errors.

  Trigger with "onenote performance", "onenote slow", "onenote large notebook", "onenote
  image upload".

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
# OneNote — Performance Tuning & Optimization

## Overview

OneNote performance degrades predictably at scale: notebooks with 100+ sections take 3-5 seconds per API call when using `$expand`, pages with embedded images over 4MB fail silently, and sections hitting the page limit return `507 Insufficient Storage`. Image uploads are capped at 25MB per multipart part, and requesting full page content for hundreds of pages without `$select` can exhaust your rate budget in seconds.

This skill provides tested patterns for every performance bottleneck: selective `$expand` and `$select` for minimal payloads, image compression before upload, batch requests via `$batch`, pagination with `$top` to avoid loading thousands of pages, and caching strategies that invalidate on change detection.

Key pain points addressed:
- Full `$expand=sections($expand=pages)` on large notebooks can take 10+ seconds and return multi-MB responses
- Image uploads silently fail when a single multipart part exceeds 25MB — no error, just missing image
- `507 Insufficient Storage` when a section hits its page limit (approximately 5,000 pages)
- Page content retrieval (`GET /pages/{id}/content`) is 5-10x slower than metadata-only requests

## Prerequisites

- Azure app registration with delegated permissions: `Notes.ReadWrite`
- App-only auth deprecated March 31, 2025 — use delegated auth only
- Python: `pip install msgraph-sdk azure-identity Pillow` (Pillow for image compression)
- Node/TypeScript: `npm install @microsoft/microsoft-graph-client @azure/identity @azure/msal-node sharp` (sharp for image compression)

## Instructions

### Step 1 — Use $select to Minimize Payload Size

Every Graph API call should specify `$select` to return only the fields you need. The default response includes navigation properties, OData metadata, and verbose timestamps that inflate payloads:

```typescript
// BAD — returns ~2KB per page with all metadata
const pages = await client.api("/me/onenote/pages").get();

// GOOD — returns ~200 bytes per page with only needed fields
const pages = await client.api("/me/onenote/pages")
  .select("id,title,lastModifiedDateTime")
  .get();

// For notebooks, avoid expanding everything
// BAD — can take 10+ seconds on large notebooks
const notebooks = await client.api("/me/onenote/notebooks")
  .expand("sections($expand=pages)")
  .get();

// GOOD — get structure first, then drill into sections on demand
const notebooks = await client.api("/me/onenote/notebooks")
  .select("id,displayName,lastModifiedDateTime,sectionsUrl")
  .get();
```

Payload size comparison for a notebook with 50 sections and 500 pages:

| Query | Response Size | Response Time |
|-------|--------------|---------------|
| Full `$expand` | ~800KB | 5-10s |
| `$select` on notebook only | ~2KB | 200ms |
| `$select` + `$top(10)` sections | ~1KB | 150ms |

### Step 2 — Paginate Large Sections

Sections can accumulate thousands of pages. Always use `$top` to limit initial loads:

```typescript
async function* iteratePages(client: any, sectionId: string, pageSize: number = 50) {
  let url: string | null =
    `/me/onenote/sections/${sectionId}/pages?$select=id,title,lastModifiedDateTime&$orderby=lastModifiedDateTime desc&$top=${pageSize}`;

  while (url) {
    const response = await client.api(url).get();
    const pages = response.value ?? [];
    for (const page of pages) {
      yield page;
    }
    // Stop if we got fewer than requested
    if (pages.length < pageSize) break;
    url = response["@odata.nextLink"] ?? null;
  }
}

// Usage — process pages lazily
for await (const page of iteratePages(client, sectionId)) {
  console.log(`Processing: ${page.title}`);
  if (shouldStop(page)) break; // Can bail early
}
```

### Step 3 — Image Upload with Size Validation

OneNote accepts images via multipart form data. Each part is limited to 25MB. Images larger than 4MB in the rendered page can cause performance issues in the client. Always validate and compress before upload:

```typescript
import sharp from "sharp";

interface ImageUploadResult {
  success: boolean;
  originalSize: number;
  compressedSize: number;
  error?: string;
}

async function prepareImageForUpload(
  imageBuffer: Buffer,
  maxSizeBytes: number = 4 * 1024 * 1024, // 4MB target for good page performance
  hardLimit: number = 25 * 1024 * 1024     // 25MB absolute limit per multipart part
): Promise<{ buffer: Buffer; result: ImageUploadResult }> {
  const originalSize = imageBuffer.length;

  if (originalSize > hardLimit) {
    return {
      buffer: imageBuffer,
      result: { success: false, originalSize, compressedSize: originalSize,
        error: `Image exceeds 25MB hard limit (${(originalSize / 1024 / 1024).toFixed(1)}MB)` },
    };
  }

  if (originalSize <= maxSizeBytes) {
    return {
      buffer: imageBuffer,
      result: { success: true, originalSize, compressedSize: originalSize },
    };
  }

  // Progressively compress: reduce quality, then resize
  let compressed = imageBuffer;
  const qualities = [80, 60, 40];

  for (const quality of qualities) {
    compressed = await sharp(imageBuffer)
      .jpeg({ quality, progressive: true })
      .toBuffer();
    if (compressed.length <= maxSizeBytes) break;
  }

  // If still too large, resize
  if (compressed.length > maxSizeBytes) {
    const metadata = await sharp(imageBuffer).metadata();
    const scale = Math.sqrt(maxSizeBytes / compressed.length);
    compressed = await sharp(imageBuffer)
      .resize(Math.round((metadata.width ?? 1920) * scale))
      .jpeg({ quality: 60 })
      .toBuffer();
  }

  return {
    buffer: compressed,
    result: { success: true, originalSize, compressedSize: compressed.length },
  };
}
```

**Supported image formats:** TIFF, PNG, GIF, JPEG, BMP. OneNote does not support WebP or AVIF — convert before uploading.

### Step 4 — Multipart Page Creation with Images

```typescript
async function createPageWithImage(
  client: any,
  sectionId: string,
  title: string,
  htmlBody: string,
  imageName: string,
  imageBuffer: Buffer
): Promise<any> {
  // Validate and compress image
  const { buffer, result } = await prepareImageForUpload(imageBuffer);
  if (!result.success) throw new Error(result.error);

  const boundary = `OneNoteBoundary${Date.now()}`;
  const body = [
    `--${boundary}`,
    'Content-Disposition: form-data; name="Presentation"',
    "Content-Type: text/html",
    "",
    `<!DOCTYPE html><html><head><title>${title}</title></head>`,
    `<body>${htmlBody}<img src="name:${imageName}" alt="${imageName}" /></body></html>`,
    `--${boundary}`,
    `Content-Disposition: form-data; name="${imageName}"`,
    "Content-Type: image/jpeg",
    "",
    buffer.toString("binary"),
    `--${boundary}--`,
  ].join("\r\n");

  return client.api(`/me/onenote/sections/${sectionId}/pages`)
    .header("Content-Type", `multipart/form-data; boundary=${boundary}`)
    .post(body);
}
```

### Step 5 — Batch Requests for Bulk Operations

The `$batch` endpoint processes up to 20 operations per request. This is the single most effective optimization for bulk workloads — it reduces HTTP overhead and counts as one request against rate limits:

```typescript
async function batchGetPageMetadata(
  client: any,
  pageIds: string[]
): Promise<Map<string, any>> {
  const results = new Map<string, any>();
  const BATCH_SIZE = 20;

  for (let i = 0; i < pageIds.length; i += BATCH_SIZE) {
    const chunk = pageIds.slice(i, i + BATCH_SIZE);
    const batchBody = {
      requests: chunk.map((id, idx) => ({
        id: String(idx),
        method: "GET",
        url: `/me/onenote/pages/${id}?$select=id,title,lastModifiedDateTime`,
      })),
    };

    const response = await client.api("/$batch").post(batchBody);

    for (const item of response.responses) {
      if (item.status === 200) {
        results.set(item.body.id, item.body);
      } else if (item.status === 404) {
        // Page was deleted — skip
        console.warn(`Page ${chunk[parseInt(item.id)]} not found`);
      }
    }
  }

  return results;
}

// 200 pages = 10 HTTP requests instead of 200
const metadata = await batchGetPageMetadata(client, twoHundredPageIds);
```

### Step 6 — HTTP 507 Detection and Mitigation

When a section reaches its page limit (approximately 5,000 pages), new page creation returns `507 Insufficient Storage`:

```typescript
async function createPageSafe(
  client: any,
  sectionId: string,
  html: string,
  fallbackNotebookId?: string
): Promise<{ page: any; usedFallback: boolean }> {
  try {
    const page = await client.api(
      `/me/onenote/sections/${sectionId}/pages`
    ).header("Content-Type", "text/html").post(html);
    return { page, usedFallback: false };
  } catch (err: any) {
    if (err.statusCode === 507 && fallbackNotebookId) {
      console.warn(`Section ${sectionId} is full — creating overflow section`);

      // Create a new section with a timestamp suffix
      const overflowSection = await client.api(
        `/me/onenote/notebooks/${fallbackNotebookId}/sections`
      ).post({
        displayName: `Overflow - ${new Date().toISOString().slice(0, 10)}`,
      });

      const page = await client.api(
        `/me/onenote/sections/${overflowSection.id}/pages`
      ).header("Content-Type", "text/html").post(html);

      return { page, usedFallback: true };
    }
    throw err;
  }
}
```

### Step 7 — Caching Strategy

Cache notebook and section structure (which changes infrequently) while keeping page data fresh:

```typescript
class OneNoteCache {
  private cache = new Map<string, { data: any; expiry: number }>();

  private readonly TTL = {
    notebooks: 5 * 60_000,    // 5 minutes — structure rarely changes
    sections: 5 * 60_000,     // 5 minutes — sections rarely added/removed
    pageList: 30_000,          // 30 seconds — pages change frequently
    pageContent: 0,            // Never cache content — always fetch fresh
  };

  async get<T>(key: string, ttlCategory: keyof typeof this.TTL, fetcher: () => Promise<T>): Promise<T> {
    const cached = this.cache.get(key);
    const now = Date.now();

    if (cached && cached.expiry > now) {
      return cached.data as T;
    }

    const data = await fetcher();
    const ttl = this.TTL[ttlCategory];
    if (ttl > 0) {
      this.cache.set(key, { data, expiry: now + ttl });
    }
    return data;
  }

  invalidate(keyPrefix: string): void {
    for (const key of this.cache.keys()) {
      if (key.startsWith(keyPrefix)) this.cache.delete(key);
    }
  }
}

// Usage
const cache = new OneNoteCache();
const notebooks = await cache.get("notebooks", "notebooks", () =>
  client.api("/me/onenote/notebooks").select("id,displayName").get()
);
```

### Step 8 — Python Image Compression

```python
from PIL import Image
import io

def compress_image(image_bytes: bytes, max_size_mb: float = 4.0) -> bytes:
    """Compress image to fit within OneNote size limits."""
    max_bytes = int(max_size_mb * 1024 * 1024)

    if len(image_bytes) <= max_bytes:
        return image_bytes

    img = Image.open(io.BytesIO(image_bytes))

    # Convert RGBA to RGB for JPEG
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # Try quality reduction first
    for quality in [80, 60, 40, 20]:
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        if buffer.tell() <= max_bytes:
            return buffer.getvalue()

    # Resize if quality alone is insufficient
    scale = (max_bytes / len(image_bytes)) ** 0.5
    new_size = (int(img.width * scale), int(img.height * scale))
    img = img.resize(new_size, Image.LANCZOS)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=60, optimize=True)
    return buffer.getvalue()
```

## Output

Performance optimization delivers:
- **Payload reduction:** 80-95% smaller responses with `$select` vs default queries
- **Latency improvement:** 5-10x faster responses by avoiding deep `$expand`
- **Image reliability:** Pre-validated uploads that never silently fail
- **Batch efficiency:** 20x fewer HTTP requests for bulk operations
- **507 resilience:** Automatic overflow section creation when page limits are hit

## Error Handling

| Status | Cause | Fix |
|--------|-------|-----|
| 507 | Section page limit exceeded (~5,000 pages) | Create overflow section automatically; archive old pages |
| 413 | Request body too large (>4MB for single-part, >25MB per multipart part) | Compress images; split content across multiple pages |
| 408 | Request timeout on large `$expand` queries | Use `$select` and avoid deep expansion; paginate with `$top` |
| 429 | Rate limit from rapid batch operations | See `onenote-rate-limits` for throttling patterns |
| 400 | Unsupported image format (WebP, AVIF) | Convert to JPEG/PNG before upload |

## Examples

**Profile a notebook for performance issues:**
```typescript
async function profileNotebook(client: any, notebookId: string) {
  const sections = await client.api(
    `/me/onenote/notebooks/${notebookId}/sections`
  ).select("id,displayName,pagesUrl").get();

  console.log(`Sections: ${sections.value.length}`);
  if (sections.value.length > 100) {
    console.warn("PERF WARNING: >100 sections — avoid $expand on this notebook");
  }

  for (const section of sections.value) {
    const pages = await client.api(
      `/me/onenote/sections/${section.id}/pages`
    ).select("id").top(1).count(true).get();

    const count = pages["@odata.count"] ?? pages.value.length;
    if (count > 1000) {
      console.warn(`PERF WARNING: Section "${section.displayName}" has ${count} pages`);
    }
    if (count > 4500) {
      console.warn(`507 RISK: Section "${section.displayName}" near page limit (${count}/~5000)`);
    }
  }
}
```

**Python — Parallel section loading with concurrency limit:**
```python
import asyncio

async def load_sections_parallel(client, notebook_ids: list[str], max_concurrent: int = 5):
    """Load sections from multiple notebooks with bounded concurrency."""
    semaphore = asyncio.Semaphore(max_concurrent)
    results = {}

    async def load_one(nb_id: str):
        async with semaphore:
            sections = await client.me.onenote.notebooks.by_notebook_id(
                nb_id
            ).sections.get()
            results[nb_id] = sections.value or []

    await asyncio.gather(*[load_one(nb_id) for nb_id in notebook_ids])
    return results
```

## Resources

- [OneNote API Overview](https://learn.microsoft.com/en-us/graph/api/resources/onenote-api-overview)
- [Images & Files](https://learn.microsoft.com/en-us/graph/onenote-images-files)
- [Best Practices](https://learn.microsoft.com/en-us/graph/onenote-best-practices)
- [Get Content](https://learn.microsoft.com/en-us/graph/onenote-get-content)
- [Create Pages](https://learn.microsoft.com/en-us/graph/onenote-create-page)
- [Error Codes](https://learn.microsoft.com/en-us/graph/onenote-error-codes)
- [Known Issues](https://learn.microsoft.com/en-us/graph/known-issues)

## Next Steps

- See `onenote-rate-limits` for request throttling when batch operations hit limits
- See `onenote-webhooks-events` for cache invalidation via polling-based change detection
- See `onenote-core-workflow-a` for CRUD operations that benefit from these optimizations
