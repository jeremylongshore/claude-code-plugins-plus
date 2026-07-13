# OneNote Performance Tuning — One-Pager

## The Problem

OneNote performance degrades predictably at scale. Notebooks with 100+ sections take 3-5 seconds per API call when using `$expand`. Pages with embedded images over 4MB fail silently — no error, just a missing image. Image uploads are capped at 25MB per multipart part, but the API returns no error if exceeded. Sections that accumulate approximately 5,000 pages return `507 Insufficient Storage` on new page creation. Requesting full page content without `$select` inflates payloads by 80-95%.

## The Solution

Production-tested patterns for every OneNote performance bottleneck: selective `$expand` and `$select` for minimal payloads (80-95% reduction), image validation and compression before upload (sharp/Pillow), batch requests via `$batch` (20 operations per HTTP call), lazy pagination with async generators, HTTP 507 detection with automatic overflow section creation, and a tiered caching strategy that keeps structure cached while invalidating page data on change detection.

## Who / What / When / Where / Why

| | |
|---|---|
| **Who** | Developers building integrations with large OneNote datasets, image-heavy content, or bulk operations |
| **What** | Payload optimization, image compression, batch consolidation, 507 mitigation, and caching |
| **When** | Notebooks exceed 100 sections, pages contain large images, or API responses exceed 1 second |
| **Where** | Client-side optimization layer wrapping Microsoft Graph API calls to OneNote endpoints |
| **Why** | Silent image failures, 507 storage errors, and multi-second response times break production integrations |

## Key Differentiators

- Quantified payload reduction: comparison table showing 800KB vs 2KB for the same notebook query
- Image upload pre-validation that prevents silent failures (4MB render limit, 25MB upload limit)
- Automatic overflow section creation when 507 is detected — prevents data loss
- Async generator pattern for lazy page iteration that can bail early without loading thousands of pages

## Stack

| Component | Technology |
|-----------|-----------|
| API | Microsoft Graph v1.0 |
| Auth | MSAL (delegated — app-only deprecated March 2025) |
| SDK (Python) | msgraph-sdk + azure-identity + Pillow |
| SDK (Node) | @microsoft/microsoft-graph-client + @azure/identity + sharp |
