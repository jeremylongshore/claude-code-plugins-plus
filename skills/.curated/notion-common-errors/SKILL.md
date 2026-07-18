---
name: notion-common-errors
description: 'Diagnose and fix Notion API errors by HTTP status code and error code.

  Use when encountering Notion errors, debugging failed requests,

  or troubleshooting integration access, rate limiting, or validation issues.

  Trigger with phrases like "notion error", "fix notion",

  "notion not working", "debug notion", "notion 400", "notion 429".

  '
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.38.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- productivity
- notion
compatibility: Designed for Claude Code
---
# Notion Common Errors

## Overview

Quick reference for all Notion API error codes with exact HTTP statuses, error bodies, and fixes. The API returns errors as JSON with three fields:

```json
{
  "object": "error",
  "status": 400,
  "code": "validation_error",
  "message": "Title is not a property that exists."
}
```

All requests require `Authorization: Bearer $NOTION_TOKEN` and `Notion-Version: 2022-06-28` headers (`2022-06-28` is the current stable API version — the header is required on every call).

This SKILL.md gives you the triage table and workflow. Two references carry the depth:

- **[references/error-codes.md](references/error-codes.md)** — the full per-status playbook (401, 403, 404, 400, 429, 409, 500, 502/503) with error bodies, causes, and code fixes.
- **[references/examples.md](references/examples.md)** — the full SDK error handler, the curl diagnostic script, and the non-HTTP client-side gotchas (rich text arrays, pagination, timeouts).

## Prerequisites

- `@notionhq/client` installed (`npm install @notionhq/client`)
- `NOTION_TOKEN` environment variable set (internal integration token starting with `ntn_` or `secret_`)
- Target pages/databases shared with the integration via the Connections menu

## Instructions

### Step 1: Identify the Error

1. Read the JSON error body returned by the failed request.
2. Note its HTTP `status` and machine-readable `code` fields — those two values route you to the exact fix.
3. If you only have logs, `Grep` your application logs for the `code` field to recover the values.

### Step 2: Match Error Code and Apply Fix

Use the Error Handling table below to see whether the error is retryable and the recommended action. For the exact error body, root cause, and copy-paste fix, open the matching section in **[references/error-codes.md](references/error-codes.md)**. The four you will hit most:

- **404 `object_not_found`** — the most common error. The page/database exists but is not shared with your integration. Fix via the `...` → **Connections** menu; parent pages must be shared too.
- **401 `unauthorized`** — token missing, malformed, expired, or revoked. Verify with `curl .../v1/users/me`; regenerate at [notion.so/my-integrations](https://www.notion.so/my-integrations).
- **400 `validation_error`** — the broadest category, usually a wrong property name/type or a filter-type mismatch (e.g. `status:` filter used as `text:`). Retrieve the database schema first.
- **429 `rate_limited`** — over 3 requests/sec/integration. Back off exponentially; the SDK retries automatically.

### Step 3: Verify the Fix

Re-run the failing call, or use the three-probe curl diagnostic in **[references/examples.md](references/examples.md)** to confirm status, token, and resource access independently.

## Output

- Identified error cause from HTTP status and `code` field
- Applied targeted fix from the matching section
- Verified resolution with test API call

## Error Handling

| Code | HTTP | Error Name | Retryable | Recommended Action |
| ------ | ------ | ------------ | ----------- | ------------------- |
| `unauthorized` | 401 | Authentication failure | No | Regenerate token at notion.so/my-integrations |
| `restricted_resource` | 403 | Missing capability | No | Enable capability in integration settings |
| `object_not_found` | 404 | Not shared / not found | No | Share page with integration via Connections menu |
| `validation_error` | 400 | Malformed request | No | Fix request body — retrieve schema first |
| `rate_limited` | 429 | Rate limit exceeded | Yes | Respect `Retry-After` header, use exponential backoff |
| `conflict_error` | 409 | Concurrent modification | Yes | Retry after 1-2s, serialize writes to same object |
| `internal_server_error` | 500 | Notion server error | Yes | Retry with backoff, check status.notion.so |
| `service_unavailable` | 502/503 | Notion down | Yes | Wait and retry, check status.notion.so |
| `gateway_timeout` | 504 | Request timeout | Yes | Retry, reduce query complexity or page size |

Each row maps to a full walkthrough in [references/error-codes.md](references/error-codes.md).

## Examples

Start with the fastest diagnostic — a single curl to confirm your token is valid and the integration is reachable:

```bash
curl -s https://api.notion.com/v1/users/me \
  -H "Authorization: Bearer ${NOTION_TOKEN}" \
  -H "Notion-Version: 2022-06-28" | jq '{id, type, name}'
```

A valid token returns your integration bot user. From there:

- Full three-probe diagnostic (status → token → database access): [references/examples.md](references/examples.md)
- A single SDK `catch` block branching on every error code: [references/examples.md](references/examples.md)
- Client-side shape gotchas that masquerade as `validation_error` (rich text arrays, block children, pagination, timeouts): [references/examples.md](references/examples.md)

## Resources

- [Notion API Error Codes](https://developers.notion.com/reference/errors)
- [Request Limits & Rate Limiting](https://developers.notion.com/reference/request-limits)
- [Notion Status Page](https://status.notion.so)
- [API Introduction](https://developers.notion.com/reference/intro)
- [Working with Databases](https://developers.notion.com/docs/working-with-databases)
- [@notionhq/client npm](https://www.npmjs.com/package/@notionhq/client)

## Next Steps

For comprehensive debugging workflows, see `notion-debug-bundle`. For rate limit strategies at scale, see `notion-rate-limits`.
