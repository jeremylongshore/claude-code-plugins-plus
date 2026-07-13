# OneNote SDK Patterns — One-Pager

## The Problem

Microsoft Graph rate limits OneNote at 600 requests per 60 seconds per user and 10,000 per 10 minutes per tenant. Production integrations that ignore these limits get 429 responses that cascade into request storms. Worse, file uploads larger than 4MB silently return 200 OK with an empty response body — the page is never created, but no error is raised. Developers only discover the data loss when users report missing pages.

## The Solution

Production-ready middleware patterns for retry logic, proactive rate limit tracking, batch requests, safe file uploads with silent failure detection, and token refresh. Provides both TypeScript middleware chains and Python async decorators that can be dropped into existing codebases.

## Who / What / When / Where / Why

| | |
|---|---|
| **Who** | Developers building production OneNote integrations handling >100 requests/minute |
| **What** | Retry middleware, rate limit tracker, batch requests, safe upload with size validation |
| **When** | Before going to production, or after experiencing 429 errors or missing pages |
| **Where** | Graph API middleware layer — wraps all OneNote API calls |
| **Why** | Rate limits cause cascading failures; silent upload failures cause data loss |

## Key Differentiators

- Parses the actual `Retry-After` header instead of hardcoding retry delays
- Proactive rate limit tracking prevents 429s instead of reacting to them
- Silent upload failure detection catches the 200-with-empty-body trap
- Both TypeScript middleware and Python decorator implementations included

## Stack

| Component | Technology |
|-----------|-----------|
| API | Microsoft Graph v1.0 |
| Auth | MSAL (delegated) |
| SDK (Python) | msgraph-sdk + azure-identity |
| SDK (Node) | @microsoft/microsoft-graph-client + @azure/identity |
