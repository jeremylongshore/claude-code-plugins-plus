# OneNote Common Errors — One-Pager

## The Problem

OneNote Graph API errors are ambiguous: a 403 could mean wrong permission scope, missing admin consent, OR the March 2025 app-only auth deprecation. A 404 could be a wrong ID, a deleted page, or a URL format error. Worst of all, a 200 with empty body means a file upload silently failed and pages were never created — no error raised, data simply lost. Developers spend hours chasing the wrong root cause.

## The Solution

A complete error decoder covering every HTTP status code (400, 403, 404, 429, 500, 502, 507) with multiple possible root causes per code. Includes diagnostic code to extract `request-id` and `x-ms-ags-diagnostic` headers for Microsoft support, a permission misconfiguration lookup table, and a structured TypeScript error handler that categorizes errors by severity and retryability.

## Who / What / When / Where / Why

| | |
|---|---|
| **Who** | Developers debugging OneNote Graph API failures in dev or production |
| **What** | Multi-cause error decoder, diagnostic header extraction, structured error handler |
| **When** | When any OneNote API call returns an unexpected status code or empty response |
| **Where** | Error handling layer of any OneNote Graph API integration |
| **Why** | Each status code has 3-5 possible root causes — wrong diagnosis wastes hours |

## Key Differentiators

- Multiple root causes per error code, not just the obvious one
- Catches the 200-with-empty-body silent failure that no error table covers
- Includes the 403 app-only auth deprecation trap with migration code
- Diagnostic header extraction for Microsoft support escalation (request-id, x-ms-ags-diagnostic)

## Stack

| Component | Technology |
|-----------|-----------|
| API | Microsoft Graph v1.0 |
| Auth | MSAL (delegated) |
| SDK (Python) | msgraph-sdk + azure-identity |
| SDK (Node) | @microsoft/microsoft-graph-client + @azure/identity |
