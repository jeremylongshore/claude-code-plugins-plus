---
name: klaviyo-common-errors
description: 'Diagnose and fix common Klaviyo API errors and exceptions.

  Use when encountering Klaviyo 4xx/5xx errors, debugging failed requests,

  or troubleshooting SDK integration issues.

  Trigger with phrases like "klaviyo error", "fix klaviyo",

  "klaviyo not working", "debug klaviyo", "klaviyo 400", "klaviyo 429".

  '
allowed-tools: Read, Grep, Bash(curl:*), Bash(npm:*)
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- klaviyo
- email-marketing
- cdp
compatibility: Designed for Claude Code
---
# Klaviyo Common Errors

## Overview

Quick reference for the most common Klaviyo API errors with real error payloads,
root causes, and solutions. Because Klaviyo returns JSON:API errors (a status
code plus a structured `errors[]` array), this skill walks you from a raw
exception to a targeted fix: extract the status code, match it against the
catalog, apply the documented remedy.

The full per-status-code catalog and the SDK-level failure table live in
`references/` to keep this workflow scannable — drill in once you know which
status code you are chasing.

## Prerequisites

- `klaviyo-api` SDK installed (`npm install klaviyo-api` — note: not `@klaviyo/sdk`)
- A private API key (`pk_*`) exported as `KLAVIYO_PRIVATE_KEY`
- Access to the application logs where the failed request was recorded, so you
  can `Read` the stack trace and `Grep` for the status code and error `code`

## Instructions

### Step 1: Identify the Error

Extract the status code and error detail from the caught exception. `Read` the
log line or wrap the call so the structured payload is visible:

```typescript
try {
  await profilesApi.createProfile(payload);
} catch (error: any) {
  console.error('Status:', error.status);
  console.error('Errors:', JSON.stringify(error.body?.errors, null, 2));
  // error.body.errors[] has: { id, code, title, detail, source }
}
```

If you only have raw logs, `Grep` for the status code (`grep -E "40[0-9]|429|50[0-9]"`)
and the `code` field to isolate the failing request.

### Step 2: Match and Fix

Map the status code to its root cause and remedy. Each row links into the full
catalog, which carries the actual response payload and the fix code block:

| Status | Meaning | Most common root cause |
|--------|---------|------------------------|
| 400 | Bad Request | Missing field, non-E.164 phone, or `snake_case` instead of `camelCase` |
| 401 | Unauthorized | Missing `KLAVIYO_PRIVATE_KEY`, or a public key used as a private key |
| 403 | Forbidden | API key lacks the required scope (e.g. `profiles:write`) |
| 404 | Not Found | Wrong resource ID or a dead `/api/v2/` path |
| 409 | Conflict | Duplicate — use `createOrUpdateProfile` upsert |
| 429 | Rate Limited | Exceeded burst (75/s) or steady (700/min); honor `Retry-After` |
| 500/503 | Server Error | Klaviyo-side — check status page, retry with backoff |

The most common one, 400, is almost always a casing mismatch (the SDK expects
`camelCase`):

```typescript
// Wrong: snake_case              // Right: camelCase (SDK convention)
{ first_name: 'Jane' }            { firstName: 'Jane' }
```

See [the full error catalog](references/error-catalog.md) for every status
code's real payload, complete cause list, and fix. For client-side failures that
never reach the network (wrong import, `response.data` vs `response.body.data`,
bad filter syntax) plus copy-paste diagnostic commands, see
[diagnostics & SDK errors](references/diagnostics.md).

## Output

Working through this skill produces a diagnosis and a fix, not a generated
artifact:

- The **status code** and **error `code`** identifying the failure class
- The **root cause** matched from the catalog
- A **concrete code or config change** (casing fix, scope grant, upsert, backoff)
- For 5xx: confirmation of whether the fault is Klaviyo-side (status page) or yours

## Error Handling

- **Status code is missing from the exception** — the failure is client-side, not
  an API response. Check the SDK-level errors table in
  [diagnostics](references/diagnostics.md) (module-not-found, wrong constructor).
- **401 persists after setting the key** — you are using a public key. Verify with
  `echo $KLAVIYO_PRIVATE_KEY | head -c 3` (must print `pk_`).
- **429 with no `RateLimit-Remaining` header** — expected. On a 429 Klaviyo returns
  only `Retry-After`; do not depend on the reset headers, honor `Retry-After`.
- **Fix does not resolve the error** — collect evidence with `klaviyo-debug-bundle`,
  check [status.klaviyo.com](https://status.klaviyo.com), then open a support
  ticket with the request IDs from the error responses.

## Examples

**Example — 403 permission_denied on profile create.** The exception shows
`status: 403`, `detail: "...required scope: profiles:write"`. Match to the 403 row:
the key lacks a scope. Fix: mint a new key with `profiles:write` at
**Settings > API Keys**. Full payload and the endpoint→scope table are in
[the error catalog](references/error-catalog.md) under the 403 section.

**Example — intermittent 429 under load.** Requests fail once traffic exceeds
700/min. Honor the `Retry-After` header and back off instead of tight-retrying:

```typescript
if (error.status === 429) {
  const retryAfter = parseInt(error.headers?.['retry-after'] || '10'); // seconds
  await new Promise(r => setTimeout(r, retryAfter * 1000));
  // then retry
}
```

More worked cases (400 casing, 404 stale ID, 409 upsert) are in
[the error catalog](references/error-catalog.md).

## Resources

- [Full error catalog](references/error-catalog.md) — per-status-code payloads and fixes
- [Diagnostics & SDK errors](references/diagnostics.md) — client-side failures, diagnostic commands, escalation
- [Rate Limits & Error Handling](https://developers.klaviyo.com/en/docs/rate_limits_and_error_handling)
- [API Error Alerts](https://developers.klaviyo.com/en/docs/review_api_error_alerts)
- [Klaviyo Status Page](https://status.klaviyo.com)
- For evidence collection see the `klaviyo-debug-bundle` skill
