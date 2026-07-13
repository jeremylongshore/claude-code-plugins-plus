# OneNote Debug Bundle — One-Pager

## The Problem

When OneNote Graph API calls fail, developers waste hours piecing together diagnostic information scattered across console logs, network tabs, and Azure portal. Microsoft support tickets require the `request-id` response header (not logged by default), token claims analysis (requires JWT decoding), and the `x-ms-ags-diagnostic` header (most developers do not know it exists). Without a structured diagnostic capture, a 403 error that takes 5 minutes to diagnose with the right data takes 2 hours of guesswork.

## The Solution

Automatic diagnostic middleware that intercepts every Graph API call and captures request-id, response headers, error bodies, and timing data. Includes zero-dependency JWT decoder for token claims inspection, permission gap analysis, and a Microsoft support ticket template with all required fields pre-filled from the diagnostic bundle.

## Who / What / When / Where / Why

| | |
|---|---|
| **Who** | Developers debugging OneNote API failures and DevOps filing Microsoft support tickets |
| **What** | Diagnostic bundle generator with request tracing, token inspection, and structured logging |
| **When** | After Graph API errors (403, 429, 500), during permission audits, or when filing support cases |
| **Where** | TypeScript and Python OneNote integrations, CI pipelines, production monitoring |
| **Why** | Graph API diagnostics require `request-id` headers, JWT claims analysis, and `x-ms-ags-diagnostic` parsing — none of which are captured by default logging |

## Key Differentiators

- Zero-dependency JWT decoder — inspects token claims without installing `jsonwebtoken` or `PyJWT`
- Automatic permission gap analysis: compares granted scopes vs required scopes and identifies the exact missing permission
- Microsoft support ticket template pre-filled from diagnostic bundle data
- Structured JSON logging format compatible with Datadog, Splunk, and CloudWatch log aggregation

## Stack

| Component | Technology |
|-----------|-----------|
| API | Microsoft Graph v1.0 |
| Auth | MSAL (delegated) |
| SDK (Python) | msgraph-sdk + azure-identity |
| SDK (Node) | @microsoft/microsoft-graph-client + @azure/identity |
| Logging | Structured JSON (console, Datadog, Splunk) |
| Token Decode | Built-in Base64 (no external JWT library) |
