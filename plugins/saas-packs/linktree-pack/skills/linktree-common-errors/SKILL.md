---
name: linktree-common-errors
description: |
  Diagnose and fix Linktree common errors.
  Trigger: "linktree error", "fix linktree", "debug linktree".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, linktree, social]
compatible-with: claude-code
---

# Linktree Common Errors

## Overview

Linktree's API manages link-in-bio profiles, individual links, appearance settings, and analytics. Common integration errors include URL validation failures when adding links with unsupported schemes, profile-not-found errors from incorrect username lookups, and analytics data lag that causes empty responses for recently created links. Analytics data lags 15-30 minutes behind real-time, which frequently causes confusion when verifying newly created links. This reference covers HTTP errors, link management issues, and analytics-specific quirks that affect Linktree API consumers.

## Error Reference

| Code | Message | Cause | Fix |
|------|---------|-------|-----|
| `400` | `Invalid URL format` | Link URL missing scheme or malformed | Ensure URLs include `https://` prefix and pass URL validation |
| `401` | `Authentication failed` | API key invalid or expired | Regenerate key at linktr.ee developer portal |
| `403` | `Plan feature restricted` | Endpoint requires Pro/Premium plan | Upgrade plan or use alternative endpoint for free tier |
| `404` | `Profile not found` | Username does not exist or is deactivated | Verify username spelling; check profile is active |
| `404` | `Link not found` | Link ID deleted or belongs to another profile | List links first to confirm valid IDs |
| `409` | `Duplicate link` | Same URL already exists on profile | Check existing links before adding; update instead of create |
| `422` | `Validation error` | Title too long or thumbnail URL invalid | Title max 100 chars; thumbnail must be valid image URL |
| `429` | `Rate limited` | Exceeded 100 requests/minute | Implement exponential backoff; check `Retry-After` header |

## Error Handler

```typescript
interface LinktreeError {
  code: number;
  message: string;
  category: "auth" | "rate_limit" | "validation" | "not_found";
}

function classifyLinktreeError(status: number, body: string): LinktreeError {
  if (status === 401 || status === 403) {
    return { code: status, message: body, category: "auth" };
  }
  if (status === 429) {
    return { code: 429, message: "Rate limited", category: "rate_limit" };
  }
  if (status === 404) {
    return { code: 404, message: body, category: "not_found" };
  }
  return { code: status, message: body, category: "validation" };
}
```

## Debugging Guide

### Authentication Errors
Linktree API keys are passed via `Authorization: Bearer` header. Keys are scoped per account, not per profile. A 403 may indicate a plan-level restriction rather than a credentials issue -- verify the endpoint is available on your current plan tier before regenerating the key. Free-tier keys cannot access analytics or appearance customization endpoints.

### Rate Limit Errors
The API enforces 100 requests/minute per key. Batch link creation using array endpoints when available. Analytics endpoints have stricter limits (30/min). Use the `Retry-After` header value and implement exponential backoff starting at 1 second.

### Validation Errors
Link URLs must include the `https://` or `http://` scheme. Custom schemes (e.g., `mailto:`, `tel:`) are not supported via API. Titles are capped at 100 characters. Thumbnail URLs must resolve to valid image formats (PNG, JPG, GIF). Profile appearance updates fail silently if the theme ID does not exist -- validate theme availability first.

## Error Handling

| Scenario | Pattern | Recovery |
|----------|---------|----------|
| Link validation fails | URL missing scheme | Prepend `https://` and retry |
| Analytics returns empty | Data not yet available | Analytics lag 15-30 min; retry after delay |
| Profile lookup fails | Username typo or deactivated | Search by email if available; confirm active status |
| Duplicate link on create | Same URL already on profile | Fetch existing links, update instead of create |
| Bulk link import partial failure | Some URLs invalid | Parse error array, fix URLs, retry failed items |

## Quick Diagnostic

```bash
# Verify API connectivity and key validity
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $LINKTREE_API_KEY" \
  https://api.linktr.ee/v1/profile
```

## Resources

- [Linktree Developer Docs](https://linktr.ee/marketplace/developer)
- [Linktree API Reference](https://developers.linktr.ee)

## Next Steps

See `linktree-debug-bundle`.
