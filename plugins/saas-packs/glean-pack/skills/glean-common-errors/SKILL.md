---
name: glean-common-errors
description: 'Diagnose and fix common Glean API errors including indexing failures,
  search issues, and permission problems.

  Trigger: "glean error", "glean not indexing", "glean search empty", "debug glean".

  '
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- enterprise-search
- glean
compatibility: Designed for Claude Code
---
# Glean Common Errors

## Overview

Glean provides enterprise search across connected data sources with AI-powered results. API integrations involve two distinct token types (indexing vs. client) and a custom datasource model for pushing content. Common errors stem from token type mismatches, permission misconfiguration that silently hides documents from search results, and bulk indexing failures caused by duplicate upload IDs or oversized documents. Stale results are a frequent complaint -- Glean indexes asynchronously, so newly pushed documents may take 1-5 minutes to appear in search. This reference covers authentication, indexing pipeline, and search-time issues.

## Error Reference

| Code | Message | Cause | Fix |
|------|---------|-------|-----|
| `401` | `Unauthorized` | Invalid or expired API token | Regenerate at Admin > Settings > API Tokens |
| `403` | `Wrong token type` | Using indexing token for search API | Indexing API needs indexing token; Client API needs client token with `X-Glean-Auth-Type: BEARER` |
| `400` | `uploadId already used` | Duplicate bulk upload identifier | Generate a unique UUID per upload run |
| `400` | `document too large` | Document body exceeds 100KB limit | Truncate or split content before indexing |
| `400` | `invalid datasource` | Datasource not registered | Create datasource first via `adddatasource` endpoint |
| `400` | `missing required field` | Document lacks `id` or `title` | Ensure every document has both `id` and `title` fields |
| `403` | `Permission denied` | Document visibility restricted | Set `allowAnonymousAccess: true` or add user/group to permissions |
| `429` | `Rate limit exceeded` | Too many API requests | Implement exponential backoff; batch indexing calls |

## Error Handler

```typescript
interface GleanError {
  code: number;
  message: string;
  category: "auth" | "rate_limit" | "indexing" | "permission";
}

function classifyGleanError(status: number, body: string): GleanError {
  if (status === 401) {
    return { code: 401, message: body, category: "auth" };
  }
  if (status === 429) {
    return { code: 429, message: "Rate limit exceeded", category: "rate_limit" };
  }
  if (status === 403 && body.includes("permission")) {
    return { code: 403, message: body, category: "permission" };
  }
  if (status === 400) {
    return { code: 400, message: body, category: "indexing" };
  }
  return { code: status, message: body, category: "auth" };
}
```

## Debugging Guide

### Authentication Errors
Glean uses two distinct token types. Indexing tokens authenticate bulk document uploads. Client tokens authenticate search queries and require the `X-Glean-Auth-Type: BEARER` header. Using the wrong token type returns 403, not 401 -- check the token type first.

### Rate Limit Errors
Glean enforces per-token rate limits. Indexing operations should batch documents (up to 100 per request). Search queries are rate-limited per client token. Use `Retry-After` header when present and implement exponential backoff starting at 2 seconds.

### Validation Errors
Bulk index uploads require a unique `uploadId` per run -- reusing an ID silently drops the upload. Documents must include both `id` and `title` fields. Content bodies over 100KB are rejected; truncate or split large documents. New datasources must be registered via `adddatasource` before any documents can be indexed against them. The `datasource` field in each document must exactly match the registered datasource name (case-sensitive).

## Error Handling

| Scenario | Pattern | Recovery |
|----------|---------|----------|
| No search results after indexing | Processing delay (1-5 min) | Wait 5 minutes, then verify with direct document lookup |
| Stale results returned | Index not refreshed | Trigger re-index; check datasource sync schedule |
| Permission mismatch | User lacks document access | Add user/group to document permissions or enable anonymous access |
| Bulk upload silently dropped | Duplicate `uploadId` | Always generate fresh UUID per upload run |
| Token type confusion | 403 on search or index | Verify correct token type for the API being called |

## Quick Diagnostic

```bash
# Verify client token connectivity
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $GLEAN_API_KEY" \
  -H "X-Glean-Auth-Type: BEARER" \
  https://your-domain.glean.com/api/v1/search
```

## Resources

- [Glean Developer Portal](https://developers.glean.com/)
- [Indexing API Docs](https://developers.glean.com/api-info/indexing/getting-started/overview)

## Next Steps

See `glean-debug-bundle`.
