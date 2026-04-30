---
name: onenote-common-errors
description: 'Decode and fix every common OneNote Graph API error with root cause
  analysis.

  Use when debugging 400, 403, 404, 429, 500, 502, or 507 errors from OneNote API.

  Trigger with "onenote error", "onenote 403", "onenote debug", "graph api error onenote".

  '
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- onenote
- microsoft
compatibility: Designed for Claude Code
---
# OneNote Common Errors

## Overview

A complete error decoder for the OneNote Graph API. Each HTTP status code has multiple possible root causes — this skill maps every cause, provides diagnostic steps, and gives fix-it code. Special attention to the two trickiest errors: 403 (which could mean wrong permissions OR deprecated app-only auth) and 200 with empty body (silent upload failure that causes data loss).

## Prerequisites

- A OneNote Graph API integration that is returning errors
- Access to application logs or the ability to add logging
- Familiarity with the Graph API request/response format

## Instructions

### Complete Error Reference Table

| Code | Error Name | Possible Causes | Fix |
|------|-----------|-----------------|-----|
| 400 | Bad Request | (1) Invalid XHTML — unclosed tags, bad encoding | Validate HTML with XML parser before sending |
| | | (2) Bad notebook name — empty or duplicate `displayName` | Check for existing notebooks, use unique names |
| | | (3) Malformed JSON in PATCH body | Validate JSON structure matches [update spec](https://learn.microsoft.com/en-us/graph/onenote-update-page) |
| | | (4) Missing `<title>` in page HTML | Always include `<head><title>...</title></head>` |
| | | (5) Invalid `$filter` OData expression | Check [OData query syntax](https://learn.microsoft.com/en-us/graph/api/resources/onenote-api-overview) |
| 403 | Forbidden | (1) **App-only auth (deprecated March 2025)** | Switch to delegated auth (DeviceCodeCredential) |
| | | (2) Missing permission scope | Add `Notes.ReadWrite` in Azure Portal, re-consent |
| | | (3) User doesn't own the notebook | Use `/users/{id}/onenote/` for shared notebooks |
| | | (4) Admin consent required but not granted | Admin must grant consent in Azure Portal |
| | | (5) Conditional access policy blocking app | Check Azure AD conditional access policies |
| 404 | Not Found | (1) Page/section/notebook ID is wrong | Re-fetch parent resource to get correct IDs |
| | | (2) Resource was deleted | Use `$filter=isDeleted eq true` if available |
| | | (3) Wrong URL format | Verify endpoint: `/me/onenote/` not `/me/notes/` |
| | | (4) User context mismatch — querying another user's notes without delegation | Use `/users/{userId}/onenote/` with correct permissions |
| 429 | Too Many Requests | (1) Per-user limit: 600 requests / 60 seconds | Parse `Retry-After` header, wait exact seconds |
| | | (2) Per-tenant limit: 10,000 requests / 10 minutes | Reduce concurrency, use batch requests |
| | | (3) Burst of requests from multiple users in same tenant | Implement per-tenant rate limit tracking |
| 500 | Internal Server Error | (1) Graph service internal failure | Retry with exponential backoff |
| | | (2) Malformed request that passes validation but fails processing | Check request body against API reference |
| 502 | Bad Gateway | (1) Upstream OneNote service unavailable | Retry after 5-10 seconds |
| | | (2) Token expiration during processing | Refresh token and retry |
| 507 | Insufficient Storage | (1) Per-section page limit exceeded (~5000 pages) | Create a new section, archive old pages |
| | | (2) User OneDrive storage quota hit | Check storage quota in OneDrive settings |

### The 403 Trap: App-Only Auth Deprecation

This is the single most common production issue since March 2025. If your code uses `ClientSecretCredential` (Node) or `client_secret` (Python) for OneNote calls, every request returns 403 regardless of permission scope.

**How to diagnose:**
```typescript
// Check if you're using the deprecated auth pattern
// SEARCH your codebase for these — any match means you need to migrate:
// - ClientSecretCredential
// - client_secret
// - AZURE_CLIENT_SECRET
// - ConfidentialClientApplication (for OneNote specifically)

// If found, the fix is:
// BEFORE (broken after March 2025):
import { ClientSecretCredential } from "@azure/identity";
const credential = new ClientSecretCredential(tenantId, clientId, clientSecret);

// AFTER (correct):
import { DeviceCodeCredential } from "@azure/identity";
const credential = new DeviceCodeCredential({ clientId, tenantId });
```

### The 200 Trap: Silent Upload Failure

This error does not appear in any error table because the HTTP status is 200. Files larger than approximately 4MB return 200 OK with an empty response body. The page is never created.

```typescript
// DETECTION: Always check the response body after page creation
const response = await client
  .api(`/me/onenote/sections/${sectionId}/pages`)
  .header("Content-Type", "text/html")
  .post(htmlContent);

// This looks successful but the page was never created:
if (!response || !response.id) {
  console.error("SILENT FAILURE: 200 OK but no page ID returned");
  console.error(`Payload size: ${Buffer.byteLength(htmlContent, "utf-8")} bytes`);
  // Fix: reduce payload size below 4MB, use URL references for images
  // instead of inline base64 data
}
```

### The 404 Trap: Deleted Pages in List Results

`GET /me/onenote/sections/{id}/pages` can return pages that have been recently deleted. When you try to `GET /me/onenote/pages/{id}/content` on these pages, you get 404.

```typescript
// Defensive page content retrieval
async function getPageContentSafe(client: Client, pageId: string) {
  try {
    return await client.api(`/me/onenote/pages/${pageId}/content`).get();
  } catch (error: any) {
    if (error.statusCode === 404) {
      console.warn(`Page ${pageId} listed but not accessible (likely deleted)`);
      return null;
    }
    throw error;
  }
}
```

### Diagnostic Code: Extract Request ID and Diagnostics

When contacting Microsoft support, they need the `request-id` header from the failed response. The `x-ms-ags-diagnostic` header contains internal routing information.

```typescript
function logGraphError(error: any): void {
  const headers = error.headers ?? new Map();
  const requestId = headers.get?.("request-id") ?? "unavailable";
  const diagnostics = headers.get?.("x-ms-ags-diagnostic") ?? "";
  const dateHeader = headers.get?.("date") ?? new Date().toISOString();

  console.error("=== OneNote Graph API Error ===");
  console.error(`Status:     ${error.statusCode}`);
  console.error(`Code:       ${error.code}`);
  console.error(`Message:    ${error.message}`);
  console.error(`Request-ID: ${requestId}`);
  console.error(`Date:       ${dateHeader}`);

  if (diagnostics) {
    try {
      const parsed = JSON.parse(diagnostics);
      console.error(`Server:     ${parsed.serverInfo?.dataCenter ?? "unknown"}`);
    } catch {
      console.error(`Diagnostics: ${diagnostics}`);
    }
  }

  console.error("==============================");
  console.error(
    `For Microsoft support, provide: request-id=${requestId}, date=${dateHeader}`
  );
}
```

```python
# Python equivalent
def log_graph_error(error) -> None:
    """Extract diagnostic info from Graph API error for support tickets."""
    request_id = getattr(error, "request_id", "unavailable")
    status = getattr(error, "status_code", "unknown")
    message = getattr(error, "message", str(error))

    print("=== OneNote Graph API Error ===")
    print(f"Status:     {status}")
    print(f"Message:    {message}")
    print(f"Request-ID: {request_id}")
    print("===============================")
    print(f"For Microsoft support: request-id={request_id}")
```

### Permission Misconfiguration Table

| Symptom | Likely Misconfiguration | Fix |
|---------|------------------------|-----|
| 403 on all OneNote calls | Using `ClientSecretCredential` (app-only deprecated) | Switch to `DeviceCodeCredential` |
| 403 on write operations only | Have `Notes.Read` but missing `Notes.ReadWrite` | Add `Notes.ReadWrite` scope, re-consent |
| 403 on shared notebooks | Have `Notes.ReadWrite` but missing `Notes.ReadWrite.All` | Add `.All` scope for shared notebook access |
| 403 after admin policy change | Conditional access policy blocks the app | Check with Azure AD admin, add app to policy exclusion |
| 403 on first request only | Admin consent required but user cannot consent | Admin must grant consent in Azure Portal |
| 401 after token was working | Token expired (default 1-hour lifetime) | Implement token refresh, use MSAL token cache |
| 400 on PATCH page | JSON body missing `target` or `action` field | Review [update page spec](https://learn.microsoft.com/en-us/graph/onenote-update-page) |

### TypeScript Error Handler with Structured Logging

```typescript
type ErrorSeverity = "warn" | "error" | "fatal";

interface DiagnosticResult {
  severity: ErrorSeverity;
  category: string;
  userMessage: string;
  devAction: string;
  retryable: boolean;
}

function diagnoseOneNoteError(statusCode: number, errorBody?: any): DiagnosticResult {
  const code = errorBody?.error?.code ?? "";

  switch (statusCode) {
    case 400:
      return {
        severity: "error",
        category: "invalid_request",
        userMessage: "The request was malformed.",
        devAction: code === "20117"
          ? "Notebook name already exists. Use a unique displayName."
          : "Validate XHTML and JSON request body against API spec.",
        retryable: false,
      };
    case 403:
      return {
        severity: "fatal",
        category: "auth_or_permissions",
        userMessage: "Access denied to OneNote resource.",
        devAction: "Check: (1) using delegated auth not app-only? " +
          "(2) correct permission scope? (3) admin consent granted?",
        retryable: false,
      };
    case 404:
      return {
        severity: "warn",
        category: "resource_not_found",
        userMessage: "The requested notebook, section, or page was not found.",
        devAction: "Re-fetch parent resource IDs. Page may have been deleted.",
        retryable: false,
      };
    case 429:
      return {
        severity: "warn",
        category: "rate_limit",
        userMessage: "Too many requests. Slowing down.",
        devAction: "Parse Retry-After header. Consider batch requests.",
        retryable: true,
      };
    case 507:
      return {
        severity: "error",
        category: "storage_quota",
        userMessage: "Storage limit reached.",
        devAction: "Check section page count (~5000 limit) and OneDrive quota.",
        retryable: false,
      };
    default:
      return {
        severity: statusCode >= 500 ? "error" : "warn",
        category: "server_error",
        userMessage: "A server error occurred. Retrying.",
        devAction: "Retry with exponential backoff. Log request-id for support.",
        retryable: statusCode >= 500,
      };
  }
}
```

## Output

After using this skill you will be able to:
- Immediately identify the root cause of any OneNote Graph API error
- Distinguish between permission errors and deprecated auth patterns
- Detect silent upload failures that return 200 OK
- Extract diagnostic headers for Microsoft support escalation
- Build structured error handling that categorizes and routes errors correctly

## Error Handling

This entire skill IS error handling documentation. For implementation of retry logic and rate limit handling, see `onenote-sdk-patterns`.

## Examples

**Quick error check script:**
```bash
# Test connectivity and permissions in one command
curl -s -w "\nHTTP %{http_code}" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://graph.microsoft.com/v1.0/me/onenote/notebooks" \
  | tail -1
# 200 = working, 401 = token issue, 403 = permissions/auth type, 404 = wrong endpoint
```

**Decode a specific error in logs:**
```typescript
// When you see this in logs:
// { statusCode: 403, code: "40004", message: "Insufficient privileges" }
// Run the diagnostic:
const result = diagnoseOneNoteError(403, { error: { code: "40004" } });
// result.devAction → "Check: (1) using delegated auth not app-only? ..."
```

## Resources

- [OneNote Error Codes](https://learn.microsoft.com/en-us/graph/onenote-error-codes)
- [OneNote API Overview](https://learn.microsoft.com/en-us/graph/api/resources/onenote-api-overview)
- [Graph API Known Issues](https://learn.microsoft.com/en-us/graph/known-issues)
- [OneNote Update Pages](https://learn.microsoft.com/en-us/graph/onenote-update-page)
- [OneNote Best Practices](https://learn.microsoft.com/en-us/graph/onenote-best-practices)
- [Graph Explorer](https://developer.microsoft.com/en-us/graph/graph-explorer)

## Next Steps

- See `onenote-sdk-patterns` for production retry and rate limit middleware
- See `onenote-install-auth` to fix authentication and permission issues
- See `onenote-local-dev-loop` to test error handling with mock responses
