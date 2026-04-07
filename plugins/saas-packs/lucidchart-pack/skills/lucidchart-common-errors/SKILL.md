---
name: lucidchart-common-errors
description: |
  Diagnose and fix Lucidchart common errors.
  Trigger: "lucidchart error", "fix lucidchart", "debug lucidchart".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, lucidchart, diagramming]
compatible-with: claude-code
---

# Lucidchart Common Errors

## Overview

Lucidchart's API enables programmatic diagram creation, document management, shape manipulation, and team collaboration workflows. Common integration errors include OAuth token expiration during long-running batch operations, document lock conflicts when multiple users edit simultaneously, and shape API 422 errors from invalid geometry or missing parent references. The OAuth token refresh flow is the most common stumbling block -- access tokens expire after 60 minutes, and batch operations that exceed this window fail mid-run. This reference covers authentication, document lifecycle, and shape-level validation issues for the Lucid developer platform.

## Error Reference

| Code | Message | Cause | Fix |
|------|---------|-------|-----|
| `401` | `Token expired` | OAuth2 access token expired | Use refresh token to obtain new access token |
| `403` | `Insufficient scopes` | OAuth app missing required permission scopes | Re-authorize with `lucidchart.document.content` and needed scopes |
| `404` | `Document not found` | Invalid document ID or user lacks access | Verify document ID and that API user has viewer/editor role |
| `409` | `Document locked` | Another user is actively editing | Wait for lock release or use force-unlock with admin privileges |
| `422` | `Invalid shape data` | Shape position/size out of bounds or missing parent | Validate x/y/width/height > 0; ensure parent page exists |
| `422` | `Invalid connection` | Source or target shape ID does not exist | Create shapes before connecting them; verify shape IDs |
| `429` | `Rate limited` | Exceeded 100 requests/minute | Implement exponential backoff; batch shape operations |
| `500` | `Export failed` | PDF/PNG export timed out on complex diagram | Reduce page count or simplify shapes before export |

## Error Handler

```typescript
interface LucidchartError {
  code: number;
  message: string;
  category: "auth" | "rate_limit" | "validation" | "conflict";
}

function classifyLucidchartError(status: number, body: string): LucidchartError {
  if (status === 401 || status === 403) {
    return { code: status, message: body, category: "auth" };
  }
  if (status === 429) {
    return { code: 429, message: "Rate limited", category: "rate_limit" };
  }
  if (status === 409) {
    return { code: 409, message: body, category: "conflict" };
  }
  return { code: status, message: body, category: "validation" };
}
```

## Debugging Guide

### Authentication Errors
Lucidchart uses OAuth2 with access and refresh tokens. Access tokens expire after 60 minutes. Always implement token refresh logic. A 403 typically means missing OAuth scopes rather than invalid credentials -- check the `scopes` parameter in your authorization URL against the API endpoints you are calling.

### Rate Limit Errors
The API enforces 100 requests/minute per OAuth token. Shape creation in bulk should use batch endpoints. Export operations (PDF, PNG) count against the same limit. Use `Retry-After` header and implement exponential backoff starting at 1 second.

### Validation Errors
Shape creation requires valid `x`, `y`, `width`, and `height` values (all positive integers). Zero or negative values return 422. Connections require both source and target shape IDs to exist on the same page -- cross-page connections are not supported. Page references must use valid page IDs from the document; list pages first before creating shapes.

## Error Handling

| Scenario | Pattern | Recovery |
|----------|---------|----------|
| OAuth token expired mid-batch | 401 after N successful calls | Refresh token, resume from last successful operation |
| Document locked by teammate | 409 on write operations | Poll lock status every 10s; notify user if persistent |
| Shape API 422 | Invalid geometry values | Validate all shape coordinates are positive before API call |
| Export timeout on large diagram | 500 on PDF/PNG export | Export individual pages instead of full document |
| Connection fails between shapes | Target shape not yet created | Create all shapes first, then create connections |

## Quick Diagnostic

```bash
# Verify OAuth token validity
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $LUCID_ACCESS_TOKEN" \
  https://api.lucid.co/v1/users/me
```

## Resources

- [Lucid Developer Docs](https://developer.lucid.co/reference/overview)
- [Lucid OAuth2 Guide](https://developer.lucid.co/guides/oauth2)

## Next Steps

See `lucidchart-debug-bundle`.
